using DB = HTCMiniProjectBackend.DatabaseOperations.DatabaseOp;

namespace HTCMiniProjectBackend.Modules
{
    public class Functions
    {
        public static string GenerateIDCode(int id)
        {
            return "ID" + id.ToString("D5"); ;
        }
    }
}
