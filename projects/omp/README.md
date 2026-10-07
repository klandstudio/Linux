# OMP on Linux — free hosted model providers

Notes on running [OMP](https://github.com/klandstudio/omp) as a CLI coding agent
on Linux Mint 22.3, specifically on **free hosted model tiers that need no
credit card**, and on a failure mode that cost real time to diagnose.

Overseeing notes for this install live in the private `klandstudio/hq` repo at
`agents/omp.md`. This document carries the parts that are safe to publish.

## The failure mode worth reading

**A model appearing in a catalog is not evidence that it works.** Every broken
selector below was listed with plausible context windows, plausible pricing, and
no error marker. Three distinct faults showed up:

1. **Malformed selectors.** `groq/groq/compound` carries a doubled provider
   prefix in its own catalog entry. Both the doubled and single-prefixed forms
   404 at the API. It is listed at `$0/$0`, which makes it look like the obvious
   free pick.
2. **Retired models, still listed.** `google/gemini-2.5-flash` returns 404 with
   "no longer available to new users" and names its own replacement in the error
   text. Some NVIDIA entries return 410 with an explicit end-of-life date —
   `deepseek-v4-pro` and `deepseek-v4-flash` both died 2026-08-07 and are still
   catalogued with full specs.
3. **Guessed provider prefixes.** Gemini's provider is `google/`, not
   `gemini/`. The family name is not the provider ID.

Also worth separating: **rate limits and output caps are different limits, and
they often share a number by coincidence.** An 8000 *tokens-per-minute* ceiling
produces a 413 that reads like a context overflow. Switching to a model with a
larger output allowance does not fix it. OMP's own warning text on that error
suggests trimming archived image frames and raising body limits, which is the
wrong lever entirely.

## Verified working set

Confirmed by live response, free tier, no card (checked 2026-10-07):

| Selector | Context | Max output | Notes |
|---|---|---|---|
| `groq/openai/gpt-oss-20b` | 131K | 66K | 8000 TPM ceiling; ~2.4 tok/s |
| `nvidia/moonshotai/kimi-k3` | 1M | 131K | listed `$0/$0`; fastest of the set |
| `mistral/ministral-3b-latest` | 131K | 131K | small; larger Devstral entries 429 |

Three separate quota pools, which is the point — a throttle on one does not take
out the others.

`google/gemini-3-flash-preview` authenticated and resolved but was returning 503
high-demand throughout testing. Transient, not broken; worth retrying.

Rejections worth recording, since each looks fine in a catalog listing:

| Selector | Result |
|---|---|
| `groq/groq/compound` | 404, doubled selector prefix |
| `google/gemini-2.5-flash` | 404, retired for new users |
| `groq/qwen/qwen3.8-27b` | 400, `enable_thinking` unsupported at every level |
| `nvidia/mistralai/devstral-2-123b-instruct-2512` | 404 page not found |
| `nvidia/deepseek-ai/deepseek-v4-{pro,flash}` | 410, EOL 2026-08-07 |
| `mistral/devstral-latest` | 429, per-model rate limit |

## Probing a selector

Non-interactive, no session write, no tools. Exit code is 0 whether or not the
model answered, so read the body, not the status:

```bash
omp -p --no-session --no-tools --mode json \
  --model <provider>/<model> "reply with the single word: ok"
```

Look for a `message_end` event with `role: "assistant"`, an empty `content`
array, and an `errorStatus`. A bare `Working...` line with no JSON is startup
output, not a response.

## Config notes

`modelRoles` is a record and must be set whole:

```bash
omp config set modelRoles '{"default":"groq/openai/gpt-oss-20b"}'   # works
omp config set modelRoles.default groq/openai/gpt-oss-20b           # Unknown setting
```

`Ctrl+P` cycles `enabledModels`. Roles and scope are both read at startup, so
config edits need an OMP restart to take effect.

Provider listings are gated on credentials: without the provider's key in
`~/.omp/agent/.env`, `omp models <provider>` reports no matches. That reads like
an empty catalog but means a missing key.

To enumerate a provider's models without a real credential — the catalog resolves
and the models list, but nothing authenticates:

```bash
NVIDIA_API_KEY=dummy omp models nvidia
```

## Credentials

Keys live in `~/.omp/agent/.env`. **Never commit them, never paste them into a
PR, issue, or chat.** Document variable names only: `GROQ_API_KEY`,
`GEMINI_API_KEY`, `MISTRAL_API_KEY`, `NVIDIA_API_KEY`.

Mistral is a useful cautionary example on plan gating: its free tier lists API
credits in the plan description, but the workspace key page is disabled with
"upgrade to activate your API keys." An organization-level key page was not
gated. Free-tier claims should be checked against the account, not a tier
comparison page.

## Untested and unresolved

- **NVIDIA rate limit unmeasured.** No `ratelimit-*` or `retry-after` headers
  are returned, and no 429 was provoked, so the commonly cited 40 RPM figure is
  unverified third-party here.
- **NVIDIA credit exhaustion behaviour unknown.** No authoritative statement on
  whether exhausted credits convert to billing.
- **Antigravity interaction.** Google's docs direct third-party agents wanting
  Gemini to use an AI Studio key rather than the Antigravity surface; BYO key
  is not supported in Antigravity itself. Forum reports suggest AI Studio free
  tier usage may share quota with an account's Antigravity usage. Untested.