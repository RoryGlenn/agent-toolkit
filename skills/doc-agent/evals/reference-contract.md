# Pulse API reference source

Audience: experienced integrators needing exact lookup information, not a tutorial.

POST /pulse has four supported parameters: name (required string); enabled (optional boolean, defaults to true); interval_seconds (optional integer, 10–3600 inclusive, defaults to 60); labels (optional object mapping strings to strings, defaults to empty). All four parameters must appear in a complete reference. The response is 201 with id and the effective parameter values. Invalid fields return 400 with field and message. This fixture specifies no authentication mechanism, rate limit, SDK, or network service.
