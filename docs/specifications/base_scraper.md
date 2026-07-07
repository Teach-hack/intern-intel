# Base Scraper Specification

**Module:** `app/core/base_scraper.py` (planned)  
**Status:** Design specification — implementation pending  
**Related documents:** [AI_CONTEXT.md](../AI_CONTEXT.md), [HTTP Client Specification](http_client.md)

This document defines the complete design specification for the Base Scraper used throughout **InternIntel**. It is implementation-independent and serves as the engineering contract that must be satisfied before writing code.

---

## 1. Purpose

InternIntel discovers internships from multiple career pages and ATS platforms. Each source has a unique page structure, API format, and listing schema. Without a shared abstraction, every company scraper would independently implement fetching, parsing, normalization, validation, logging, and error handling. That approach leads to duplicated logic, inconsistent data quality, and difficult maintenance.

The Base Scraper exists to:

- Define a **mandatory scraping lifecycle** that every source implementation must follow
- Enforce **consistent data normalization** so all listings match the Internship model schema
- Centralize **validation, logging, and error handling** across all scrapers
- Keep company scrapers focused on **source-specific parsing only**
- Make scraping behavior **testable and mockable** through a stable abstract interface
- Accept the **HTTP Client via dependency injection** to decouple transport from parsing

Per project architecture rules, **no company scraper or ATS connector may implement its own fetch, validation, or normalization logic**. All source implementations must extend the Base Scraper and follow the lifecycle defined in this specification.

---

## 2. Responsibilities

The Base Scraper is responsible for the following:

| Responsibility | Description |
|----------------|-------------|
| **Orchestrate the scraping lifecycle** | Execute the mandatory sequence of fetch, parse, normalize, validate, and return |
| **Fetch pages via HttpClient** | Delegate all HTTP requests to the injected HttpClient instance |
| **Define the parsing contract** | Require subclasses to implement source-specific parsing |
| **Define the normalization contract** | Require subclasses to map raw fields to the Internship schema |
| **Validate normalized listings** | Reject incomplete or malformed listings before returning them |
| **Log scraping activity** | Record lifecycle events through the centralized Loguru logger |
| **Handle scraping errors** | Catch, log, and re-raise errors using the application exception hierarchy |
| **Provide a source identifier** | Require subclasses to declare their source name for traceability |

The Base Scraper returns **normalized listing dicts** to the caller. It does not interpret, rank, persist, or distribute the data it produces.

---

## 3. Non-Responsibilities

The Base Scraper must **not** perform any of the following:

- **Write to the database** — persistence belongs in the service layer
- **Read from the database** — deduplication and lookups belong in the service layer
- **Send notifications** — alerting belongs in the notification layer
- **Deduplicate listings** — deduplication by URL is a service-layer concern
- **Rank or score listings** — business logic belongs in services
- **Contain company-specific parsing** — source-specific logic belongs in subclasses
- **Configure HTTP transport** — timeouts, retries, and user agents are the HTTP Client's responsibility
- **Retry failed requests** — retry logic belongs exclusively to the HTTP Client
- **Call httpx directly** — all HTTP access must flow through the injected HttpClient

The Base Scraper is **scraping infrastructure only**. It orchestrates the lifecycle and enforces contracts; subclasses and services decide what to parse and what to do with the results.

---

## 4. Public API

The Base Scraper exposes a small, stable interface intended for extension by all ATS connectors and company scrapers.

### Class: `BaseScraper`

| Method | Type | Description |
|--------|------|-------------|
| `scrape(url)` | Concrete | Orchestrate the full scraping lifecycle |
| `fetch_page(url)` | Concrete | Fetch a page via the injected HttpClient |
| `parse_listings(content)` | Abstract | Extract raw listing dicts from HTML or JSON |
| `normalize(raw)` | Abstract | Map a raw listing dict to the normalized schema |
| `validate(listing)` | Concrete | Check that required fields are present and non-empty |
| `get_source_name()` | Abstract | Return the source identifier string |

