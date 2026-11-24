package com.connx.showcase;

import java.sql.*;

/** JDBC reader for the same CONNX-mapped OpenVMS RMS customer table used by the Python and .NET samples. */
public final class CustomerReader {
  private static final String DEFAULT_TABLE = "RMS.dbo.customers_rms";

  public static void main(String[] args) throws SQLException {
    if (args.length == 0 || args[0].isBlank()) {
      System.err.println("Usage: mvn compile exec:java -Dexec.args=<customer-id>   (5 characters, case-sensitive; see docs/rms-mapping.md)");
      System.exit(1);
    }
    String id = args[0];
    String url = required("CONNX_RMS_JDBC_URL");
    String user = System.getenv("CONNX_RMS_JDBC_USER");
    String password = System.getenv("CONNX_RMS_JDBC_PASSWORD");
    // The table name is deployment configuration, never user input; values are bound as parameters.
    String table = System.getenv().getOrDefault("CONNX_RMS_TABLE", DEFAULT_TABLE);
    if (table.isBlank()) table = DEFAULT_TABLE;
    String sql = "SELECT customerid, customername, customercity, customerstate, customerphone FROM " + table + " WHERE customerid = ?";
    try (Connection connection = (user == null || user.isBlank()) ? DriverManager.getConnection(url) : DriverManager.getConnection(url, user, password);
         PreparedStatement statement = connection.prepareStatement(sql)) {
      statement.setString(1, id);
      try (ResultSet result = statement.executeQuery()) {
        if (!result.next()) {
          System.out.println("Customer not found.");
          System.exit(2); // same exit code as the .NET sample
        }
        System.out.printf("%s: %s | %s, %s | %s%n", text(result, "customerid"), text(result, "customername"), text(result, "customercity"), text(result, "customerstate"), text(result, "customerphone"));
      }
    }
  }

  private static String required(String key) {
    String value = System.getenv(key);
    if (value == null || value.isBlank()) throw new IllegalStateException(key + " must be set");
    return value;
  }

  private static String text(ResultSet result, String column) throws SQLException {
    String value = result.getString(column);
    return value == null ? "" : value.stripTrailing();
  }
}
