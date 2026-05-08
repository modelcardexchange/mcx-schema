# MCX Webhook Event Types

Human-readable companion to `mcx-event-v0.1.schema.json`. The JSON Schema is the authoritative source for shape; this document explains intent, trigger conditions, and payload semantics.

Every event uses the common envelope (`event_id`, `type`, `occurred_at`, `schema_version`, `disclosure_id`, `model_id`, `publisher_name`, optional `disclosure_url`, plus the type-specific `payload`). Subscribers must dedupe on `event_id` — the same logical state change may be redelivered.

This document is part of the MCX schema package, subject to the same Apache 2.0 licence and the same disclaimers in the main README. It is not legal advice.

---

## `disclosure.published`

**Fires when:** a disclosure record for a model is published to the registry for the first time.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `version` | string | yes | The model version this disclosure documents (e.g. `1.4.0`). |

**Example payload:**
```json
{
  "version": "1.4.0"
}
```

**Notes for subscribers:** treat as a brand-new model arrival in the buyer's vendor inventory. There is no `from_version`; this is the first state.

---

## `disclosure.updated`

**Fires when:** any field in an existing disclosure record changes. The version of the *disclosure record* itself is incremented; the underlying *model* version may or may not have changed (use `risk_class.changed`, `training_data.changed`, etc. for substantive triggers).

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `from_version` | string | yes | Disclosure record version before the change. |
| `to_version` | string | yes | Disclosure record version after the change. |
| `fields_changed` | string[] | yes | Names of top-level fields that changed. May be empty if metadata-only update. |
| `summary` | string | no | Free-text human summary. Sourced from the vendor's `update_changelog` entry if available. |

**Example payload:**
```json
{
  "from_version": "1.3.2",
  "to_version": "1.4.0",
  "fields_changed": ["evaluation_metrics", "accuracy_specification"],
  "summary": "Recalibration after Q1 monitoring detected drift."
}
```

**Notes for subscribers:** use `fields_changed` to drive selective re-review in GRC tools. A `disclosure.updated` event with only metadata changes (e.g. typo fix in `model_summary`) may be filtered out by buyer-side rules.

---

## `disclosure.expired`

**Fires when:** a disclosure record passes its review-by date without an update. The exact review cadence is registry policy; default in v0.1 is 12 months from `last_updated_at`.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `last_updated_at` | date-time | yes | The disclosure's `last_updated_at` value at the moment of expiry. |
| `expired_at` | date-time | yes | Timestamp at which the registry marked the record expired. |

**Example payload:**
```json
{
  "last_updated_at": "2025-04-15T10:00:00Z",
  "expired_at": "2026-04-15T10:00:00Z"
}
```

**Notes for subscribers:** treat as a procurement signal. The model may still be in production; the disclosure has gone stale. Trigger a vendor outreach.

---

## `risk_class.changed`

**Fires when:** a model's EU AI Act `risk_class` value changes. Material event — buyers may have classification-driven controls that need to fire.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `from_class` | enum | yes | Previous `risk_class` value. |
| `to_class` | enum | yes | New `risk_class` value. |
| `rationale` | string | no | Vendor-provided explanation. Should be drawn from `classification_rationale`. |

Enum values for `from_class` and `to_class`: `prohibited`, `high_risk`, `limited_risk`, `minimal`, `gpai`, `gpai_systemic`.

**Example payload:**
```json
{
  "from_class": "limited_risk",
  "to_class": "high_risk",
  "rationale": "Use case extended into Annex III §5(b) creditworthiness scope."
}
```

**Notes for subscribers:** treat any move *into* `high_risk`, `gpai_systemic`, or `prohibited` as a material event. Conditional required fields will also have changed (`bias_assessment`, `monitoring_plan`, etc.) — pair this with a `disclosure.updated` event in the same logical operation.

---

## `conformity.changed`

**Fires when:** the `conformity_assessment_type` or `ce_marking_status` field changes. Distinct from `risk_class.changed` — a model may keep its risk class but move from `ce_marking_status: pending` to `affixed`.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `from_status` | string \| null | no | Previous status; null if not previously set. |
| `to_status` | string \| null | no | New status. |
| `ce_marking_status` | string \| null | no | Current CE marking status (mirrors disclosure field). |

**Example payload:**
```json
{
  "from_status": "pending",
  "to_status": "affixed",
  "ce_marking_status": "affixed"
}
```

**Notes for subscribers:** procurement teams that gate vendor approval on CE-marking status should subscribe to this event specifically.

---

## `training_data.changed`

**Fires when:** training data sources, scope, or cutoff are materially updated. Driven by changes to `training_data_description`, `training_data_source`, or `training_time_period`.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `summary` | string | no | Vendor-provided change summary. |
| `new_cutoff_date` | date \| null | no | Updated training cutoff if changed. |

**Example payload:**
```json
{
  "summary": "Added Q1 2026 transactional data; cutoff extended.",
  "new_cutoff_date": "2026-03-31"
}
```

**Notes for subscribers:** for buyers with data-lineage compliance obligations (GDPR, sector-specific record-of-processing), this event triggers downstream artefact regeneration.

---

## `incident.reported`

**Fires when:** a serious incident is added to the disclosure record's `incidents` array. Aligned to EU AI Act Article 73 reporting; the registry propagates the *fact* of the report to subscribed buyers — it does not interpose between the vendor and the relevant market surveillance authority.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `incident_id` | string | yes | Vendor-controlled incident identifier. Matches `incidents[].incident_id` in the disclosure. |
| `severity` | enum | yes | `low`, `medium`, `high`, or `serious`. |
| `summary` | string | no | Short human description. |

**Example payload:**
```json
{
  "incident_id": "INC-2026-014",
  "severity": "high",
  "summary": "Calibration drift on retail credit cohort exceeded threshold; model held."
}
```

**Notes for subscribers:** `serious` severity should trigger immediate review per the buyer's incident response process. `low`/`medium` may aggregate into a periodic digest.

---

## `access.granted`

**Fires when:** a vendor grants a buyer access to a `record_visibility = "verified_buyers_only"` or `"private"` disclosure record. Governance event, not a content event.

**Payload:**

| Field | Type | Required | Description |
|---|---|---|---|
| `buyer_organisation_id` | string | no | The buyer organisation being granted access. |

**Example payload:**
```json
{
  "buyer_organisation_id": "mcx-org-bigbank-002"
}
```

**Notes for subscribers:** this event is delivered to the *granted* buyer organisation. It is a signal to begin pulling the disclosure record via the registry API; the event itself does not carry the disclosure body.

---

## Common subscriber guidance

- **Idempotency.** Always dedupe on `event_id`. Retries will redeliver the same `event_id`.
- **Ordering.** Events are best-effort ordered by `occurred_at` but are not guaranteed strictly sequential. Use `disclosure_id` + `to_version` (where applicable) as the secondary ordering key.
- **Recovery.** A subscriber that has missed events should re-fetch the current full disclosure record via the registry API, not replay events. Events are propagation hints; the disclosure record is the source of truth.
- **Schema versioning.** The `schema_version` field on the envelope identifies the MCX schema version of the disclosure being referenced. Multi-version-aware subscribers should branch on this.
