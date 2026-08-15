# LegacyLink: judge pitch and Q&A

## 45-second pitch

"LegacyLink modernizes undocumented SOAP integrations with Codex, but it solves the
trust problem that usually stops AI-generated enterprise code from shipping. We
capture a SOAP contract, ask Codex to work in an isolated Git worktree, and generate
a typed FastAPI draft with tests and OpenAPI documentation. The reviewer does not
need to trust the agent: the dashboard shows source provenance, validated fields,
strict types, and an explicit approval boundary. For a new payload, LegacyLink
discovers candidate fields in memory, flags sensitive fields, and never returns raw
values. It turns a manual reverse-engineering bottleneck into a fast, auditable
engineering workflow."

## Three points to repeat

1. **Codex is central:** it does constrained implementation work in an isolated
   worktree; this is not a generic chatbot layered onto an API.
2. **Trust is the differentiator:** strict types, negative tests, source digest,
   sensitive-field detection, and human review make the output inspectable.
3. **The value is real:** legacy integration work blocks modernization across banks,
   health systems, insurers, and government platforms.

## Likely judge questions

### "Why not just ask Codex to write a wrapper?"

"That is a useful start, but it is not enough for a regulated or sensitive legacy
system. LegacyLink adds a repeatable workflow around Codex: isolated changes,
contract validation, privacy-aware discovery, test evidence, and human sign-off."

### "Is this production ready?"

"The prototype is deliberately a reviewable migration draft, not an autonomous
production deployer. Production rollout would add source authentication,
authorization, secrets management, SOAP fault handling, and a real billing-provider
integration. Making that boundary explicit is intentional."

### "How does the unseen-payload analyzer protect data?"

"It analyzes in memory, enforces payload and field-count limits, detects likely
sensitive field names, and returns only metadata: paths, inferred types, confidence,
and sensitivity—not source values."

### "What is the next milestone?"

"A review queue that turns the inferred contract into a Codex-generated pull request,
then runs fixture-based contract tests before a human approves deployment."

## Avoid saying

- "Production-ready autonomous deployment"
- "Live Dodo billing" (the code contains a clearly labeled integration boundary)
- Unmeasured claims such as exact time saved or conversion speed
