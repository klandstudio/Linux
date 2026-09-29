# AGENTS.md — Linux

Kland GitHub work: read `klandstudio/hq/AGENTS.md` first if you can access
the private repository; this file stands on its own when you cannot.

## Public boundary and read map

This is a public repository for Linux hardware projects, reverse engineering,
and reusable tooling that is safe to publish. Start with `README.md`, then the
README and source in the specific directory under `projects/`; do not read all
project material recursively.

## Working rules

- Treat every committed file and all Git history as public. Never add secrets,
  private identifiers, vendor firmware payloads, private captures, addresses,
  or personal information.
- Stay within the authorized task. Work on a branch, open a pull request, and
  leave merging to the owner.
- Preserve validation provenance. Distinguish observed device behavior,
  source-confirmed protocol fields, hypotheses, and untested procedures.
- Prefer reversible, bounded tests and document rollback steps for hardware
  procedures.

## Human and safety gates

Do not run arbitrary HID/register probing, flash firmware, alter host services,
or apply hardware, power, thermal, or display changes without separate owner
and safety authorization. Repository review is not authorization to operate on
physical hardware or publish from it.