### `scrape(url)`

Orchestrate the full scraping lifecycle for a given URL.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Target career page or API endpoint URL |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `listings` | `list[dict]` | Normalized, validated internship dicts |

**Raises:**

- `ScraperError` — base exception for any scraping failure
- `ScraperParsingError` — subclass failed to parse response content
- `ScraperBlockedError` — target site blocked the request
- `HttpClientError` — HTTP transport failure (propagated from HttpClient)

**Behavior:**

1. Call `fetch_page(url)` to retrieve the page content
2. Call `parse_listings(content)` to extract raw listing dicts
3. For each raw listing, call `normalize(raw)` to produce a normalized dict
4. For each normalized listing, call `validate(listing)` to check required fields
5. Return only validated listings
6. Log summary statistics (total parsed, validated, rejected)

### `fetch_page(url)`

Fetch a single page using the injected HttpClient.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Target URL to fetch |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Response body as text |

**Raises:**

- `ScraperError` — wraps any HttpClient exception with scraper context
- `ScraperBlockedError` — when the response indicates blocking (e.g., 403 Forbidden)

**Behavior:**

1. Delegate to `self._http_client.get(url)`
2. Check the response status code
3. If blocked (403, 429), raise `ScraperBlockedError`
4. Return the response text body

### `parse_listings(content)`

**Abstract method.** Extract raw listing dicts from page content.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | `str` | Yes | Raw HTML or JSON response body |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `raw_listings` | `list[dict]` | Raw listing dicts as extracted from the source |

**Raises:**

- `ScraperParsingError` — when parsing fails or produces no usable data

**Behavior:**

Subclasses implement source-specific parsing logic. The base class calls this method but does not define its behavior. Each subclass is responsible for deciding how to extract listings from the content it receives.

### `normalize(raw)`

**Abstract method.** Map a single raw listing dict to the normalized Internship schema.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `raw` | `dict` | Yes | A single raw listing dict from `parse_listings()` |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `listing` | `dict` | Normalized dict matching the Internship model schema |

**Raises:**

- `ScraperParsingError` — when a required field cannot be extracted or mapped

**Behavior:**

