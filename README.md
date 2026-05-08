# MCX Disclosure Schema

**Version 0.1.0 · Community Draft · Apache License 2.0**

An open JSON Schema for AI vendor compliance disclosures.

This repository defines a machine-readable format for documenting AI models against the EU AI Act, the NIST AI Risk Management Framework, and ISO/IEC 42001. It is the *format* — not a platform. Vendors can use it to structure their own model documentation, build internal tooling around it, or publish to any registry that consumes it.

The schema is independently useful. You can adopt it without using any specific service or platform.

---

## What this repository contains

- **`schemas/mcx-disclosure-v0.1.schema.json`** — the JSON Schema specification for a disclosure record (Draft 2020-12)
- **`schemas/events/mcx-event-v0.1.schema.json`** — schema for change events that registries built on this format can emit (optional)
- **`schemas/events/types.md`** — documentation of event types and their payloads
- **`examples/`** — fully populated example disclosure records
- **`scripts/validate.py`** — validator that confirms records conform to the schema
- **`LICENSE`** — Apache License 2.0

## What it covers

A disclosure record describes a single AI model or system across:

- Publisher identification, EU AI Act role, and contact information
- EU AI Act risk classification (`risk_class` enum: `prohibited`, `high_risk`, `limited_risk`, `minimal`, `gpai`, `gpai_systemic`)
- Intended purpose, intended users, and out-of-scope uses
- Technical architecture and delivery form
- Training data sources, scope, and known gaps
- Performance, bias, robustness, and cybersecurity
- Human oversight and automation level
- Instructions-for-use fields: explainability capabilities, group-specific performance, input data specifications, output interpretation guidance, predetermined changes, computational requirements, expected lifetime, maintenance measures (Article 13(3))
- Post-market monitoring, logging, and incidents
- Conformity assessment outcomes and CE marking status
- GPAI-specific fields (training compute, copyright policy, training data summary)
- Lifecycle metadata, version history, and a named human attestation

High-risk and GPAI classifications add conditional required fields. The schema enforces these rules using standard JSON Schema validators.

## What it doesn't cover

This is a disclosure schema. It is not:

- **A certification.** Validators confirm a record's *structure*, not the *truth* of its content. Attestation accountability rests with the vendor.
- **A Notified Body certificate.** Conformity assessments under Article 43 are performed by accredited bodies; the schema records the outcome (`conformity_assessment_type`, `ce_marking_status`) where relevant but does not produce one.
- **Legal advice.** Field mappings to regulatory frameworks are best-effort community work, not legal opinions.
- **A platform or service.** No hosted registry, no API, no account system. Just a format.
- **A conformity assessment process.** Notified Bodies perform assessments under EU AI Act Article 43; the schema records outcomes, it does not produce them.
- **An internal governance workflow.** This describes models for external disclosure. It does not run a vendor's risk management or QMS.

## Quick start

Install a JSON Schema validator. Add the `[format]` extras so that `uri`, `email`, `uuid`, `date`, and `date-time` constraints are enforced rather than treated as advisory annotations:

```bash
pip install "jsonschema[format]"
```

Validate a record:

```python
import json
from jsonschema import Draft202012Validator, FormatChecker

schema = json.load(open("schemas/mcx-disclosure-v0.1.schema.json"))
record = json.load(open("my-disclosure.json"))

validator = Draft202012Validator(schema, format_checker=FormatChecker())
errors = list(validator.iter_errors(record))
if not errors:
    print("Valid disclosure record")
else:
    for err in errors:
        print(f"- {list(err.path)}: {err.message}")
```

Or run the included script across all examples:

```bash
python3 scripts/validate.py
```

## Browse the examples

- [`examples/high-risk-credit-scoring.json`](examples/high-risk-credit-scoring.json) — fully populated high-risk disclosure under Annex III §5(b). Non-EU provider with `eu_authorised_representative` populated under Article 22.
- [`examples/gpai-foundation-model.json`](examples/gpai-foundation-model.json) — open-weights GPAI disclosure aligned to Article 53.
- [`examples/gpai-systemic-foundation-model.json`](examples/gpai-systemic-foundation-model.json) — systemic-risk GPAI disclosure under Article 51, with `training_compute_summary`, `systemic_risk_flag`, and a populated incidents array demonstrating the conditional rules and the incident object shape.

## The Core profile

A valid disclosure record always includes 21 top-level fields:

