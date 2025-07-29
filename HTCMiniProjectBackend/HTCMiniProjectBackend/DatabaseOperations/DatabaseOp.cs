using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc.RazorPages;
using MySql.Data.MySqlClient;
using System.Data;

namespace HTCMiniProjectBackend.DatabaseOperations
{
    public class DatabaseOp : IDisposable
    {
        private MySqlConnection? _conn;
        private MySqlTransaction? trans;

        public DatabaseOp()
        {
            string dbConnect = "Server=localhost;Port=3306;Database=htcproject;Uid=root;Pwd=password";
            _conn = new MySqlConnection(dbConnect);
            _conn.Open();
        }

        public void Dispose()
        {
            trans?.Dispose();
            if (_conn != null)
            {
                if (_conn.State != ConnectionState.Closed)
                    _conn.Close();
                _conn.Dispose();
            }
        }

        public MySqlTransaction StartTransaction()
        {
            if (_conn == null)
                throw new InvalidOperationException("Database connection has not been initialized.");
            return trans = _conn.BeginTransaction();
        }

        public int InsertQueue()
        {
            const string query = "INSERT INTO request_queue (`type`, `status`) VALUES ('0', '0');";
            using var cmd = new MySqlCommand(query, _conn, trans);
            cmd.ExecuteNonQuery();
            return Convert.ToInt32(cmd.LastInsertedId);
        }

        public bool InsertUrl(int id, string imageUrl)
        {
            const string query = @"INSERT INTO request_url (q_id, type, url) 
                                   VALUES (@qId, 0, @url);";
            using var cmd = new MySqlCommand(query, _conn, trans);
            cmd.Parameters.AddWithValue("@qId", id);
            cmd.Parameters.AddWithValue("@url", imageUrl);
            cmd.ExecuteNonQuery();
            return true;
        }

        public string? GetNextQueue()
        {
            const string query = "SELECT id_code FROM request_queue WHERE status = 0 LIMIT 1 FOR UPDATE";
            using var cmd = new MySqlCommand(query, _conn, trans);
            using var reader = cmd.ExecuteReader();
            return reader.Read() ? reader["id_code"].ToString() : null;
        }

        public string? GetConfig(string configName)
        {
            const string query = "SELECT details FROM config WHERE name = @name";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@name", configName);
            using var reader = cmd.ExecuteReader();
            return reader.Read() && !reader.IsDBNull(0) ? reader.GetString(0) : null;
        }

        public string? GetLatestQueueID()
        {
            const string query = "SELECT MAX(id_code) FROM request_queue";
            using var cmd = new MySqlCommand(query, _conn);
            using var reader = cmd.ExecuteReader();
            return reader.Read() && !reader.IsDBNull(0) ? reader.GetString(0) : null;
        }

        public List<Dictionary<string, object>> GetQueueResult(int queueId)
        {
            const string query = "SELECT * FROM request_result WHERE q_id = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);
            using var reader = cmd.ExecuteReader();

            var results = new List<Dictionary<string, object>>();
            while (reader.Read())
            {
                var row = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                {
                    row[reader.GetName(i)] = reader.GetValue(i);
                }
                results.Add(row);
            }
            return results;
        }

        public int CheckQueueStatus(int queueId)
        {
            const string query = "SELECT status FROM request_queue WHERE id_code = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);
            using var reader = cmd.ExecuteReader();
            return reader.Read() && !reader.IsDBNull(0) ? reader.GetInt32(0) : -1;
        }

        public string? GetResultImage(int queueId)
        {
            const string query = "SELECT image FROM request_result_image WHERE q_id = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);
            using var reader = cmd.ExecuteReader();
            return reader.Read() && !reader.IsDBNull(0) ? reader.GetString(0) : null;
        }

        public string? GetImageById(string queueId)
        {
            const string query = "SELECT url FROM request_url WHERE q_id = @qId";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@qId", queueId);
            using var reader = cmd.ExecuteReader();
            return reader.Read() && !reader.IsDBNull(0) ? reader.GetString(0) : null;
        }

        public int UpdateQueueStatus(string queueId, int status)
        {
            const string query = @"
                UPDATE request_queue 
                SET status = @status,
                    completed_date = CASE 
                        WHEN @status = 1 THEN CURRENT_TIMESTAMP
                        ELSE completed_date
                    END
                WHERE id_code = @id;";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@id", queueId);
            cmd.Parameters.AddWithValue("@status", status);
            return cmd.ExecuteNonQuery();
        }

        public void InsertResult(string queueId, int type, string result, double confidence)
        {
            const string query = @"
                INSERT INTO request_result (q_id, type, result, confidence)
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
            const string query = @"
                INSERT INTO request_result_image (q_id, image)
                VALUES (@queueId, @image);";
            using var cmd = new MySqlCommand(query, _conn);
            cmd.Parameters.AddWithValue("@queueId", queueId);
            cmd.Parameters.AddWithValue("@image", base64Image);
            cmd.ExecuteNonQuery();
        }

        public void InsertInferenceLog(string queueId, int? workerId, DateTime startTime, DateTime endTime)
        {
            const string query = @"INSERT INTO request_log (q_id, worker_id, start_time, end_time)
                           VALUES (@queueId, @workerId, @startTime, @endTime);";

            using var cmd = new MySqlCommand(query, _conn, trans);
            cmd.Parameters.AddWithValue("@queueId", queueId);
            cmd.Parameters.AddWithValue("@workerId", workerId ?? -1);
            cmd.Parameters.AddWithValue("@startTime", startTime);
            cmd.Parameters.AddWithValue("@endTime", endTime);
            cmd.ExecuteNonQuery();
        }
    }
}
