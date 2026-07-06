# HTTP Client Specification

**Module:** `app/core/http_client.py` (planned)  
**Status:** Design specification — implementation pending  
**Related documents:** [AI_CONTEXT.md](../AI_CONTEXT.md)

This document defines the complete design specification for the centralized HTTP Client used throughout **InternIntel**. It is implementation-independent and serves as the engineering contract that must be satisfied before writing code.

---

## 1. Purpose

InternIntel monitors multiple career pages and ATS platforms that require reliable, repeatable HTTP access. Without a centralized client, each scraper would independently configure timeouts, user agents, retries, logging, and error handling. That approach leads to duplicated logic, inconsistent behavior, and difficult maintenance.

The centralized HTTP Client exists to:

- Provide a **single entry point** for all outbound HTTP traffic in the application
- Enforce **consistent network behavior** across scrapers and services
- Centralize **configuration, logging, retries, and error handling**
- Keep scrapers focused on **parsing and business logic**, not transport concerns
- Make network behavior **testable and mockable** through a stable public API

Per project architecture rules, **no module outside the HTTP Client may call httpx directly**. Scrapers, ATS connectors, and services must depend on this client for all standard HTTP operations.

---

## 2. Responsibilities

The HTTP Client is responsible for the following:

| Responsibility | Description |
|----------------|-------------|
| **HTTP GET requests** | Fetch resources from remote URLs |
| **HTTP POST requests** | Submit data to remote endpoints when required by a source |
| **Shared client/session management** | Reuse a single underlying connection pool across requests |
| **Configurable timeouts** | Apply request, connect, and read timeout limits |
| **Configurable User-Agent** | Send a consistent, identifiable agent string |
| **Custom request headers** | Accept per-request header overrides without bypassing the client |
| **Retry support** | Automatically retry transient failures up to a configured limit |
| **Exponential backoff** | Increase wait time between retries to reduce load on failing targets |
| **Request logging** | Log outbound requests through the centralized Loguru logger |
| **Response timing** | Measure and record elapsed time per request |
| **Exception normalization** | Translate low-level library errors into meaningful application exceptions |

The client returns **raw HTTP responses** (status code, headers, body) to the caller. Interpretation of response content is explicitly outside its scope.

---

## 3. Non-Responsibilities

The HTTP Client must **not** perform any of the following:

- **Parse HTML** — delegated to BeautifulSoup in scraper layers
- **Parse JSON into models** — delegated to scrapers or services
- **Perform scraping logic** — no knowledge of internships, companies, or ATS platforms
- **Save data to the database** — persistence belongs in services
- **Deduplicate internships** — business logic belongs in services

The client is **transport infrastructure only**. It fetches and returns HTTP responses; callers decide what to do with them.

---

## 4. Public API

The HTTP Client exposes a small, stable interface intended for reuse across the codebase.

### Class: `HttpClient`

| Method | Description |
|--------|-------------|
| `get(url, **options)` | Perform an HTTP GET request |
| `post(url, **options)` | Perform an HTTP POST request |
| `close()` | Release underlying connections and clean up resources |

A module-level shared instance may also be exported for convenience, following the same pattern as `settings` and `logger`.

### `get(url, **options)`

Perform an HTTP GET request.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Target URL |
| `params` | `dict` | No | Query string parameters |
| `headers` | `dict` | No | Additional request headers merged with defaults |
| `timeout` | `float` or `tuple` | No | Per-request timeout override |
| `follow_redirects` | `bool` | No | Override default redirect behavior |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `status_code` | `int` | HTTP response status code |
| `headers` | `dict` | Response headers |
| `text` | `str` | Response body as text |
| `content` | `bytes` | Response body as raw bytes |
| `elapsed_ms` | `float` | Total request duration in milliseconds |
| `url` | `str` | Final URL after redirects |

**Raises:**

- `HttpClientError` — base exception for client failures
- `HttpTimeoutError` — request exceeded configured timeout
- `HttpConnectionError` — connection could not be established
- `HttpRetryExhaustedError` — all retry attempts failed

### `post(url, **options)`

Perform an HTTP POST request.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Target URL |
| `data` | `dict` or `str` | No | Form or raw request body |
| `json` | `dict` | No | JSON-encoded request body |
| `headers` | `dict` | No | Additional request headers merged with defaults |
| `timeout` | `float` or `tuple` | No | Per-request timeout override |
| `follow_redirects` | `bool` | No | Override default redirect behavior |

**Returns:** Same response structure as `get()`.

**Raises:** Same exceptions as `get()`.

### `close()`

Release the underlying HTTP session and connection pool.

**Parameters:** None

**Returns:** None

**Behavior:** Safe to call multiple times. Should be invoked during application shutdown or test teardown.

---

## Request Lifecycle

Every HTTP request processed by the client must follow the same lifecycle. No request may bypass any stage.

