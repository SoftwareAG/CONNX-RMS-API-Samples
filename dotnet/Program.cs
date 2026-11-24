using System.Data.Common;
using System.Data.Odbc;

if (args.Length == 0 || string.IsNullOrWhiteSpace(args[0]))
{
    Console.Error.WriteLine("Usage: dotnet run -- <customer-id>   (5 characters, case-sensitive; see docs/rms-mapping.md)");
    return 1;
}
var customerId = args[0];
var dsn = Environment.GetEnvironmentVariable("CONNX_RMS_DSN") ?? "CONNX_RMS";
var table = Environment.GetEnvironmentVariable("CONNX_RMS_TABLE") ?? "RMS.dbo.customers_rms";
var user = Environment.GetEnvironmentVariable("CONNX_RMS_USER");
var password = Environment.GetEnvironmentVariable("CONNX_RMS_PASSWORD");
// Brace-quote a value only when ODBC requires it (';', '{', '}' or surrounding spaces).
// The CONNX driver passes braces through literally, so quoting every value breaks ordinary logins.
static string Quote(string value) =>
    value.IndexOfAny(new[] { ';', '{', '}' }) >= 0 || value != value.Trim() ? "{" + value.Replace("}", "}}") + "}" : value;
var parts = new List<string> { $"DSN={dsn}" };
if (!string.IsNullOrWhiteSpace(user)) parts.Add($"UID={Quote(user)}");
if (!string.IsNullOrWhiteSpace(password)) parts.Add($"PWD={Quote(password)}");

await using var connection = new OdbcConnection(string.Join(';', parts) + ";");
await connection.OpenAsync();
await using var command = connection.CreateCommand();
command.CommandText = $"SELECT customerid, customername, customercity, customerstate, customerphone FROM {table} WHERE customerid = ?";
command.Parameters.Add("customerid", OdbcType.Char, 5).Value = customerId;
await using var reader = await command.ExecuteReaderAsync();
if (!await reader.ReadAsync()) { Console.WriteLine("Customer not found."); return 2; }

static string? Text(DbDataReader row, int ordinal) => row.IsDBNull(ordinal) ? null : row.GetString(ordinal).TrimEnd();
var customer = new Customer(Text(reader, 0)!, Text(reader, 1)!, Text(reader, 2), Text(reader, 3), Text(reader, 4));
Console.WriteLine($"{customer.Id}: {customer.Name} | {customer.City}, {customer.State} | {customer.Phone}");
return 0;

internal record Customer(string Id, string Name, string? City, string? State, string? Phone);
