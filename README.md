# CONNX + RMS Modernization Showcase

A customer-facing reference project showing modern applications reading the same OpenVMS RMS indexed file through a CONNX ODBC mapping. The sample uses the mapped table `RMS.dbo.customers_rms` and the `CONNX_RMS` DSN.

The project intentionally keeps RMS access behind small repository classes. Applications interact with normal customer objects while CONNX translates SQL to the mapped RMS indexed file. The mapped object is configurable through `CONNX_RMS_TABLE` and defaults to `RMS.dbo.customers_rms`.

> **Using your own RMS files?** The samples are written for one demonstration file, `CUSTOMER.DAT`, and its customer fields. Your RMS files will have different names, record layouts, and keys, so changing `CONNX_RMS_TABLE` alone is not enough. See [Adapting the samples to your own RMS files](#adapting-the-samples-to-your-own-rms-files).

> **Not production-ready as supplied.** The REST API has no authentication, no authorization, and no HTTPS/TLS. This is deliberate, to keep the sample small. Any production use requires you to add authentication and transport security first. See [Security: no authentication by design](#security-no-authentication-by-design).

## Why OpenVMS RMS data becomes siloed

OpenVMS Record Management Services (RMS) is a mature, high-performance record store built into the OpenVMS platform. An RMS indexed file is organized around records, fixed-width fields, and one or more indexes rather than tables, rows, and SQL constraints. This design is still effective for transactional workloads, but it is different from the relational model used by most modern application frameworks.

Over time, RMS data is commonly accessed by long-running OpenVMS applications written in languages such as COBOL, BASIC, FORTRAN, or C. The file definitions, record layouts, key semantics, and operational procedures are embedded in those applications and in the OpenVMS environment. Modern teams may therefore be able to see the business data, but not easily consume it from Python, .NET, Java, BI tools, or REST services. The result is a practical silo: the data is valuable and active, yet every new consumer must understand RMS-specific APIs, host connectivity, character layouts, and index behavior.

CONNX provides a bridge across that boundary. A CONNX administrator maps the RMS file and its record definition into a virtual relational table, such as `RMS.dbo.customers_rms`. CONNX exposes that mapping through standard database connectivity, including ODBC (and, where configured, JDBC), so applications can use familiar parameterized SQL and ordinary client libraries. The application does not need to rewrite the RMS file, copy it into a new database, or replace the existing OpenVMS system of record.

In this showcase, the Python repository is the boundary between application code and CONNX. It trims RMS fixed-width `CHAR` values, binds values as SQL parameters, and returns normal customer objects. The REST API and CLI then consume that repository just as they would consume a modern relational service. This separation lets an organization modernize access incrementally: keep the proven RMS workload in place, expose governed read access to new applications, and add writes only where the CONNX mapping and operational controls explicitly allow them.

## Why expose RMS data through modern APIs?

RMS systems often contain the authoritative customer, order, and operational data that the business already trusts. Requiring every new application to connect directly to OpenVMS or learn RMS-specific record APIs makes integration slow, duplicates connection logic, and increases the number of systems that need privileged access to the core platform.

A modern API creates a stable boundary around that data. Web applications, mobile clients, reporting tools, integration workflows, and cloud services can use HTTP and JSON without knowing whether the source is RMS, a relational database, or another backend. The API can centralize validation, field-name translation, authorization, logging, rate limits, and future compatibility decisions while the existing RMS application remains the system of record. In this sample, the REST surface is intentionally read-only so it can be safely demonstrated with a least-privilege CONNX account.

## Why use the OpenAPI standard?

OpenAPI provides a machine-readable contract for the REST API. FastAPI generates the contract and interactive documentation at `/openapi.json` and `/docs`, so a customer can inspect endpoints, parameters, response models, and error behavior before writing client code. The same document can be used by API tooling to generate client libraries, create test collections, validate requests, and publish an internal service catalog entry.

Using OpenAPI also keeps the demonstration honest: the documented read-only operations are the operations the service exposes, and the customer schema is visible as a deliberate contract rather than an implementation detail of the RMS file. If the RMS layout changes later, the repository can absorb that change while the API contract remains stable or is versioned explicitly (for example, under `/v1`).

## Layout

```
.
├── python/
│   ├── src/connx_rms_showcase/   Read-only repository, models, CLI, and FastAPI service
│   ├── tests/                    API tests using a repository test double (no CONNX needed)
│   ├── smoketest.py              Read-only connectivity check
│   ├── describe_table.py         Lists the columns and key of the configured table
│   └── client_example.py         httpx client for the REST API
├── dotnet/        .NET 8 console reader using ODBC
├── java/          Java 17 console reader using the CONNX JDBC driver
├── docs/          RMS file and CONNX mapping reference
└── .env.example   Shared configuration contract
```

## RMS mapping

The full mapping, including the RMS record layout and offsets, keys and indexes, the `customerid` format, and how to reproduce it in CONNX, is in [docs/rms-mapping.md](docs/rms-mapping.md). In summary:

| Column | RMS virtual relational type |
| --- | --- |
| `customerid` | `CHAR(5)` |
| `customername` | `CHAR(31)` |
| `customeraddress` | `CHAR(22)` |
| `customercity` | `CHAR(14)` |
| `customerstate` | `CHAR(10)` |
| `customerzip` | `CHAR(8)` |
| `customercountry` | `CHAR(7)` |
| `customerphone` | `CHAR(14)` |

RMS fixed-width `CHAR` values are trimmed by each sample before they reach callers. `customerid` is the RMS primary key (key 0): unique, case-sensitive, and the only indexed column. In the demonstration file, IDs are 5 upper-case letters. The sample uses strict ANSI-92 SQL; list-windowing is applied in Python because `OFFSET … FETCH` is not available.

## Quick start: Python

Prerequisites: Python 3.11+, the CONNX ODBC driver, and a configured `CONNX_RMS` DSN. On Windows, ensure the Python architecture matches the installed ODBC driver architecture.

### Required 64-bit ODBC connection

The Python process must use a 64-bit ODBC connection. Configure the DSN with the 64-bit ODBC Data Source Administrator (`ODBC Data Sources (64-bit)`), using the CONNX ODBC driver. That DSN must point to the CONNX Data Dictionary (CDD) containing the RMS file mapping and its virtual relational table definition.

For this showcase, the expected configuration is:

```text
DSN: CONNX_RMS
Driver: CONNX ODBC (64-bit)
CDD: the CONNX Data Dictionary containing the RMS customer mapping
Table: RMS.dbo.customers_rms
```

The `CONNX_RMS_DSN` value in `.env` must match the configured 64-bit DSN name. A 32-bit DSN or a DSN pointing at a different CDD can produce connection errors or make the mapped table appear to be missing, even when the RMS file itself is available.

### Install and run

Run these commands in PowerShell from the repository root (the folder containing this README):

```powershell
# 1. Work from the python folder
cd python

# 2. Confirm Python is 64-bit (must print 64)
python -c "import struct; print(struct.calcsize('P') * 8)"

# 3. Create the configuration file, then edit it
Copy-Item ..\.env.example .env
notepad .env

# 4. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 5. Install the sample with pinned dependency versions
pip install -c constraints.txt -e ".[dev]"

# 6. Check the CONNX connection (read-only)
python smoketest.py

# 7. Start the API
uvicorn connx_rms_showcase.api:app --reload
```

In step 3, set `CONNX_RMS_DSN` to your 64-bit DSN name and fill in `CONNX_RMS_USER` and `CONNX_RMS_PASSWORD` unless the DSN supplies credentials. When activation succeeds, the prompt starts with `(.venv)`.

If step 4 fails:

| Symptom | Fix |
| --- | --- |
| `Activate.ps1 cannot be loaded because running scripts is disabled on this system` | Allow local scripts for your account once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then run `.\.venv\Scripts\Activate.ps1` again. |
| `.\.venv\Scripts\Activate.ps1 is not recognized` or the `Scripts` folder is missing | The `.venv` folder is incomplete, or was created somewhere else. Make sure you are in the `python` folder, run `python -m venv --clear .venv`, then activate again. |
| You are using Command Prompt (`cmd.exe`) instead of PowerShell | Run `.venv\Scripts\activate.bat`. |
| You prefer not to activate | Prefix commands with the environment's Python instead, for example `.\.venv\Scripts\python.exe -m pip install -c constraints.txt -e ".[dev]"` and `.\.venv\Scripts\python.exe -m uvicorn connx_rms_showcase.api:app --reload`. |

If step 6 or 7 fails:

| Symptom | Fix |
| --- | --- |
| `uvicorn : The term 'uvicorn' is not recognized`, or `ModuleNotFoundError: No module named ...` | The sample is not installed in the active environment. Check that the prompt starts with `(.venv)` (if not, repeat step 4), then run step 5 and confirm it ends with `Successfully installed ...`. You can check with `pip show connx-rms-showcase`. |
| The smoke test reports a login or `Active Rejection` error | Check `CONNX_RMS_USER` and `CONNX_RMS_PASSWORD` in `.env`. |
| The smoke test reports `Data source name not found` | `CONNX_RMS_DSN` does not match a 64-bit DSN; see [Required 64-bit ODBC connection](#required-64-bit-odbc-connection). |

Browse `http://127.0.0.1:8000/docs`. The REST surface is deliberately read-only:

```text
GET /health
GET /ready
GET /v1/customers?limit=50&offset=0
GET /v1/customers/{customer_id}
```

`python smoketest.py` (step 6) performs a read-only connection check and queries `RMS.dbo.customers_rms`, reporting status without printing credentials or row contents. Fix any failure it reports before starting the API.

`/health` checks only that the process is running. `/ready` executes `SELECT 1` through CONNX and returns 503 when the data connection is unavailable. Every 503 includes a `Retry-After` header (5 seconds).

Every response includes an `X-Request-ID` header. Clients may send their own (up to 64 letters, digits, `.`, `_`, `:` or `-`; anything else is replaced with a generated ID). The API writes the ID on each of its log lines, including a one-line summary per request (`GET /v1/customers -> 200 (42 ms)`), so a failed client call can be found in the server log.

Run the example HTTP client in a second terminal. Each new terminal needs the virtual environment activated again:

```powershell
cd python
.\.venv\Scripts\Activate.ps1
python client_example.py
```

The client shows two practices worth copying: it retries connection errors, timeouts, and 502/503/504 responses up to four times with exponential backoff, honouring `Retry-After` (other errors, such as 404, are not retried); and it sends an `X-Request-ID` with every call, reusing it across retries and printing it when a call fails. Set `CONNX_RMS_API_URL` to point it at another API address.

Run automated API tests without a live CONNX connection:

```powershell
pytest
```

The CLI reads the same data from the command line, without the API:

```powershell
python -m connx_rms_showcase.cli list --limit 10
python -m connx_rms_showcase.cli get <customer-id>
```

Exit codes: `0` success, `1` customer not found, `2` invalid command or arguments, `3` CONNX/ODBC error. Errors are reported as a single message rather than a traceback.

## Security: no authentication by design

The REST API in this repository intentionally has **no authentication, no authorization, and no encryption in transit**. Anyone who can reach the port can read every record the CONNX account can read, over plain HTTP. We left security out on purpose:

- It keeps the sample focused on its subject, which is reaching RMS data through CONNX, rather than on one identity product.
- Every organisation already has its own identity provider, API gateway, certificate management, and security policies. A built-in scheme here would rarely match them, and could be copied into production by mistake.
- As supplied, it is safe only as a local demonstration: uvicorn listens on `127.0.0.1`, so only the same machine can connect, and the API is read-only.

**Any production use, or any deployment that other machines can reach, requires authentication and security to be added first.** At a minimum:

- **HTTPS/TLS on every connection.** Terminate TLS at a reverse proxy or API gateway, or configure uvicorn's `--ssl-certfile` and `--ssl-keyfile`, using certificates from your organisation's certificate authority. Never send customer data or credentials over plain HTTP.
- **Authentication for every caller.** Use your organisation's identity provider, for example OAuth 2.0 / OpenID Connect bearer tokens validated by an API gateway or in FastAPI (`fastapi.security`), or mutual TLS for service-to-service calls. Leave `/health` unauthenticated only if your monitoring requires it.
- **Authorization.** Decide which callers can read which data, and enforce it in the gateway or the API. Treat RMS customer data as confidential.
- **Least-privilege CONNX access.** Run the API with a read-only CONNX account limited to the tables it serves, Keep credentials in a secrets store or protected environment, never in source control.
- **Network controls.** Keep the API and the CONNX server on restricted networks, behind firewalls, and do not expose the OpenVMS host directly.
- **Abuse protection and auditing.** Add rate limits, request size limits, and audit logging (the `X-Request-ID` logging in this sample is a starting point), and review CORS if browsers will call the API.
- **Writes.** The samples are read-only: the API, CLI, .NET, and Java readers only run `SELECT` statements. If you add write operations, do not expose them through an API without authentication, authorization, input validation, and auditing designed for your environment.

Have your security team review the design before going live. See also [SECURITY.md](SECURITY.md).

## Running the API: uvicorn and alternatives

### Why uvicorn

FastAPI does not listen on a network port by itself. It builds an ASGI application (ASGI is the Python standard interface between web servers and async web frameworks), and a separate ASGI server accepts HTTP connections and passes requests to it. `uvicorn connx_rms_showcase.api:app` tells uvicorn to load the `app` object from `connx_rms_showcase/api.py` and serve it.

The samples use uvicorn because:

- It is the server the FastAPI documentation uses, and the one the `fastapi` command line runs underneath, so most FastAPI examples and troubleshooting advice assume it.
- It runs natively on Windows, Linux, and macOS, so the same command works on a developer PC and on a server.
- `--reload` restarts the server whenever a source file changes, which suits a demonstration you are editing.
- It is installed with the sample (`uvicorn[standard]` in `pyproject.toml`, pinned in `constraints.txt`), so step 5 already provides it.

The API's endpoints are ordinary (non-async) functions because `pyodbc` calls block while CONNX works. FastAPI runs each request in a worker thread, so a slow RMS query does not stop the server from answering other requests. This holds with any ASGI server.

### Development compared with production

The quick-start command is for development only:

```powershell
uvicorn connx_rms_showcase.api:app --reload
```

It listens only on `127.0.0.1` (this machine), port 8000, and watches files for changes. For a shared or long-running deployment, drop `--reload` and set the address, port, and number of worker processes explicitly, for example:

```powershell
uvicorn connx_rms_showcase.api:app --host 0.0.0.0 --port 8000 --workers 4
```

Each worker process opens its own CONNX connections, so size `--workers` with your CONNX licensing and the load on the OpenVMS host in mind. `--host 0.0.0.0` makes the API reachable from other machines, so do this only after adding the security described in [Security: no authentication by design](#security-no-authentication-by-design). The API has no authentication or TLS; in production, put it behind a reverse proxy or API gateway (for example IIS, nginx, or your organisation's gateway) that handles HTTPS and access control, and run it as a managed service so it restarts after failures and reboots.

### Alternatives

Any ASGI server can run the same `connx_rms_showcase.api:app` object without code changes. Install the alternative into the virtual environment first.

| Option | Example | When to consider it |
| --- | --- | --- |
| FastAPI CLI | `pip install "fastapi[standard]"`, then `fastapi dev src/connx_rms_showcase/api.py` or `fastapi run src/connx_rms_showcase/api.py` | A shorter command with development (`dev`) and production (`run`) defaults. It runs uvicorn underneath. |
| Hypercorn | `hypercorn connx_rms_showcase.api:app --bind 127.0.0.1:8000` | You need HTTP/2 (or HTTP/3) served directly by the Python process. |
| Granian | `granian --interface asgi connx_rms_showcase.api:app` | A server written in Rust, aimed at high throughput. With this API, CONNX and RMS response times usually matter more than server speed. |
| Gunicorn with uvicorn workers | `gunicorn connx_rms_showcase.api:app -k uvicorn_worker.UvicornWorker -w 4` (needs the `uvicorn-worker` package) | Linux or Unix servers where Gunicorn already manages processes. Gunicorn does not run on Windows. |
| Containers | Run any of the above in a container image | Deploying to Kubernetes or a container platform. The image needs the CONNX ODBC driver and a configured DSN. |

Whichever server you choose, keep `CONNX_RMS_*` settings in the environment or `.env`, and check `/ready` after starting to confirm the CONNX connection.

## .NET sample

Set the shared environment variables (or use your shell profile), then:

```powershell
cd dotnet
dotnet run -- <customer-id>
```

It uses `System.Data.Odbc` and parameterized SQL. Build it with `dotnet build`. The .NET and Java readers exit with `0` when the customer is found, `1` when no ID is given, and `2` when the customer is not found.

## Java sample

The Java sample uses the CONNX JDBC driver supplied with your CONNX installation. The driver JAR is not published to Maven Central and is not included in this repository. (The JDK's former JDBC-ODBC bridge was removed in Java 8, so a `jdbc:odbc:` URL does not work on Java 17.)

The driver is `connxjdbc.jar`, found under `CONNXJDBC\JAVA\JAR` in a Windows CONNX installation (for example `C:\CONNX32\CONNXJDBC\JAVA\JAR\connxjdbc.jar`). It connects to the CONNX JDBC Server service rather than to ODBC directly.

Set `CONNX_RMS_JDBC_URL` to a CONNX JDBC URL of the form `jdbc:connx:DSN=<jdbc-dsn>;Gateway=<jdbc-server-host>;PORT=7502`. The DSN must be one the CONNX JDBC Server knows about and must point at the CDD containing the RMS mapping; otherwise the driver reports `Server Registry Error. Dsn Probably not registered`. See the CONNX JDBC documentation for the other URL options. Also set `CONNX_RMS_JDBC_USER` and `CONNX_RMS_JDBC_PASSWORD` if needed. The sample queries `CONNX_RMS_TABLE`, which defaults to `RMS.dbo.customers_rms`.

```powershell
cd java
mvn compile exec:java "-Dconnx.jdbc.jar=C:\path\to\connx-jdbc-driver.jar" "-Dexec.args=<customer-id>"
```

## Adapting the samples to your own RMS files

Everything above runs against one demonstration file: `CUSTOMER.DAT`, mapped in CONNX as `RMS.dbo.customers_rms`, with eight fixed-width text fields and a 5-character key. Your RMS files will be different: other file and table names, other fields and widths, numeric, packed-decimal or date fields, different or multi-segment keys, and perhaps alternate keys. The samples do not discover the layout at run time. The column names, field lengths, and key column are written into the code, so a new file needs code changes as well as configuration.

Only `smoketest.py` and `describe_table.py` work against any table without code changes. Treat the rest as a pattern to copy: keep the structure (configuration, repository, models, API, CLI) and replace the customer-specific parts.

### 1. Map your RMS file in CONNX

Add the file and its record layout to a CONNX Data Dictionary (CDD), usually by importing the existing COBOL copybook, BASIC MAP, or FDL definition, and expose it as a table. Make sure each RMS key (key 0 and any alternate keys) is mapped as an index. [docs/rms-mapping.md](docs/rms-mapping.md) shows what this looks like for `CUSTOMER.DAT` and can serve as a checklist for your own file.

### 2. Point the configuration at your table

In `python\.env` (or your environment), set `CONNX_RMS_DSN` to a 64-bit DSN for that CDD and `CONNX_RMS_TABLE` to your table's full name in `catalog.schema.table` form. Then, from `python\` with the virtual environment active:

```powershell
python smoketest.py
python describe_table.py
```

`describe_table.py` is read-only. It prints each column's name, SQL type, and size, plus the primary key, from the ODBC catalog. It never prints row contents. Keep its output to hand: it gives you the values for the next steps.

### 3. Change the Python code

Search for the customer-specific names to find every place that needs a change:

```powershell
git grep -n -i customer -- python dotnet java
```

| File | What to change |
| --- | --- |
| `python/src/connx_rms_showcase/models.py` | Rename the models and fields. Set each `alias` to your CONNX column name and each `max_length` to the column size. Use the right Python type for non-text columns, for example `int`, `Decimal`, or `date`. |
| `python/src/connx_rms_showcase/repository.py` | Update `_COLUMNS` and the key column in every `WHERE` and `ORDER BY` clause. For a multi-segment key, match every key column in the `WHERE` clause. |
| `python/src/connx_rms_showcase/api.py` | Rename the routes (`/v1/customers`), the path parameter, the response models, and the OpenAPI tags. |
| `python/src/connx_rms_showcase/cli.py` | Update the help text and the `get` argument name to match your key. |
| `python/tests/` | Update the test doubles and expected fields, then run `pytest`. |

The REST API keeps its own field names (`customer_id`, `name`, and so on) separate from the CONNX column names. Keep that separation in your version: give API fields clear business names, even when the RMS field names are short or cryptic.

### 4. Change the .NET and Java readers

In `dotnet/Program.cs` and `java/src/main/java/com/connx/showcase/CustomerReader.java`, update the `SELECT` column list, the key column in the `WHERE` clause, the key parameter's type and length (`OdbcType.Char, 5` in .NET), and the printed output. Set `CONNX_RMS_TABLE` for both, as for Python.

### 5. Check your file's behaviour

- **Keys:** find out whether your key values are case-sensitive, padded, or numeric. `get` needs the exact key value.
- **Performance:** lookups on a mapped RMS key are fast. Filtering on other fields reads the whole file, so add an alternate key before adding search on large files.
- **Read-only access:** the samples never write to RMS. Give them a read-only CONNX account, so a mistake in adapted code cannot change the file that the OpenVMS applications depend on.
- **Live files:** the OpenVMS applications keep updating the file while you read it, so successive pages of `list` can shift if records are added or removed in between.

Finally, run `ruff check .` and `pytest` from `python\`, and build the .NET and Java samples, as described in [CONTRIBUTING.md](CONTRIBUTING.md).

## Operational notes

- Do not commit `.env` files or credentials. The samples read environment variables only.
- Use a least-privilege, read-only CONNX account. The samples only read RMS data.
- ODBC parameter markers (`?`) are used for data values. Table and column names are constants, never user input.
- The API maps database failures to a generic 503 response and logs details server-side.
- RMS `CHAR` fields are fixed-width. The repository trims trailing spaces and validates documented maximum lengths.
- `CONNX_RMS_TABLE` defaults to `RMS.dbo.customers_rms`; set it explicitly for another mapped object, and see [Adapting the samples to your own RMS files](#adapting-the-samples-to-your-own-rms-files) for the code changes a new table needs.
- Python list paging is applied after an ANSI-92 ordered query because this CONNX configuration does not support `OFFSET … FETCH`.

______________________

These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.