```
Caller
    ↓
Validate Input
    ↓
Load Configuration
    ↓
Merge Default Headers
    ↓
Prepare Request
    ↓
Send Request
    ↓
Retry (if required)
    ↓
Log Result
    ↓
Normalize Exceptions
    ↓
Return Response
```

| Stage | Description |
|-------|-------------|
| **Validate Input** | Reject empty URLs, invalid timeouts, and malformed options before any network activity |
| **Load Configuration** | Resolve timeouts, retries, user agent, and redirect behavior from the Config Loader |
| **Merge Default Headers** | Apply default headers (including User-Agent) and merge per-request overrides |
| **Prepare Request** | Build the final request with resolved configuration and headers |
| **Send Request** | Dispatch through the shared underlying httpx client |
| **Retry (if required)** | Apply exponential backoff for retryable failures up to the configured limit |
| **Log Result** | Record method, URL, status, timing, and retry count through the centralized logger |
| **Normalize Exceptions** | Translate low-level errors into application-level exceptions |
| **Return Response** | Return a stable response abstraction to the caller |

Both `get()` and `post()` must execute this full lifecycle on every invocation.

---

## Connection Management

The HTTP Client must maintain **one shared `httpx.Client` instance** for the lifetime of the application process.

| Rule | Description |
|------|-------------|
| **Reuse the shared client** | A single `httpx.Client` instance serves all requests |
| **Never create per-request clients** | Do not instantiate a new client for every `get()` or `post()` call |
| **Reuse TCP connections** | Keep-alive connections reduce handshake overhead across requests to the same host |
| **Reuse TLS sessions** | Session resumption avoids repeated TLS negotiation |
| **Reuse connection pools** | Pooled connections improve throughput during scrape runs |
| **Close only on shutdown** | Call `close()` during application shutdown or test teardown |

Connection reuse significantly improves performance during scraping workloads, where many requests target the same career page or ATS host in rapid succession. Creating a new client per request forces a new TCP connection and TLS handshake each time, increasing latency and resource consumption.

---

## Response Abstraction

Callers should interact with a stable **`HttpResponse` abstraction** rather than depending directly on `httpx.Response`. This insulates scrapers and services from the underlying HTTP library and keeps the public API stable if the transport layer changes.

### Planned Fields

| Field | Type | Description |
|-------|------|-------------|
| `status_code` | `int` | HTTP response status code |
| `headers` | `dict` | Response headers |
| `text` | `str` | Response body as text |
| `content` | `bytes` | Response body as raw bytes |
| `elapsed_ms` | `float` | Total request duration in milliseconds |
| `url` | `str` | Final URL after redirects |

### Extensibility

The following fields may be added in future versions without breaking the public API:

| Field | Type | Description |
|-------|------|-------------|
| `retry_count` | `int` | Number of retries performed before success or failure |
| `from_cache` | `bool` | Whether the response was served from cache |
| `request_id` | `str` | Correlation identifier for logging and tracing |

This is a **design note only**. `HttpResponse` is not implemented in this specification.

---

## 5. Configuration

All HTTP Client configuration must come from the **Config Loader** (`app.core.config.settings`). No hardcoded values are permitted.

### Configuration Keys

The following settings are expected under the `scraper` and future `http` namespaces in `settings.yaml`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `scraper.timeout` | `int` | `30` | Total request timeout in seconds |
| `scraper.user_agent` | `str` | `InternIntelBot/1.0` | Default User-Agent header |
| `http.connect_timeout` | `float` | `10` | Connection establishment timeout (planned) |
| `http.read_timeout` | `float` | `30` | Response read timeout (planned) |
| `http.retries` | `int` | `3` | Maximum number of retry attempts (planned) |
| `http.backoff_factor` | `float` | `0.5` | Exponential backoff multiplier (planned) |
| `http.follow_redirects` | `bool` | `true` | Whether to follow HTTP redirects (planned) |

### Configuration Rules

- Read all values through `settings.get("key.subkey")`
- Apply defaults only when a key is absent — defaults must be documented, not hidden in scrapers
- Support per-request overrides for `timeout` and `headers` without bypassing the client
- Never read YAML directly inside the HTTP Client module

### Currently Available Settings

The following keys already exist in `app/config/settings.yaml`:

- `scraper.timeout`
- `scraper.user_agent`

Additional keys listed above are planned and should be added to configuration when the client is implemented.

---

## Configuration Resolution

Configuration values are resolved in strict priority order. Scrapers must never bypass this order by hardcoding values or reading YAML directly.

```
Per-request override
        ↓
settings.yaml
        ↓
Built-in documented default
```

| Priority | Source | Example |
|----------|--------|---------|
| **1 — Highest** | Per-request override | `timeout` passed to `get()` or `post()` |
| **2** | `settings.yaml` via Config Loader | `settings.get("scraper.timeout")` |
| **3 — Lowest** | Built-in documented default | Default defined in this specification |

