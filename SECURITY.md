# Security policy

## Supported scope

This project is an offline analyzer for synthetic or already-authorized, sanitized JSON fixtures. It does not send HTTP requests, import browser state, process packet captures, or provide login, signature, challenge-solving, scraping, credential-testing, or access-control bypass features.

## Sensitive data

Do not rely on the built-in redactor as permission to ingest raw production traffic. Remove customer data and secrets before creating a fixture. The redactor masks common authorization, cookie, token, password, secret, email and phone locations, and masks every query value, but unknown application-specific fields may remain.

Generated contracts retain origins, normalized path templates, header names, query parameter names, body field names and data types. Those names can themselves be sensitive in a private system. Review outputs before sharing them.

## Input limits

- 2 MiB maximum per JSON input file.
- 1,000 captures maximum per command.
- Only `http` and `https` URLs without username or password components are accepted.
- Fixture content is parsed as JSON and never executed.
- Existing outputs are not overwritten.

## Reporting a vulnerability

Use the repository's private security reporting channel after publication. Until then, report findings to the project owner through the existing private coordination channel. Do not attach live credentials, session cookies or customer payloads.
