using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using DB = HTCMiniProjectBackend.DatabaseOperations.DatabaseOp;

namespace HTCMiniProjectBackend.Controllers
{
    [ApiController]
    [Route("ai")]
    public class AiModelController : ControllerBase
    {
        [HttpGet("next_job")]
        public IActionResult GetNextPendingJob()
        {
            var db = new DB();
            var trans = db.StartTransaction();

            try
            {
                var job = db.GetNextQueue();

                if (job == null)
                {
                    trans.Commit(); // nothing to do, but clean exit
                    return Ok(new { message = "No pending job." });
                }

                string? imagePath = db.GetImageById(job);
                string? basePath = db.GetConfig("imagePath");

                if (string.IsNullOrWhiteSpace(basePath))
                {
                    trans.Rollback();
                    return StatusCode(500, new { error = "imagePath config not found." });
                }

                if (string.IsNullOrWhiteSpace(imagePath))
                {
                    db.updateQueueStatus(job, 9);
                    trans.Commit(); // update still happened
                    return BadRequest(new { error = "Image path not found in DB." });
                }

                imagePath = Path.Combine(basePath, imagePath);
                Console.WriteLine($"Attempting to load image at: |{imagePath}|");
                Console.WriteLine($"Running as user: {Environment.UserName}");

                try
                {
                    using var fs = System.IO.File.OpenRead(imagePath); // check readable
                }
                catch (Exception ex)
                {
                    db.updateQueueStatus(job, 9);
                    trans.Commit();
                    Console.WriteLine($"❌ Cannot read file: {ex.Message}");
                    return BadRequest(new { error = "Cannot read image file.", details = ex.Message });
                }

                if (!System.IO.File.Exists(imagePath))
                {
                    db.updateQueueStatus(job, 9);
                    trans.Commit();
                    Console.WriteLine("❌ Image file not found.");
                    return BadRequest(new { error = "Image file not found." });
                }

                byte[] imageBytes;
                try
                {
                    imageBytes = System.IO.File.ReadAllBytes(imagePath);
                }
                catch (Exception ex)
                {
                    db.updateQueueStatus(job, 9);
                    trans.Commit(); // still update the queue status
                    return StatusCode(500, new { error = "Failed to load image.", details = ex.Message });
                }

                db.updateQueueStatus(job, 2); // ✅ now marked as processing
                trans.Commit(); // ✅ everything succeeded

                string base64Image = Convert.ToBase64String(imageBytes);

                return Ok(new
                {
                    queueId = job,
                    image = base64Image
                });
            }
            catch (Exception ex)
            {
                trans.Rollback();
                return StatusCode(500, new { error = "Unexpected error", details = ex.Message });
            }
        }


        [HttpPost("submit_result")]
        public IActionResult SubmitResult([FromBody] JsonElement body)
        {
            var db = new DB(); // instance-based DB handler
            var trans = db.StartTransaction(); // manually start transaction

            try
            {
                // Extract queue ID
                if (!body.TryGetProperty("queueId", out JsonElement queueIdElement))
                {
                    Console.WriteLine("❌ Missing queueId in payload.");
                    return BadRequest(new { error = "Missing queueId." });
                }

                string queueId = queueIdElement.GetString() ?? "";
                Console.WriteLine($"🔹 Queue ID: {queueId}");

                // === CLASSIFICATION ===
                var classification = body.GetProperty("classification");
                string prediction = classification.GetProperty("prediction").GetString() ?? "";
                double classConfidence = classification.GetProperty("confidence").GetDouble();

                // Optional: cap confidence to 100
                if (classConfidence > 100) classConfidence = 100;

                db.updateQueueStatus(queueId, 1); // mark as completed
                Console.WriteLine($"🔸 Classification => Label: {prediction}, Confidence: {classConfidence}");
                db.InsertResult(queueId, 1, prediction, classConfidence); // Type 1 = Classification

                // === DETECTION ===
                var detection = body.GetProperty("detection");
                var objects = detection.GetProperty("objects").EnumerateArray();

                foreach (var obj in objects)
                {
                    string label = obj.GetProperty("label").GetString() ?? "";
                    double confidence = obj.GetProperty("confidence").GetDouble();

                    if (confidence > 100) confidence = 100;

                    Console.WriteLine($"🔸 Detection => Label: {label}, Confidence: {confidence}");
                    db.InsertResult(queueId, 2, label, confidence); // Type 2 = Detection
                }

                if (detection.TryGetProperty("image", out JsonElement imageElement))
                {
                    string base64Image = imageElement.GetString() ?? "";

                    if (!string.IsNullOrWhiteSpace(base64Image))
                    {
                        Console.WriteLine($"🖼 Saving annotated image for queue {queueId}");
                        db.InsertResultImage(queueId, base64Image);
                    }
                    else
                    {
                        Console.WriteLine("⚠️ Empty image data, skipped saving image.");
                    }
                }

                trans.Commit(); // ✅ All successful
                Console.WriteLine("✅ Results inserted and committed successfully.");
                return Ok(new { message = "Results saved." });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error in submit_result: {ex}");
                trans.Rollback(); // ❌ Rollback transaction if error
                return BadRequest(new
                {
                    error = "Failed to insert results",
                    details = ex.Message
                });
            }
        }

    }
}
