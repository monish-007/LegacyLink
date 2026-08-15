# LegacyLink demo script (90 seconds)

## One-line pitch

LegacyLink uses Codex to turn undocumented SOAP responses into reviewable, typed
REST API drafts—with validation evidence and human approval before deployment.

## 0:00–0:15 — the problem

Show `legacy_server.py` and the raw SOAP response.

> "A team needs data from a legacy SOAP service. The payload is deeply nested, its
> schema is undocumented, and its authentication header must never leak into a new
> API. Today, an engineer manually reverse-engineers this before an integration can
> even start."

## 0:15–0:35 — Codex workflow

Run `python orchestrator.py`; show the isolated worktree and Codex prompt.

> "LegacyLink captures the contract and gives Codex a constrained task in an
> isolated Git worktree: build strict models, negative tests, an OpenAPI API, and a
> dashboard. It produces a reviewable draft—not an unchecked production deployment."

## 0:35–0:55 — working result

Open `/dashboard`; click **Execute GET /v1/customer-data**, then **View validation
evidence**.

> "The generated endpoint is strongly typed—money is decimal, dates are dates, and
> risk tier is an enum. This evidence view fingerprints the source, lists exactly
> what was validated, and confirms that SOAP authentication headers are not exposed."

## 0:55–1:15 — prove it generalizes

Paste a small, different SOAP payload containing an `AuthToken` into **Try an unseen
SOAP payload**; click **Analyze contract**.

> "For an unseen payload, LegacyLink discovers candidate JSON fields and types in
> memory. It flags the sensitive token, returns no raw values, and persists nothing.
> The operator can now review the inferred contract before asking Codex to generate
> the final API."

## 1:15–1:30 — close

Show `/docs` and the Git diff.

> "LegacyLink makes Codex useful in the place enterprises need it most: converting
> legacy integration work from an opaque, manual bottleneck into a fast, auditable,
> human-approved engineering workflow."

## Recording checklist

- Keep the demo server and dashboard already running.
- Use an intentionally different XML sample for the analyzer section.
- Show the validation report before the analyzer to establish trust.
- Never claim production deployment or live Dodo billing; both are deliberate next
  integrations, not implemented features.
