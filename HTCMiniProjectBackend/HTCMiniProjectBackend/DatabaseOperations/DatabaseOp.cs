using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc.RazorPages;
using MySql.Data.MySqlClient;

namespace HTCMiniProjectBackend.DatabaseOperations
{

    public class DatabaseOp: IDisposable
    {
        private MySqlConnection? _conn;
        private MySqlTransaction? trans;

        public DatabaseOp()
        {
            string dbConnect = "Server=localhost;Port=3306;Database=htcproject;Uid=root;Pwd=password";
            var connection = new MySqlConnection(dbConnect);
            connection.Open();
            _conn = connection;
        }

        public void Dispose()
        {
            trans?.Dispose();

            if (_conn != null)
            {
                if (_conn.State != System.Data.ConnectionState.Closed)
                    _conn.Close();

                _conn.Dispose();
            }
        }

        public bool InsertQueue(string id)
        {
            // insert data into queue
            string query = "INSERT INTO `request_queue` " +
                "(`id_code`, `type`, `status`) VALUES " +
                "(@id_code, '0', '0');";

            using var cmd = new MySqlCommand(query, _conn, trans);
            cmd.Parameters.AddWithValue("@id_code", id);
            cmd.ExecuteNonQuery();
            return true;
        }

        public bool InsertUrl(string id, string imageUrl)
        {
            // insert data into url
            string query = "INSERT INTO `request_url` " +
                "(`q_id`, `type`, `url`) VALUES " +
                "(@qId, '0', @url);";

            using var cmd = new MySqlCommand(query, _conn, trans);
            cmd.Parameters.AddWithValue("@qId", id);
            cmd.Parameters.AddWithValue("@url", imageUrl);
            cmd.ExecuteNonQuery();
            return true;
        }

        public string? GetNextQueue()
        {
            string query = "SELECT id_code FROM request_queue WHERE status = 0 LIMIT 1 FOR UPDATE";

            using var cmd = new MySqlCommand(query, _conn);
            using var reader = cmd.ExecuteReader();

            if (reader.Read())
            {
                return reader.GetString("id_code");
            }

            return null;
        }

        public string? GetConfig(string configName)
        {
            const string query = "SELECT details FROM config WHERE name = @name";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@name", configName);
            using var reader = cmd.ExecuteReader();

            if (reader.Read() && !reader.IsDBNull(0))
            {
                return reader.GetString(0);
            }

            return null; // or return "" if you prefer
        }



        public string? GetLatestQueueID()
        {
            const string query = "SELECT MAX(id_code) FROM request_queue";
            using var cmd = new MySqlCommand(query, _conn);
            using var reader = cmd.ExecuteReader();

            if (reader.Read() && !reader.IsDBNull(0))
            {
                return reader.GetString(0);
            }

            return null; //
        }

        public MySqlTransaction StartTransaction()
        {
            if (_conn == null)
                throw new InvalidOperationException(
                    "Database connection has not been initialized.");

            return trans = _conn.BeginTransaction();
        }

        public List<Dictionary<string, object>> GetQueueResult(string queueId)
        {
            string query = "SELECT * FROM request_result WHERE q_id = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);

            using var reader = cmd.ExecuteReader();

            var results = new List<Dictionary<string, object>>();

            while (reader.Read())
            {
                var row = new Dictionary<string, object>();

                for (int i = 0; i < reader.FieldCount; i++)
                {
                    string columnName = reader.GetName(i);
                    object value = reader.GetValue(i);
                    row[columnName] = value;
                }

                results.Add(row);
            }

            return results;
        }
        public int CheckQueueStatus(string queueId)
        {
            const string query = "SELECT status FROM request_queue WHERE id_code = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);

            using var reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                return reader.IsDBNull(0) ? -1 : reader.GetInt32(0);
            }

            // If no rows were returned, treat as invalid/missing
            return -1;
        }


        public string? GetResultImage(string queueId)
        {
            const string query = "SELECT image FROM request_result_image WHERE q_id = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);

            using var reader = cmd.ExecuteReader();
            if (reader.Read() && !reader.IsDBNull(0))
            {
                return reader.GetString(0);
            }

            return null; // Return null when not found or empty
        }

        public string? GetImageById(string queueId)
        {
            const string query = "SELECT url FROM request_url WHERE q_id = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);

            using var reader = cmd.ExecuteReader();
            if (reader.Read() && !reader.IsDBNull(0))
            {
                return reader.GetString(0);
            }

            return null; // or string.Empty if you prefer
        }

        public int updateQueueStatus(string queueId, int status)
        {
            string query = "Update request_queue SET status = @status where id_code = @id";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@id", queueId);
            cmd.Parameters.AddWithValue("@status", status);
            return cmd.ExecuteNonQuery();
        }

        public void InsertResult(string queueId, int type, string result, double confidence)
        {
            const string query = @"INSERT INTO request_result (q_id, type, result, confidence)
                VALUES (@queueId, @type, @result, @confidence);";

            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@queueId", queueId);
            cmd.Parameters.AddWithValue("@type", type);
            cmd.Parameters.AddWithValue("@result", result);
            cmd.Parameters.AddWithValue("@confidence", confidence);
            cmd.ExecuteNonQuery();
        }
        public void InsertResultImage(string queueId, string base64Image)
        {
            const string query = @"INSERT INTO request_result_image (q_id, image) VALUES (@queueId, @image);";

            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@queueId", queueId);
            cmd.Parameters.AddWithValue("@image", base64Image);
            cmd.ExecuteNonQuery();
        }
    }
}