Per-request overrides apply only to the current call. Global defaults always fall back through `settings.yaml` before using built-in defaults.

---

## 6. Retry Strategy

The HTTP Client must implement a predictable, configurable retry strategy for transient failures.

### Exponential Backoff

Wait time between retries increases exponentially based on the backoff factor:

```
wait_time = backoff_factor × (2 ^ attempt_number)
```

Example with `backoff_factor = 0.5`:

| Attempt | Wait Before Retry |
|---------|-------------------|
| 1 | 0.5 seconds |
| 2 | 1.0 seconds |
| 3 | 2.0 seconds |

### Retryable Status Codes

The following HTTP status codes should trigger a retry by default:

| Status Code | Reason |
|-------------|--------|
| `408` | Request Timeout |
| `429` | Too Many Requests |
| `500` | Internal Server Error |
| `502` | Bad Gateway |
| `503` | Service Unavailable |
| `504` | Gateway Timeout |

Non-retryable client errors (`4xx` except `408` and `429`) must fail immediately without retry.

### Retryable Exceptions

The following exception categories should trigger a retry:

- Connection timeouts
- Read timeouts
- Connection refused or reset
- DNS resolution failures (transient)
- Network unreachable errors

### Maximum Retries

- Controlled by `http.retries` configuration (default: `3`)
- Total attempts = `1` initial request + up to `http.retries` retries
- When all retries are exhausted, raise `HttpRetryExhaustedError` with context about the last failure

---

## 7. Logging

All HTTP Client logging must use the centralized logger from `app.core.logger`. No `print()` statements are permitted.

### What to Log

| Event | Fields |
|-------|--------|
| **Request start** | method, URL |
| **Request success** | method, URL, status code, response time (ms), retry count |
| **Request failure** | method, URL, error type, response time (ms), retry count |
| **Retry attempt** | method, URL, attempt number, wait time, reason |

### Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Request start, retry wait details |
| `INFO` | Successful responses |
| `WARNING` | Retries and recoverable failures |
| `ERROR` | Exhausted retries and unrecoverable failures |

### Security

- **Do not log secrets** — omit authorization tokens, API keys, cookies, and credentials
- **Do not log full request or response bodies** by default — bodies may contain sensitive data
- Truncate or redact sensitive header values such as `Authorization` and `Cookie`

---

## Sequence Diagram

The following sequence shows how a request flows through the system:

```
Scraper
    │
    ▼
HttpClient
    │
    ▼
Logger
    │
    ▼
httpx
    │
    ▼
Website
    │
    ▼
Response
    │
    ▼
Logger
    │
    ▼
Scraper
```

The scraper initiates the request. The HTTP Client handles transport, delegates logging at key stages, and returns a normalized response. The scraper remains responsible for interpreting response content.

---

## Thread Safety

The HTTP Client is designed for reuse across the application's supported execution model.

- **Shared `HttpClient` instances should be safe for concurrent use** within the supported execution model
- **Prefer long-lived clients** created once at startup and reused across scrape runs
- **Avoid creating temporary clients** that are discarded after a single request or short-lived task

Connection pooling and the underlying `httpx.Client` are intended to support concurrent requests safely. Callers should not create separate client instances per thread unless explicitly required by a future extension.

---

## 8. Error Handling

The HTTP Client must raise **meaningful, application-level exceptions** instead of exposing raw httpx or network library errors to callers.

### Planned Exception Hierarchy

| Exception | Description |
|-----------|-------------|
| `HttpClientError` | Base exception for all HTTP client failures |
| `HttpTimeoutError` | Request exceeded configured timeout |
| `HttpConnectionError` | Connection could not be established |
| `HttpStatusError` | Non-success HTTP status after retries exhausted |
| `HttpRetryExhaustedError` | All retry attempts failed |

### Error Handling Rules

- **Never silently ignore exceptions**
- **Log meaningful context** before raising (URL, method, status code, attempt count)
- **Re-raise unexpected exceptions** wrapped in `HttpClientError` with original cause preserved
- **Validate inputs** — reject empty URLs and invalid timeout values before making requests
- **Fail fast on invalid configuration** — do not proceed with missing or malformed settings

Callers (scrapers and services) should catch specific exceptions where recovery is possible and allow unexpected errors to propagate after logging.

---

## 9. Future Extensions

The initial implementation covers synchronous GET and POST requests. The following capabilities are planned for future versions:

| Extension | Description |
|-----------|-------------|
| **Async requests** | Non-blocking HTTP operations for concurrent scraping |
| **Proxy support** | Route requests through configurable HTTP or SOCKS proxies |
| **Rate limiting** | Throttle outbound requests per host to avoid blocking |
| **Caching** | Cache immutable responses with configurable TTL |
| **HTTP/2** | Enable HTTP/2 where supported by the underlying transport |
| **Connection pooling** | Advanced pool sizing and keep-alive tuning |

