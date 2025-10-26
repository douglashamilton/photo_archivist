## TDD Template

### Bottom line

* One paragraph: exactly what will be shipped in the MVP and the chosen stack, highlighting the primary capabilities the architecture must support.

### Architecture Overview

* **Stack:** framework, key libs, test runner, formatter/linter.
* **App structure:** SPA/SSR/API-only/hybrid; state management approach if UI.
* **Data storage:** what and why; migrations (if any).
* **Auth:** method or “none”.
* **Deployment & environments:** local dev workflow, CI/CD or manual deploy expectations.

### Tech Stack Decisions

* Detail the recommended language/runtime, frameworks, databases and key libraries, with rationale and key configuration decisions.

### Interfaces

* Detail the necessary API contracts, module contracts and event / telemetry contracts (as applicable).
* Include inputs/outputs, validation rules, and error handling strategy.

### Domain model

* Entities with fields/types, relationships, invariants, validations.
* Always include **IDs** and **timestamps** where relevant.
* Note persistence choices (e.g., tables, collections) and indexing considerations.

### Data flow & interfaces

* **Inbound:** UI/CLI/event → handler → service → storage.
* **Outbound:** UI rendering / CLI output / API response.
* Define concrete contracts for each interface:

```http
POST /api/{{resource}}   // if applicable to the MVP scope
Request: { ...validated schema... }
Response: { data|error }  // include error shape
Limits: {{rate limits}} | Auth: {{scheme or none}}
```

### Tooling & workflows

* **Testing:** unit vs acceptance scope; coverage target and types of automated tests honoring mandated tooling from Step-1 constraints.
* **Quality:** formatter, linter, type-checking, pre-commit (run lint+test) consistent with Step-1 engineering standards.
* **Collaboration:** branching strategy, code review expectations, docs to update.

### Risks & mitigations

* List 3–5 risks. Provide a concrete mitigation for each.
* Flag any design decisions that require validation with stakeholders.

### Assumptions

* Explicit defaults where info was missing (platform, stack, data volumes, auth, etc.).

### Open questions

* Numbered list with resolution plan (owner/test/link). Proceed with **Assumptions** if blocks remain.

### Iteration readiness checklist

* Bullet list confirming the design provides everything required: bounded MVP scope, clear contracts, defined dependencies, and any pre-work needed before implementation.