# SignalQueue v2 supported contract

POST /exports accepts a request and returns HTTP 202 with an export_id and state="queued". Acceptance means processing will occur later; it is not a completion signal. GET /exports/{export_id} returns queued, running, complete, or failed. Only a complete result includes download_url. Failed results include error_code. No completion-time guarantee is defined.

The client must supply an Idempotency-Key header for POST /exports. Retrying with the same key returns the existing export; a new key creates another export. This is relevant after connection timeouts. No polling interval or rate limit is specified in this approved contract.

GET /exports/{export_id} requires exports:read scope. The existing authentication guide describes how users obtain a token; this fixture does not contain that guide.

The scope of this documentation review is first-time API integrators. The API implementation is not available locally. No credentials or service access are provided.
