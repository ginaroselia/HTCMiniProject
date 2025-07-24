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
            var job = db.GetNextQueue();

            if (job == null)
            {
                return Ok(new { message = "No pending job." });
            }

            string? imagePath = db.GetImageById(job);
            string? basePath = db.GetConfig("imagePath");

            if (string.IsNullOrWhiteSpace(basePath))
            {
                return StatusCode(500, new { error = "imagePath config not found." });
            }

            if (string.IsNullOrWhiteSpace(imagePath))
            {
                db.updateQueueStatus(job, 9); // error
                return BadRequest(new { error = "image path." });
            }

            imagePath = Path.Combine(basePath, imagePath);
            Console.WriteLine($"Attempting to load image at: |{imagePath}|");
            Console.WriteLine($"Running as user: {Environment.UserName}");
            try
            {
                using var fs = System.IO.File.OpenRead(imagePath);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Cannot read file: {ex.Message}");
            }

            if (!System.IO.File.Exists(imagePath))
            {
                db.updateQueueStatus(job, 9); // mark as error
                Console.WriteLine($"❌ Image file not found.");
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
                return StatusCode(500, new { error = "Failed to load image.", details = ex.Message });
            }

            // ✅ Now safe to update status to "processing"
            db.updateQueueStatus(job, 2);

            string base64Image = Convert.ToBase64String(imageBytes);

            return Ok(new
            {
                queueId = job,
                image = base64Image
            });
        }

        [HttpPost("submit_result")]
        public IActionResult SubmitResult([FromBody] JsonElement body)
        {
            var db = new DB(); // instance-based DB handler
            var trans = db.StartTransaction(); // manually start transaction

            try
            {
                // 📥 Log the full incoming payload
                Console.WriteLine("==== Incoming SubmitResult Payload ====");
                Console.WriteLine(JsonSerializer.Serialize(body, new JsonSerializerOptions { WriteIndented = true }));
                Console.WriteLine("========================================");

                // Extract queue ID
                string queueId = body.GetProperty("queueId").GetString() ?? "";
                Console.WriteLine($"🔹 Queue ID: {queueId}");

                // === CLASSIFICATION ===
                var classification = body.GetProperty("classification");
                string prediction = classification.GetProperty("prediction").GetString() ?? "";
                double classConfidence = classification.GetProperty("confidence").GetDouble();

                db.updateQueueStatus(queueId, 1); // mark as error
                Console.WriteLine($"🔸 Classification => Label: {prediction}, Confidence: {classConfidence}");
                db.InsertResult(queueId, 1, prediction, classConfidence); // Type 1 = Classification

                // === DETECTION ===
                var detection = body.GetProperty("detection");
                var objects = detection.GetProperty("objects").EnumerateArray();

                foreach (var obj in objects)
                {
                    string label = obj.GetProperty("label").GetString() ?? "";
                    double confidence = obj.GetProperty("confidence").GetDouble();

                    Console.WriteLine($"🔸 Detection => Label: {label}, Confidence: {confidence}");
                    db.InsertResult(queueId, 2, label, confidence); // Type 2 = Detection
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
