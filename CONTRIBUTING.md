# Contributing templates

Every template is a folder `<category>/<id>/` with a `contract.yaml` and the
files it needs. A good template reproduces a real vulnerability in a
**vulnerable** state, the same system with the flaw removed in a **patched**
state, and proves each with an independent `verify` probe.

The [README](README.md#layout) is the canonical reference for the folder layout,
how to choose a category, and the id naming grammar. In short: one target per
category, chosen by the product you scan (language runtimes go in `web-apps`
with a `runtime` tag); overlays live under `files/common|vulnerable|patched/`;
and the id follows `<product>[-<version>][-<component>]-cve-<YYYY>-<NNNNN>[-<slug>]`.

## Checklist

- [ ] `metadata.fidelity` is set. Use `real` and stand up the genuine software
      (with its real database/dependencies via `sidecars` and a `seed` that
      initialises it) whenever a public image or buildable upstream source
      exists. Reserve `simulated` for bare-OS / device / protocol flaws that no
      public image reproduces, and add a `-sim` suffix to the id so a real and a
      simulated target for the same flaw can coexist.
- [ ] `metadata.id` equals the folder name and follows the grammar
      `<product>[-<version>][-<component>]-cve-<YYYY>-<NNNNN>[-<slug>]`
      (`apache-httpd-2.4.49-cve-2021-41773`, `wordpress-cve-2026-60137-wp-query-sqli`),
      or `<product>-<flaw>` for things without a CVE (`redis-unauthenticated-access`).
      Exactly one primary CVE goes in the id; list every CVE in `vuln_refs`.
- [ ] `metadata.updated` is set when you change an existing target (metadata,
      versions, or probes); new targets may leave it unset (it defaults to `added`).
- [ ] `base` is **pinned**: an image `digest`, a source `commit`, or a
      self-contained `build` context. `vulnsuite validate` fails on an unpinned
      base. Get a digest with `docker buildx imagetools inspect <image>`.
- [ ] `vulnerable` and `patched` differ by the **minimum** that toggles the flaw
      (a newer tag, one config directive, one patched file). If the diff is
      large, a scanner's discrimination is measuring more than the flaw.
- [ ] Each state has a `verify` probe written from the advisory, **not** copied
      from a scanner matcher: the vulnerable probe asserts the *impact*
      (`root:.*:0:0:` in the body, `uid=` from the injected command, the leaked
      secret), the patched probe sends the **same request** and asserts it now
      fails (`status_in: [403, 404]` and `body_absent`).
- [ ] The scanner templates that detect the target are linked in
      `detected_by` (`nuclei:<id>`), so whoever deploys it knows what to run.
      `vulnsuite info <id>` with a nuclei-templates checkout suggests
      candidates by CVE. Set `detection: scanner` only once you have run the
      scanner against both states and it fires on vulnerable and stays silent
      on patched; until then leave `detection` unset (declared, unverified).
      `custom-only` means no public template exists for the flaw.
- [ ] **No scanner template exists?** That is a detection gap, and your target
      is the perfect test bed for closing it: write a nuclei template, verify
      it against both states, contribute it to
      [nuclei-templates](https://github.com/projectdiscovery/nuclei-templates),
      then link it here. `vulnsuite validate` lists these gaps
      (`no-detected-by`): a target with `detection` unset is the open invitation.
- [ ] `references` link the advisory and the fix. `vuln_refs` holds the CVE /
      GHSA, or a `VS-<AREA>-<NAME>` id for flaws without one.
- [ ] `vulnsuite validate -t <id>` is clean (use `-strict` to see warnings as
      failures) and both `vulnsuite run vulnerable|patched -t <id>` print
      `verify: ok`.
- [ ] Nothing in the folder is larger than it must be. Vendor a source tarball
      when upstream may disappear; never vendor a base image.

## Optional per-target README

A target's `contract.yaml` is the source of truth; most targets need no README.
Add one **only** for build/run nuance a reader can't get from the contract — an
arch-specific build, an HTTPS requirement, a seed step, a vendored tarball. Keep
CVE facts (severity, affected/fixed versions, references) **out** of it; those
live in `metadata` so a frequently-updated CVE changes in one place. Use this
template:

```markdown
# <id>

> One line: what makes this target non-trivial to stand up.

## Why this exists
What's special about the build/run that the contract can't express
(arch logic, HTTPS requirement, source build, seed data).

## Building / running notes
Host prerequisites or gotchas (e.g. "needs an amd64 host", "first boot seeds a DB").

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
```

## Choosing the base and the state mechanism

| Situation | `base.kind` | vulnerable | patched |
| --- | --- | --- | --- |
| released version, fix is a newer version | `image` | the vulnerable tag | `image:` override to the fixed tag |
| flaw needs a config to be reachable | `image` | `overlay` a vulnerable config | `overlay` the fixed config |
| unreleased / RC commit | `source` (repo + commit) | build at the commit | `patch` with the fix, or `image:` the fixed tag |
| no public image reproduces it (devices, protocols, sims) | `build` (local `build/`) | build `build/` as-is | `overlay` a patched file, or a `patch` |

Prefer `image` — it is the most portable. Use `build` for anything with no
reproducible public image; keep the vulnerable and patched apps identical
except for the flawed code path, and make the sim faithful to the real class
(real endpoints, a real sink), not a toy. You can prove a sim without Docker
by running the app and the verify request by hand before shipping.

## Authoring with an assistant

[SKILL.md](SKILL.md) is a complete authoring procedure (gather facts, choose
the base, write the contract, write independent probes, validate) that an AI
coding assistant can follow to turn a CVE, Nuclei template or advisory into a
template. Review what it produces against the checklist above.

## Pull requests

- One template (or one coherent fix) per PR.
- CI validates every template with the current vulnsuite and checks the
  contract against `schemas/contract.schema.json`; both must pass.
- Say in the PR which scanner(s) you ran against both states and what they
  reported.
- PRs are squash-merged with the PR title as the commit message.

## Commit messages: Conventional Commits

Commits and PR titles follow
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
The scope is the template id (or category for cross-cutting changes):

| Type | Use for |
| --- | --- |
| `feat` | a new template, or a new state / probe on an existing one |
| `fix` | a template that was wrong: wrong version, probe, base, file |
| `refactor` | restructuring a template with no change to what it proves |
| `docs` | README, CONTRIBUTING, SKILL, comments |
| `chore` | pins, metadata, housekeeping |
| `ci` | workflow changes |

Examples:

```
feat(web-apps): add metabase-cve-2023-38646
fix(grafana-8.3.0-cve-2021-43798): assert body_absent on the patched state
chore(web-servers): pin httpd:2.4.49 digest
feat(exposures)!: rename vuln_refs prefix AB- to VS-

BREAKING CHANGE: consumers keying on AB- ids must update.
```

Description: imperative, lower-case, no trailing period, at most 72 characters.

## Safety and responsibility

Templates stand up real vulnerabilities. Keep exploitation inside `verify`
minimal (prove the impact, don't weaponise it), never include credentials or
data that are not fake, and never reference a host you do not own.
