using Microsoft.AspNetCore.Mvc;
using DB = HTCMiniProjectBackend.DatabaseOperations.DatabaseOp;

namespace HTCMiniProjectBackend.Controllers
{
    [ApiController]
    public class MainController : ControllerBase
    {
        [HttpPost("upload_img")]
        public async Task<IActionResult> UploadImage(IFormFile image)
        {
            if (image == null || image.Length == 0)
                return BadRequest("No file uploaded.");

            // Validate MIME type
            var allowedTypes = new[] { "image/jpeg", "image/png", "image/gif", "image/webp" };
            if (!allowedTypes.Contains(image.ContentType.ToLower()))
                return BadRequest("Only image files are allowed.");

            var db = new DB();
            string imageUrl = db.GetConfig("imagePath");
            
            // Ensure folder exists
            if (!Directory.Exists(imageUrl))
                Directory.CreateDirectory(imageUrl);

            // Generate UUID filename with original extension
            var extension = Path.GetExtension(image.FileName);
            var uuid = Guid.NewGuid().ToString();
            var newFileName = uuid + extension;

            var savePath = Path.Combine(imageUrl, newFileName);

            // Save the file
            using (var stream = new FileStream(savePath, FileMode.Create))
            {
                await image.CopyToAsync(stream);
            }

            var trans = db.StartTransaction();
            try
            {
                string id = Modules.Functions.GenerateIDCode();
                db.InsertQueue(id);
                db.InsertUrl(id, newFileName);
                trans.Commit();
                return Ok(
                    new { 
                        message = "Upload successful", 
                        queueId = id,
                        path = savePath,
                        imgName = newFileName
                    });
            }
            catch (Exception ex)
            {
                trans.Rollback(); // Optional: if using transaction
                return StatusCode(500, new
                {
                    message = "An error occurred",
                    error = ex.Message,
                    stackTrace = ex.StackTrace // Optional, useful for debugging
                });
            }
        }

        [HttpGet("request_result")]
        public IActionResult RequestResult(string id)
        {
            var db = new DB();

            int processed = db.CheckQueueStatus(id);

            if ( processed == -1 || processed == 9)
            {
                return Ok(new { message = "ID not found!" });
            } else if ( processed == 0 || processed == 2)
            {
                return Ok(new { message = "Request Processing!" });
            }

            var results = db.GetQueueResult(id);
            var resultImage = db.GetResultImage(id);

            string className = "";
            float confidence = 0f;
            var detectionObjects = new List<object>();

            foreach (var row in results)
            {
                int type = Convert.ToInt32(row["type"]);

                switch (type)
                {
                    case 1: // Classification
                        className = row["result"].ToString() ?? "";
                        confidence = Convert.ToSingle(row["confidence"]);
                        break;

                    case 2: // Detection (may have multiple)
                        detectionObjects.Add(new
                        {
                            label = row["result"].ToString() ?? "",
                            confidence = Convert.ToSingle(row["confidence"])
                        });
                        break;
                }
            }

            var response = new
            {
                classification = new
                {   
                    prediction = className,
                    confidence = confidence
                },
                detection = new
                {
                    objects = detectionObjects,
                    image = resultImage
                }
            };


            return Ok(response);
        }
    }
}
