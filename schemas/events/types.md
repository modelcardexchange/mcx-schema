# MCX Webhook Event Types

Human-readable companion to `mcx-event-v0.1.schema.json`. The JSON Schema is the authoritative source for shape; this document explains intent, trigger conditions, and payload semantics.

This document describes the events the registry **actually delivers** to webhook endpoints in v0.1 — the shape the delivery worker (`worker/deliver.py`) sends, not an aspirational design. Designed-but-not-yet-emitted types are listed under [Planned event types](#planned-event-types).

This document is part of the MCX schema package, subject to the same Apache 2.0 licence and the same disclaimers in the main README. It is not legal advice.

---

## The envelope

Every delivered event uses a common JSON envelope:

| Field | Type | Required | Description |
|---|---|---|---|
| `event_id` | uuid | yes | Unique per event. Idempotency key — dedupe on this. Also the `X-MCX-Event-ID` header. |
| `event_type` | string | yes | One of the types below. Also the `X-MCX-Event-Type` header. |
| `occurred_at` | date-time | yes | ISO 8601 timestamp at the source registry. |
| `disclosure_slug` | string | yes* | Public slug of the disclosure (e.g. `dsc_ZDK3527R`). Present on every disclosure event. |
| `model_id` | string | yes* | Stable provider-controlled model identifier. Present on every disclosure event. |
| `payload` | object | yes | Type-specific payload (see each type below). |

\* `disclosure_slug` and `model_id` are present on all currently-delivered events (they are all disclosure-aggregate events). They let a subscriber attribute the event to a model **without** parsing the type-specific payload.

> **Note:** only `event_id`, `event_type`, `occurred_at`, and `payload` are guaranteed for every conceivable event; `disclosure_slug` / `model_id` are added for disclosure-aggregate events, which is every type delivered in v0.1.

Delivery headers (see the API Surface "Webhook Signature Verification" section):

- `X-MCX-Event-ID` — mirrors `event_id`
- `X-MCX-Event-Type` — mirrors `event_type`
- `X-MCX-Timestamp` — Unix seconds the signature was computed
- `X-MCX-Signature` — `sha256=<hex>` HMAC-SHA256 over `{timestamp}.{body}`

**Subscribers must dedupe on `event_id`** — the same logical state change may be redelivered (retries).

---

## `disclosure.published`

**Fires when:** a disclosure record for a model is published to the registry for the first time.

**Payload:** the shared *record snapshot* (see below).

---

## `disclosure.updated`

**Fires when:** an existing disclosure record is edited and a new immutable version is written.

**Payload:** the shared *record snapshot* (see below).

> **No diff in the payload.** The payload is a snapshot of the disclosure's *current* state — it does not contain old/new value pairs or a list of changed fields. To compute what changed between two versions, call:
> ```
> GET /api/v1/disclosures/{disclosure_slug}/versions/diff?from={from_version_slug}&to={to_version_slug}
> ```
> Use `GET /api/v1/disclosures/{disclosure_slug}/versions` to obtain the version slugs (newest first); the prior version's slug is the `from`, the current event's `version_slug` is the `to`.

---

## `subscription.snapshot`

**Fires when:** a subscriber newly subscribes to a disclosure — a one-shot snapshot is delivered to that subscriber so they start with current state rather than waiting for the next change. Targeted: only the subscribing org's endpoint receives it.

**Payload:** the shared *record snapshot* (see below).

---

### Shared record snapshot payload

Used by `disclosure.published`, `disclosure.updated`, and `subscription.snapshot` (built by `build_record_payload` in `api/services/disclosure_service.py`):

| Field | Type | Required | Description |
|---|---|---|---|
| `disclosure_slug` | string | yes | Public slug of the disclosure. |
| `version_slug` | string | yes | Slug of the specific immutable version this event refers to. |
| `version_number` | integer | yes | Monotonic version number (1 = first publish). |
| `model_id` | string | yes | Stable model identifier. |
| `risk_class` | enum \| null | no | `prohibited` \| `high_risk` \| `limited_risk` \| `minimal` \| `gpai` \| `gpai_systemic`. |
| `lifecycle_status` | string \| null | no | e.g. `production`. |
| `publisher_role` | string \| null | no | e.g. `provider`, `deployer`. |

**Example body:**
```json
{
  "event_id": "6455475a-65d4-424b-911f-aa5fd31bb262",
  "event_type": "disclosure.updated",
  "occurred_at": "2026-05-28T11:45:03.036405+00:00",
  "disclosure_slug": "dsc_ZDK3527R",
  "model_id": "meridian-credit-risk",
  "payload": {
    "disclosure_slug": "dsc_ZDK3527R",
    "version_slug": "ver_6FW28XGS",
    "version_number": 4,
    "model_id": "meridian-credit-risk",
    "risk_class": "high_risk",
    "lifecycle_status": "production",
    "publisher_role": "provider"
  }
}
```

---

## `incident.reported`

**Fires when:** a new incident is added to the disclosure record's `incidents` array (severity `low` or `medium`). Aligned to EU AI Act Article 73 reporting; the registry propagates the *fact* of the report to subscribed buyers — it does not interpose between the vendor and the relevant market surveillance authority.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `incident_id` | string | yes | Vendor-controlled incident identifier (matches `incidents[].incident_id`). |
| `severity` | enum | yes | `low`, `medium`, `high`, or `serious`. |
| `summary` | string | no | Short human description (the incident's description). |

**Example body:**
```json
{
  "event_id": "c4997db7-9ac1-4927-aae2-61f5c1a3a3b2",
  "event_type": "incident.reported",
  "occurred_at": "2026-05-28T12:47:22.196854+00:00",
  "disclosure_slug": "dsc_ZDK3527R",
  "model_id": "meridian-credit-risk",
  "payload": {
    "incident_id": "inc_N422EA7R",
    "severity": "low",
    "summary": "someone fell over"
  }
}
```

---

## `incident.critical_alert`

**Fires when:** a new incident is added with severity `high` or `serious`. Identical payload shape to `incident.reported`; the distinct event type lets subscribers route urgent incidents differently (e.g. page on-call vs. periodic digest).

**Payload:** same as `incident.reported`.

---

## `incident.updated`

**Fires when:** an existing incident's status changes (e.g. `open` → `mitigating` → `resolved`).

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `incident_id` | string | yes | The incident identifier. |
| `incident_index` | integer | yes | Index of the incident within the disclosure's `incidents` array. |
| `severity` | enum | yes | `low`, `medium`, `high`, or `serious`. |
| `status` | string | yes | New incident status. |

**Example body:**
```json
{
  "event_id": "c4997db7-9ac1-4927-aae2-61f5c1a3a3b3",
  "event_type": "incident.updated",
  "occurred_at": "2026-05-28T12:47:22.196854+00:00",
  "disclosure_slug": "dsc_ZDK3527R",
  "model_id": "meridian-credit-risk",
  "payload": {
    "incident_id": "inc_HJ873BWW",
    "incident_index": 0,
    "severity": "low",
    "status": "mitigating"
  }
}
```

---

## Planned event types

These are part of the designed event vocabulary but the registry does **not** emit them as webhook deliveries in v0.1. Do not build hard dependencies on receiving them yet. When implemented they will reuse the common envelope.

| Type | Status | Designed intent |
|---|---|---|
| `disclosure.expired` | planned | Disclosure passed its review-by date without update. |
| `risk_class.changed` | planned | A model's `risk_class` changed. Designed payload `{from_class, to_class, rationale}`. |
| `conformity.changed` | planned | Conformity assessment or CE marking status changed. |
| `training_data.changed` | planned | Training data sources, scope, or cutoff materially updated. |
| `access.granted` | emitted but not delivered | Today emitted as an `access`-category event; it does **not** fan out to webhooks (only `business`-category, disclosure-aggregate events do). |

---

## Common subscriber guidance

- **Idempotency.** Always dedupe on `event_id`. Retries will redeliver the same `event_id`.
- **Attribution.** Use the envelope `disclosure_slug` + `model_id` to attribute any event to a record/model without parsing the payload.
- **Snapshots, not diffs.** `disclosure.*` payloads are current-state snapshots. For field-level change detail, call the versions/diff endpoint.
- **Recovery.** A subscriber that has missed events should re-fetch the current record via `GET /api/v1/disclosures/{disclosure_slug}`, not replay events. Events are propagation hints; the disclosure record is the source of truth.
