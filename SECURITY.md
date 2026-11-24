# Security policy

## Reporting a vulnerability

Please do **not** report security vulnerabilities, credentials, or connection details in a public issue, pull request, or discussion.

Report suspected vulnerabilities privately using GitHub's private vulnerability reporting: open this repository's **Security** tab and select **Report a vulnerability**. Include:

- the affected file(s) or sample (Python API/CLI, .NET, or Java),
- steps to reproduce or a proof of concept,
- the impact you expect, and
- any suggested fix.

Remove passwords, DSN details, host names, and customer data from anything you send.

These samples are provided as-is and are not part of the supported Software AG product suite (see the end of the README). Reports are reviewed on a best-effort basis; there is no guaranteed response time. Vulnerabilities in the CONNX product itself, or in its ODBC/JDBC drivers, should be reported through your regular Software AG support channel rather than here.

## Supported versions

Only the latest commit on the `main` branch is maintained. Fixes are not backported.

## Secure usage

- Never commit `.env`, passwords, private keys, or production connection details.
- Use a least-privilege read-only DSN for the REST API.
- Keep the REST API read-only unless write access is explicitly authorized and controlled.
- Treat `CONNX_RMS_TABLE` as deployment configuration; do not derive it from request input.
- Do not expose detailed ODBC errors to API clients; the service logs details server-side and returns a generic 503.
- The sample API has no authentication. Put it behind your organization's API gateway or authentication layer before exposing it beyond a local demonstration.