Subclasses implement source-specific field mapping. The base class calls this method but does not define its behavior. The returned dict must conform to the [Normalized Data Contract](#normalized-data-contract) defined in section 9.

### `validate(listing)`

Validate that a normalized listing dict contains all required fields with non-empty values.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `listing` | `dict` | Yes | A normalized listing dict |

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | `bool` | `True` if all required fields are present and non-empty |

**Behavior:**

1. Check that all required fields exist in the dict
2. Check that required string fields are non-empty after stripping whitespace
3. Log a warning for each listing that fails validation, including the reason
4. Return `True` if valid, `False` if not

### `get_source_name()`

**Abstract method.** Return the source identifier for this scraper.

**Parameters:** None

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `source` | `str` | Source identifier (e.g., `"google"`, `"greenhouse"`, `"lever"`) |

**Behavior:**

Subclasses return a constant string identifying the source. This value is stored in the `source` column of the Internship model and used for traceability and filtering.

#### Source Naming Rules

Source names returned by `get_source_name()` must follow these rules:

| Rule | Description |
|------|-------------|
| **Lowercase** | Must be entirely lowercase |
| **Snake case** | Multi-word names must use `snake_case` |
| **Stable** | Must remain the same across versions — renaming breaks historical data |
| **No spaces** | Must never contain spaces or whitespace |
| **No special characters** | Must contain only lowercase letters, digits, and underscores |
| **Unique** | Must uniquely identify the scraper within the system |

**Examples:**

| Source Name | Scraper |
|-------------|---------|
| `"google"` | Google careers page scraper |
| `"greenhouse"` | Greenhouse ATS connector |
| `"lever"` | Lever ATS connector |
| `"smart_recruiters"` | SmartRecruiters ATS connector |
| `"amazon_jobs"` | Amazon jobs page scraper |
| `"zoho_careers"` | Zoho careers page scraper |

### `close()`

Release any resources held by the scraper.

**Parameters:** None

**Returns:** None

**Behavior:** The Base Scraper does not own the HttpClient and must not close it. This method exists as a hook for subclasses that acquire additional resources (e.g., Playwright browser instances). The default implementation is a no-op. Safe to call multiple times.

---

## 5. Constructor Design

The Base Scraper constructor accepts its dependencies explicitly. No dependency is resolved internally.

### Signature

```
BaseScraper(http_client, source_url=None)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `http_client` | `HttpClient` | Yes | Shared HTTP client instance for making requests |
| `source_url` | `str \| None` | No | Default URL for this scraper; can be overridden per call |

### Stored State

| Attribute | Description |
|-----------|-------------|
| `_http_client` | The injected HttpClient instance |
| `_source_url` | Optional default URL for convenience |

### Rules

- The constructor must **not** create its own HttpClient
- The constructor must **not** read configuration directly — configuration is resolved at a higher level and injected
- The constructor must **not** perform any I/O (no network requests, no file reads)

---

## 6. Dependency Injection

The Base Scraper follows the project's dependency injection pattern to keep scraping logic decoupled from transport infrastructure.

### Why Inject HttpClient

| Reason | Explanation |
|--------|-------------|
| **Testability** | Tests substitute a mock HttpClient without network access |
| **Reuse** | All scrapers share the same connection pool and configuration |
| **Single responsibility** | Scrapers parse; the HttpClient handles transport |
| **Consistency** | All HTTP behavior (timeouts, retries, logging) is centralized |

### Injection Pattern

```
Caller creates HttpClient
    ↓
Caller passes HttpClient to BaseScraper subclass
    ↓
BaseScraper stores reference
    ↓
BaseScraper delegates HTTP calls through stored reference
```

### Rules

- **Never import `http_client` at module level inside a scraper** — receive it via constructor
- **Never create a new HttpClient inside a scraper** — use the injected instance
- **Never call `httpx` directly** — always go through the injected HttpClient

---

## 7. Scraping Lifecycle

Every invocation of `scrape()` must follow the same lifecycle. No step may be skipped or reordered.

```
Caller
    ↓
scrape(url)
    ↓
fetch_page(url)
    ↓
parse_listings(content)
    ↓
normalize(raw)          ← repeated for each raw listing
    ↓
validate(listing)       ← repeated for each normalized listing
    ↓
Log Summary
    ↓
Return Validated Listings
```

| Stage | Method | Type | Description |
|-------|--------|------|-------------|
| **Fetch** | `fetch_page(url)` | Concrete | Retrieve page content via HttpClient |
| **Parse** | `parse_listings(content)` | Abstract | Extract raw listing dicts from content |
| **Normalize** | `normalize(raw)` | Abstract | Map raw fields to Internship schema |
| **Validate** | `validate(listing)` | Concrete | Reject incomplete listings |
| **Log** | (internal) | Concrete | Record statistics |
| **Return** | (internal) | Concrete | Return list of validated dicts |

### Method Ownership

Each method in the lifecycle has a clear owner. Subclasses must respect these boundaries.

| Method | Owner | Subclass May Override? |
|--------|-------|------------------------|
| `scrape()` | Framework | **No** — lifecycle orchestration is fixed |
| `fetch_page()` | Framework | **No** — HTTP delegation is fixed |
| `validate()` | Framework | **No** — validation rules are fixed |
| `parse_listings()` | Subclass | **Must implement** |
| `normalize()` | Subclass | **Must implement** |
| `get_source_name()` | Subclass | **Must implement** |
| `close()` | Subclass (optional) | **May override** |

Framework-owned methods define the scraping contract. Overriding them would break the lifecycle guarantees that the base class provides.

### Stage Boundaries

Each lifecycle stage has a clearly defined scope. Mixing responsibilities across stages leads to fragile, untestable scrapers.

| Stage | Must Do | Must Not Do |
|-------|---------|-------------|
| `parse_listings()` | Extract raw dicts from HTML or JSON; preserve original field names and values | Rename fields, apply defaults, strip whitespace, normalize data |
| `normalize()` | Map source fields to schema, apply defaults, strip whitespace, set `source` and `status` | Parse HTML or JSON, access raw response content, perform validation |
| `validate()` | Check presence and emptiness of required fields, return boolean result | Mutate data, coerce types, fix or repair invalid values |

**Parsing never normalizes. Normalization never parses. Validation never mutates.**

---

## 8. Request Lifecycle

Each call to `fetch_page()` follows a predictable request flow through the application stack:

```
BaseScraper.fetch_page(url)
    ↓
HttpClient.get(url)
    ↓
httpx.Client.get(url)
    ↓
Remote Website
    ↓
httpx.Response
    ↓
Status Code Check
    ↓
Return response.text
```

| Stage | Responsibility |
|-------|----------------|
| **fetch_page** | Delegates to HttpClient, checks for blocking status codes |
| **HttpClient.get** | Manages transport, timeouts, retries, logging |
| **httpx** | Low-level HTTP execution |
| **Status check** | Detect blocking (403, 429) and raise ScraperBlockedError |

The Base Scraper does not configure HTTP behavior. All transport settings (timeout, user agent, retries) are the HttpClient's responsibility.

### Retry Ownership

Retry logic belongs **exclusively** to the HttpClient. The Base Scraper has no role in retrying failed requests.

| Rule | Description |
|------|-------------|
| **BaseScraper never retries** | `fetch_page()` makes exactly one call to `HttpClient.get()` |
| **HttpClient owns retries** | The HttpClient has already exhausted its configured retry attempts before returning a response or raising an exception |
| **No backoff in scrapers** | BaseScraper must not import `time.sleep` or implement any backoff logic |
| **No retry configuration** | Retry count and backoff factor are HttpClient settings, not scraper settings |

When `fetch_page()` receives a response or exception from the HttpClient, that result is **final**. The scraper must accept it and proceed accordingly.

---

## 9. Normalization Rules

Every listing returned by `scrape()` must conform to the normalized Internship schema. Normalization maps source-specific field names and formats to a single consistent structure.

### Normalized Data Contract

The normalized schema is the **single source of truth** for listing data returned by any scraper. Every subclass must produce dicts that conform exactly to this contract.

| Rule | Description |
|------|-------------|
| **Exact fields only** | Every returned dict must contain exactly the fields defined below — no more, no fewer |
| **No unknown fields** | Fields not listed in the schema must not be included in the returned dict |
| **Uniform structure** | All scrapers return the same dict structure regardless of source |
| **Schema is authoritative** | When in doubt, the schema defined here takes precedence over source data |

### Normalized Fields

| Field | Type | Required | Default | Allowed Values | Description |
|-------|------|----------|---------|----------------|-------------|
| `company` | `str` | Yes | — | Any non-empty string | Company name as scraped from the source |
| `title` | `str` | Yes | — | Any non-empty string | Job or internship title |
| `url` | `str` | Yes | — | Any non-empty string | Canonical listing URL used for deduplication |
| `location` | `str \| None` | No | `None` | Any string or `None` | Geographic location or region |
| `employment_type` | `str` | Yes | `"internship"` | `"internship"`, `"full-time"`, `"part-time"`, `"contract"` | Employment classification |
| `work_mode` | `str` | Yes | `"unknown"` | `"remote"`, `"hybrid"`, `"on-site"`, `"unknown"` | Work arrangement |
| `source` | `str` | Yes | `get_source_name()` | Valid source name per [Source Naming Rules](#source-naming-rules) | Scraper or platform identifier |
| `status` | `str` | Yes | `"new"` | `"new"`, `"active"`, `"archived"` | Pipeline status |
| `posted_date` | `date \| None` | No | `None` | `datetime.date` or `None` | Date the listing was originally posted |
| `deadline` | `date \| None` | No | `None` | `datetime.date` or `None` | Application deadline |
| `stipend` | `str \| None` | No | `None` | Any string or `None` | Stipend or compensation text |
| `skills` | `str \| None` | No | `None` | Any string or `None` | Skills or requirements extracted from the listing |

### Normalization Rules

- **Strip whitespace** from all string fields
- **Normalize empty strings to `None`** for optional fields
- **Set `source`** to the value returned by `get_source_name()`
- **Set `status`** to `"new"` for all freshly scraped listings
- **Set `employment_type`** to `"internship"` when the source does not specify a type
- **Set `work_mode`** to `"unknown"` when the source does not specify a work arrangement
- **Preserve original URL casing** — URLs are case-sensitive for deduplication
- **Dates must be `date` objects**, not strings — subclasses parse date strings into `datetime.date`

### Field Mapping Responsibility

The base class defines the schema. Subclasses are responsible for mapping source-specific field names to the normalized schema. For example:

- Greenhouse uses `title`, `location.name`, `absolute_url`
- Lever uses `text`, `categories.location`, `hostedUrl`
- A company career page may use entirely custom HTML structures

Each subclass's `normalize()` method performs this mapping.

---

## 10. Validation

The Base Scraper validates every normalized listing before including it in the results. Validation enforces the required fields defined in the [Normalized Data Contract](#normalized-data-contract).

### Required Fields

The following fields must be present and non-empty in every listing:

| Field | Validation Rule |
|-------|----------------|
| `company` | Must be a non-empty string after stripping |
| `title` | Must be a non-empty string after stripping |
| `url` | Must be a non-empty string after stripping |
| `employment_type` | Must be a non-empty string after stripping |
| `work_mode` | Must be a non-empty string after stripping |
| `source` | Must be a non-empty string after stripping |
| `status` | Must be a non-empty string after stripping |

### Validation Behavior

- Listings that fail validation are **excluded** from the results
- A **WARNING log** is emitted for each rejected listing, including the field that failed
- Validation must **not raise exceptions** — it filters quietly and logs
- Validation must **not mutate data** — it is a read-only check
- The total count of rejected listings is included in the scrape summary log

### Validation Rules

- Required string fields must not be `None`, empty, or whitespace-only
- Optional fields are permitted to be `None` — their absence is not a validation failure
- No type coercion is performed during validation — data must already be normalized

---

## 11. Error Handling

The Base Scraper uses the centralized exception hierarchy from `app.core.exceptions`. It must never expose raw library errors to callers.

### Exception Usage

| Exception | When Raised |
|-----------|-------------|
| `ScraperError` | Base exception for any scraping failure not covered by a more specific type |
| `ScraperParsingError` | `parse_listings()` or `normalize()` fails to extract or map data |
| `ScraperBlockedError` | Target site returns 403, 429, or other blocking indicators |
| `HttpClientError` | Propagated from HttpClient — not caught by the base scraper |
| `HttpTimeoutError` | Propagated from HttpClient — not caught by the base scraper |
| `HttpConnectionError` | Propagated from HttpClient — not caught by the base scraper |

### Error Handling Rules

- **Never silently ignore exceptions** — log context and re-raise
- **Log meaningful context** before raising — include URL, source name, and error details
- **Let HTTP exceptions propagate** — the HttpClient has already logged and retried
- **Wrap parsing failures** in `ScraperParsingError` with the source URL and raw error
- **Detect blocking proactively** — check response status codes in `fetch_page()`
- **Individual listing failures should not abort the entire scrape** — if `normalize()` fails for one listing, log the error and continue processing remaining listings

### Partial Failure Strategy

When processing a page with multiple listings:

```
For each raw listing:
    Try normalize()
    If fails → log WARNING, skip this listing
    Try validate()
    If fails → log WARNING, skip this listing
    If passes → include in results
```

This allows a scraper to return partial results even when some listings are malformed. The summary log records how many listings were parsed, normalized, validated, and rejected. See [Scraping Lifecycle](#7-scraping-lifecycle) for the full stage sequence.

---

## 12. Logging

All Base Scraper logging must use the centralized logger from `app.core.logger`. No `print()` statements are permitted.

### What to Log

| Event | Fields |
|-------|--------|
| **Scrape start** | Source name, URL |
| **Fetch complete** | URL, response status, response time |
| **Parse complete** | Source name, count of raw listings found |
| **Normalization failure** | Source name, URL, raw listing snippet, error |
| **Validation failure** | Source name, listing URL or title, missing field |
| **Scrape complete** | Source name, total parsed, validated, rejected, total time |
| **Blocking detected** | Source name, URL, status code |

### Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Scrape start, fetch details, per-listing processing |
| `INFO` | Scrape complete summary with statistics |
| `WARNING` | Individual normalization or validation failures, retryable issues |
| `ERROR` | Complete scrape failure, blocking detected, unrecoverable errors |

### Correlation Fields

Every log line emitted during a scrape should include correlation fields to support traceability and debugging. The following fields should be included where available:

| Field | Description | Availability |
|-------|-------------|--------------|
| `source` | Scraper source name from `get_source_name()` | Now — include in every log line |
| `url` | Target URL being scraped | Now — include in every log line |
| `listing_count` | Number of validated listings returned | Now — include in summary log |
| `scrape_duration` | Total elapsed time for the scrape in milliseconds | Now — include in summary log |
| `request_id` | Unique correlation identifier per scrape invocation | Future — planned for tracing |

At minimum, every log line from a scrape must include `source` and `url` so that log output can be filtered by scraper and target.

### Security

- **Do not log full response bodies** — they may be large and contain sensitive data
- **Do not log authentication tokens or cookies** passed in request headers
- **Truncate long content** in debug logs to avoid log file bloat

---

## 13. Configuration

The Base Scraper reads configuration through the Config Loader (`app.core.config.settings`). No hardcoded values are permitted.

### Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `scraper.timeout` | `int` | `30` | Default HTTP request timeout in seconds |
| `scraper.user_agent` | `str` | `InternIntelBot/1.0` | Default User-Agent header |

These values are consumed by the HttpClient, not directly by the Base Scraper. The Base Scraper relies on the HttpClient to apply transport configuration.

### Configuration Rules

- The Base Scraper must **not** read YAML directly
- The Base Scraper must **not** hardcode timeouts, user agents, or retry limits
- Transport configuration is the HttpClient's responsibility
- The Base Scraper may read scraper-specific configuration (e.g., keyword filters) from `settings.get()` if needed in the future

### Currently Available Settings

The following keys already exist in `app/config/settings.yaml`:

- `scraper.timeout`
- `scraper.user_agent`

Additional scraper-specific keys may be added when the implementation requires them.

---

## 14. Extension Points

The Base Scraper provides a clear contract for subclasses to extend. Extension is achieved through abstract methods and optional hooks.

### Abstract Methods (Must Override)

| Method | Purpose |
|--------|---------|
| `parse_listings(content)` | Extract raw listing dicts from source-specific HTML or JSON |
| `normalize(raw)` | Map raw fields to the normalized Internship schema |
| `get_source_name()` | Return the source identifier string |

### Optional Hooks

| Method | Default | Purpose |
|--------|---------|---------|
| `close()` | No-op | Release additional resources (e.g., Playwright browsers) |

### Subclass Contract

Every subclass must:

1. Call `super().__init__(http_client)` in its constructor
2. Implement all three abstract methods
3. Return dicts conforming to the [Normalized Data Contract](#normalized-data-contract) from `normalize()`
4. Return a stable, lowercase source name from `get_source_name()` following the [Source Naming Rules](#source-naming-rules)
5. Not override framework-owned lifecycle methods — see [Method Ownership](#method-ownership)

### Example Subclass Patterns

**ATS Connector (e.g., Greenhouse):**

```
GreenhouseScraper extends BaseScraper
    parse_listings() → parse JSON API response
    normalize() → map Greenhouse fields to Internship schema
    get_source_name() → "greenhouse"
```

**Company Scraper (e.g., Google):**

```
GoogleScraper extends BaseScraper
    parse_listings() → parse HTML with BeautifulSoup
    normalize() → map HTML elements to Internship schema
    get_source_name() → "google"
```

---

## 15. Sequence Diagram

The following sequence shows how a scrape request flows through the system:

```
Company Scraper / ATS Connector
    │
    ▼
BaseScraper.scrape(url)
    │
    ▼
BaseScraper.fetch_page(url)
    │
    ▼
HttpClient.get(url)
    │
    ▼
Remote Website / API
    │
    ▼
Response (HTML / JSON)
    │
    ▼
Subclass.parse_listings(content)
    │
    ▼
Raw Listing Dicts
    │
    ▼
Subclass.normalize(raw)        ← per listing
    │
    ▼
BaseScraper.validate(listing)  ← per listing
    │
    ▼
Validated Listings
    │
    ▼
Caller (Service Layer)
```

The caller (typically a service) initiates the scrape. The Base Scraper orchestrates the lifecycle, delegates parsing to the subclass, validates results, and returns normalized data. The caller remains responsible for persistence, deduplication, and notification.

---

## 16. Testing Strategy

The Base Scraper must include comprehensive unit tests. All HTTP calls must be **mocked** — tests must not depend on live external websites.

### Planned Test Cases

| Test Case | Description |
|-----------|-------------|
| **Successful scrape** | Verify full lifecycle returns validated listings |
| **Empty results** | Verify scraper returns empty list when no listings found |
| **Partial failure** | Verify scraper continues when some listings fail normalization |
| **Validation rejection** | Verify listings missing required fields are excluded |
| **Validation logging** | Verify WARNING log for each rejected listing |
| **Fetch blocked** | Verify `ScraperBlockedError` on 403 and 429 responses |
| **Fetch failure** | Verify HTTP exceptions propagate correctly |
| **Parse failure** | Verify `ScraperParsingError` when parsing produces no results |
| **Normalization failure** | Verify individual normalize failures don't abort scrape |
| **Source name** | Verify `get_source_name()` returns expected identifier |
| **Dependency injection** | Verify HttpClient mock is used, not a real client |
| **Scrape summary log** | Verify INFO log with parsed/validated/rejected counts |
| **Empty URL** | Verify error behavior when URL is empty or None |
| **Default field values** | Verify `status`, `employment_type`, `work_mode` defaults |

### Lifecycle Verification Tests

The following additional tests verify lifecycle correctness:

| Test Case | Description |
|-----------|-------------|
| **Lifecycle order** | Verify fetch → parse → normalize → validate executes in strict sequence |
| **No skipped stages** | Verify parse is not called without fetch; validate is not called without normalize |
| **DI behavior** | Verify scraper calls the injected HttpClient, not a default or internally created instance |
| **Partial failure counts** | Verify summary log accurately reflects parsed, validated, and rejected counts |
| **Logging levels** | Verify DEBUG on start, INFO on success, WARNING on individual failures, ERROR on blocking |

### Testing Approach

- Create a **concrete test subclass** that implements the abstract methods with predictable test data
- Mock the **HttpClient** to return controlled responses
- Verify **logging** using mock logger assertions
- Test the **lifecycle order** — fetch → parse → normalize → validate
- Verify **no database access** occurs during any test

Tests should use dependency injection to substitute the HttpClient. No test may make real outbound HTTP requests to external services.

---

## 17. Design Principles

The Base Scraper must adhere to the following design principles, consistent with the InternIntel engineering specification:

| Principle | Application |
|-----------|-------------|
| **Single responsibility** | Orchestrate scraping lifecycle only — no persistence, no notification |
| **Open/closed principle** | Open for extension via abstract methods; closed for modification of the lifecycle |
| **Dependency injection** | HttpClient received via constructor, not imported or created internally |
| **Composition over inheritance** | HttpClient is composed in, not inherited from. Inheritance is used only for the abstract contract. |
| **Framework independent** | No coupling to FastAPI, Flask, or web frameworks |
| **Testable** | Abstract methods and DI enable full mocking in unit tests |
| **Configuration through Config Loader** | No hardcoded values; all settings from `settings.get()` |
| **Centralized logging** | All log output through `app.core.logger` |
| **Explicit behavior** | Lifecycle stages are predictable and documented |

---

## 18. Design Constraints

The Base Scraper implementation must respect the following hard constraints:

- **No database access** — no imports from `app.database` or `app.models`
- **No notification logic** — no imports from notification modules
- **No direct httpx usage** — all HTTP through the injected HttpClient
- **No company-specific parsing** — source-specific logic belongs in subclasses
- **No data persistence** — returning data is the scraper's final act
- **No deduplication** — URL uniqueness checks belong in the service layer
- **No retry logic** — retry handling belongs exclusively to the HttpClient
- **No global mutable state** — all state is instance-scoped
- **No `print()` statements** — use the centralized logger

These constraints align with the [Non-Responsibilities](#3-non-responsibilities) defined in this specification and the dependency rules in `AI_CONTEXT.md`.

---

## 19. Thread Safety

The Base Scraper is designed for use within the application's supported execution model.

| Rule | Description |
|------|-------------|
| **Lightweight instances** | BaseScraper instances are inexpensive to create and should not accumulate heavy state |
| **One instance per workflow** | One scraper instance should normally serve one scrape workflow (one URL or one scrape run) |
| **Shared HttpClient** | The injected HttpClient is designed to be shared across scraper instances and reused across scrape runs |
| **No mutable shared state** | Scrapers must not maintain mutable state that is shared across calls or instances |
| **Concurrent scraping** | If future concurrent scraping is needed, each task should create its own scraper instance sharing the same HttpClient |

Scrapers are stateless processing pipelines. They receive an HttpClient, execute a lifecycle, return results, and may be discarded. The HttpClient provides connection reuse; the scraper provides parsing and normalization logic.

---

## 20. Future Extensions

The initial implementation covers synchronous GET-based scraping. The following capabilities are planned for future versions:

| Extension | Description |
|-----------|-------------|
| **Pagination** | Automatic multi-page scraping with configurable page limits |
| **Async scraping** | Non-blocking scraping for concurrent source processing |
| **Playwright fallback** | Browser-based scraping for JavaScript-rendered pages |
| **Rate limiting** | Per-host request throttling to avoid blocking |
| **Keyword filtering** | Filter listings by configured include/exclude keyword lists |
| **Caching** | Cache responses for recently visited pages |
| **POST-based scraping** | Support for sources that require POST requests (e.g., search forms) |
| **robots.txt awareness** | Respect `robots.txt` directives before scraping a host |
| **Incremental scraping** | Track last-seen timestamps to scrape only new or updated listings |
| **Checkpoint/resume** | Save progress during long scrape runs and resume on failure |
| **Metrics collection** | Emit structured scraping metrics for monitoring dashboards |
| **Scraper health reporting** | Report scraper status, success rate, and error trends over time |

Future extensions must not break the existing public API. New behavior should be opt-in through configuration or additional methods. This is a **design note only** — none of the extensions above are implemented in this specification.

---

## 21. Quality Gate

Before the Base Scraper implementation is considered complete, it must satisfy every item in the [Quality Gate](../AI_CONTEXT.md#quality-gate) defined in `AI_CONTEXT.md`, including:

- Black formatting
- Ruff linting
- Pytest coverage for lifecycle, normalization, validation, and error handling
- Type hints and Google-style docstrings
- Architecture and dependency rule compliance
- No database imports
- No notification imports
- HttpClient used exclusively through dependency injection

---

*Last updated: July 2026*
