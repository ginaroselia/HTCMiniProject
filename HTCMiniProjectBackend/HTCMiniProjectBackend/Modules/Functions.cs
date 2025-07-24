using DB = HTCMiniProjectBackend.DatabaseOperations.DatabaseOp;

namespace HTCMiniProjectBackend.Modules
{
    public class Functions
    {
        public static string GenerateIDCode()
        {
            var db = new DB();
            string queueId = db.GetLatestQueueID();
            string newQueueId;
            if (queueId == "")
            {
                newQueueId = "ID00001";
            }
            else
            {
                int numberPart = int.Parse(queueId.Substring(2));
                numberPart++;
                newQueueId = "ID" + numberPart.ToString("D5"); // Ensures 5-digit padding
            }
            return newQueueId;
        }
    }
}