| # | Field | Purpose |
|---|---|---|
| 1 | `schema_version` | Which schema version this record uses |
| 2 | `disclosure_id` | Globally unique ID for this record |
| 3 | `model_id` | Provider-controlled stable model identifier |
| 4 | `model_name` | Human-readable model name |
| 5 | `version` | Released version of the model |
| 6 | `publisher` | Publishing entity, EU AI Act role, contact, EU representative |
| 7 | `risk_class` | EU AI Act classification |
| 8 | `model_description` | What the system does |
| 9 | `intended_purpose` | Article 3(12) intended purpose |
| 10 | `intended_users` | Who is supposed to operate it |
| 11 | `out_of_scope_use` | Explicit unsupported uses |
| 12 | `market_delivery_form` | SaaS, on-prem, weights, etc. |
| 13 | `training_data_description` | What was the model trained on |
| 14 | `training_data_source` | Source categories |
| 15 | `evaluation_summary` | How performance was measured |
| 16 | `known_limitations` | Failure modes the buyer needs to know |
| 17 | `automation_level` | Human oversight classification |
| 18 | `lifecycle_status` | Development / production / deprecated |
| 19 | `published_at` | When this record was first published |
| 20 | `last_updated_at` | Most recent update timestamp |
| 21 | `attestation` | Named human accountable for accuracy |

When `risk_class = high_risk`, fifteen additional fields become required (foreseeable misuse, bias assessment, human oversight measures, monitoring plan, computational requirements, expected lifetime, maintenance measures, etc.). When `risk_class = gpai` or `gpai_systemic`, four more become required (training data summary URL, copyright policy, GPAI flag, technical documentation bundle). When `risk_class = gpai_systemic`, four further fields become required (systemic risk flag, training compute summary, robustness testing, cybersecurity controls).

These conditional rules are encoded in the schema using `if`/`then`/`allOf` and enforced automatically by any standard JSON Schema validator.

## Identity and attestation

Every disclosure record carries a mandatory `attestation` block: a named individual within the publishing organisation who is accountable for the accuracy of the disclosure. The `attestation_status` field distinguishes between `self_attested`, `third_party_verified`, and `notified_body`.

Cryptographic signing of disclosure records is planned for a future schema version (see roadmap). v0.1 relies on the named attestation block for accountability.

The schema does not certify the truth of disclosure content. Validators confirm the structural integrity of a record — that all required fields are present, that types and enums conform, and that conditional rules are satisfied. Truth claims rest with the named attestor.

## Versioning

From v1.0 onwards, the schema follows [Semantic Versioning](https://semver.org). Pre-1.0 releases (v0.x) are explicitly community drafts and may include breaking changes between minor versions; the `schema_version` field tells consumers which version a record targets. From v1.0, within a major version, fields may be added or made optional, but never removed or made stricter. Major version bumps are reserved for breaking changes and are announced with a migration period.

Records always declare which schema version they target via the `schema_version` field, allowing systems built on the schema to support multiple concurrent versions during transitions. Each schema version pins `schema_version` to a `const`, so a v0.1.0 record only validates against this schema if `schema_version` is exactly `"0.1.0"`.

## Roadmap

- **v0.1 (this release)** — community draft. JSON Schema, examples, event envelope.
- **v0.2** — incorporate design partner feedback. Interoperability blocks (APP, C2PA, MLflow, DCAT-AP). Expanded NIST AI RMF and ISO/IEC 42001 mappings. Cryptographic signature specification.
- **v0.3** — domain-specific extension profiles (financial services, healthcare).
- **v1.0** — first stable release. Versioning guarantees activate.

## Contributing

We particularly welcome contributions on:

- EU AI Act citation accuracy
- NIST AI RMF and ISO/IEC 42001 mapping completeness
- Field naming and schema ergonomics
- Example records covering more risk classes and verticals
- Translations of field descriptions

## Disclaimer

This schema is a community draft published for review and adoption. It is provided "as is" without warranty of any kind. Field references to the EU AI Act, NIST AI RMF, ISO/IEC 42001, and other frameworks are best-effort interpretations intended to aid practitioners. They are not legal opinions. Organisations using this schema for regulatory compliance should validate field mappings with qualified counsel and competent authorities.

## Licence

[Apache License 2.0](LICENSE). You may use, modify, and redistribute this schema commercially or non-commercially, with attribution.

## Contact

- **Bugs and contributions**: GitHub Issues on this repository
- **Questions and discussion**: GitHub Discussions on this repository