Future extensions must not break the existing public API. New behavior should be opt-in through configuration.

---

## Future HTTP Methods

Version 1 of the HTTP Client includes **GET** and **POST** only. The following methods are planned for future versions:

| Method | Planned Use |
|--------|-------------|
| **HEAD** | Check resource availability without downloading the body |
| **OPTIONS** | Discover supported methods and CORS behavior |
| **PUT** | Replace resources on endpoints that require it |
| **PATCH** | Partial updates on endpoints that require it |
| **DELETE** | Remove resources on endpoints that require it |

New methods must follow the same request lifecycle, configuration resolution, logging, and error handling rules defined in this specification. Only **GET** and **POST** are in scope for Version 1.

---

## 10. Example Usage

The following examples illustrate intended usage patterns. They are illustrative only and do not represent implemented code.

### Basic GET Request

```
Import the shared HTTP client.

Call client.get() with a career page URL.

Receive a response containing status_code, text, and elapsed_ms.

Pass the response text to a scraper for HTML parsing.
```

### GET with Query Parameters

```
Call client.get() with a URL and params dictionary.

The client appends query parameters and sends the request.

Use the returned text body for JSON or HTML parsing in the scraper layer.
```

### POST Request

```
Call client.post() with a URL and json payload.

Use for ATS platforms that expose JSON submission endpoints.

Handle the response in the calling scraper or service.
```

### Custom Headers

```
Call client.get() with additional headers.

Custom headers are merged with defaults such as User-Agent.

Authorization headers are supported but must not appear in logs.
```

### Cleanup

```
Call client.close() during application shutdown or test teardown.

Releases the underlying connection pool.
```

### Dependency Injection in Scrapers

```
A company scraper receives an HttpClient instance via constructor injection.

The scraper calls client.get() but does not configure httpx directly.

This enables unit tests to substitute a mock client.
```

---

## 11. Design Principles

The HTTP Client must adhere to the following design principles, consistent with the InternIntel engineering specification:

| Principle | Application |
|-----------|-------------|
| **Single responsibility** | Handle HTTP transport only — no parsing, persistence, or business logic |
| **Reusable infrastructure** | One client shared across all scrapers, connectors, and services |
| **Framework independent** | No coupling to FastAPI, Flask, or other web frameworks |
| **Testable** | Public API supports mocking and dependency injection in unit tests |
| **Dependency injection friendly** | Accept client instance via constructor in scrapers and services |
| **Configuration through Config Loader** | All defaults and limits come from `settings.get()` |
| **Centralized logging** | All log output goes through `app.core.logger` |
| **Explicit behavior** | Retries, timeouts, and failures are predictable and documented |

---

## Design Constraints

The HTTP Client implementation must respect the following hard constraints:

- **No business logic**
- **No HTML parsing**
- **No ORM access**
- **No database writes**
- **No scraper-specific behavior**
- **No framework coupling**
- **No global mutable state** outside the shared client instance

These constraints align with the [Non-Responsibilities](#3-non-responsibilities) defined in this specification and the dependency rules in `AI_CONTEXT.md`.

---

## Testing Strategy

The HTTP Client must include comprehensive unit tests. All network calls must be **mocked** — tests must not depend on live external websites.

### Planned Test Cases

| Test Case | Description |
|-----------|-------------|
| **Successful request** | Verify correct response fields and logging on a `200` response |
| **Timeout** | Verify `HttpTimeoutError` when request exceeds configured timeout |
| **Retry** | Verify retry is attempted on retryable status codes and exceptions |
| **Retry exhaustion** | Verify `HttpRetryExhaustedError` when all attempts fail |
| **Logging** | Verify request, success, failure, and retry events are logged correctly |
| **Header merging** | Verify default headers merge with per-request overrides |
| **Redirect handling** | Verify redirects are followed when configured |
| **Invalid configuration** | Verify fail-fast behavior on missing or malformed settings |
| **Invalid URL** | Verify input validation rejects empty or malformed URLs |
| **Connection failures** | Verify `HttpConnectionError` on unreachable hosts |

Tests should use dependency injection or mocking to substitute the underlying httpx transport. No test may make real outbound HTTP requests to external services.

---

## Quality Gate

Before the HTTP Client implementation is considered complete, it must satisfy every item in the [Quality Gate](../AI_CONTEXT.md#quality-gate) defined in `AI_CONTEXT.md`, including:

- Black formatting
- Ruff linting
- Pytest coverage for retries, timeouts, and error normalization
- Type hints and Google-style docstrings
- Architecture and dependency rule compliance

---

*Last updated: July 2026*
