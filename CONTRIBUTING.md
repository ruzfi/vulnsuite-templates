# Contributing templates

Every template is a folder `<product-surface>/<id>/` with a `contract.yaml` and
the files it needs. A good template reproduces a real vulnerability in a
**vulnerable** state, the same system with the flaw removed in a **patched**
state, and proves each with an independent `verify` probe.

The [README](README.md#layout) is the canonical reference for the folder layout,
how to choose a category, and the id naming grammar. In short: the directory is
one axis — the product/surface you scan (language runtimes go in `web-apps` with
a `runtime` tag) — while the finding class lives in `metadata.class`, not in a
directory; overlays live under `files/common|vulnerable|patched/`; and the id
follows `<product>[-<version>][-<component>]-cve-<YYYY>-<NNNNN>[-<slug>]`.

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
- [ ] `metadata.class` is set to the finding class(es): `vuln` (a flaw in the
      software, usually CVE-tracked), `misconfig`, `exposure`, `default-login`,
      or `weak-crypto`. This is the filter axis that replaces the old issue-class
      directories; CVE and KEV status are derived (from `vuln_refs` and the CISA
      KEV catalog), not set by hand. Set `disclosed` when you know the public
      disclosure date.
- [ ] `metadata.updated` is set when you change an existing target (metadata,
      versions, or probes); new targets may leave it unset (it defaults to `added`).
- [ ] If the target is a member of a **variant group** (same vuln, several
      members), `metadata.group` / `primary` / `variant` are set per
      [Authoring a variant group](#authoring-a-variant-group): one shared
      `group`, `primary: true` on exactly one member, a unique `variant` on each.
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

## Authoring a variant group

Sometimes several targets are the **same vulnerability expressed differently** —
a canonical reproduction plus a WAF-evasion variant, the same flaw across runtime
or distro branches, or a set of remediation strategies for one CVE. Tie them into
a **variant group** so `vulnsuite` can pull the representative with one handle
(`-t <group>`) or the whole family at once (`-t <group> -variants`). Each member
stays its own folder and `contract.yaml`; three optional `metadata` fields link
them:

- **`group`** — the family handle, **identical on every member**
  (`^[a-z0-9]+(-[a-z0-9]+)*$`, e.g. `php2shell`). It must not collide with any
  target `id`. A selector naming the group resolves to the primary.
- **`primary: true`** — on **exactly one** member, the canonical one a bare
  `-t <group>` runs. Zero or several primaries in a multi-member group is a
  validator error. (A *lone* target that sets only `group` is just a nickname for
  its id and needs no `primary`/`variant`.)
- **`variant`** — each member's discriminator, **unique within the group**
  (`^[a-z0-9]+(-[a-z0-9]+)*$`, e.g. `version-upgrade`, `alpine-3-24`). Dots are
  not allowed, so write a version as `3-24`, not `3.24`.

Rules the validator enforces per group: exactly one `primary`, unique `variant`
per member, the `group` handle distinct from every `id`, and (soft) a single
category and shared `vuln_refs` across the family — variants of one vuln should
agree on the CVE. Keep every CVE fact in each `contract.yaml metadata` only;
nothing about the group goes into a README.

The two shipped families are the pattern to copy:

| Group | Members | Primary | Variant axis |
| --- | --- | --- | --- |
| `php2shell` | 3 × PHP 8.2 mod_php RCE (CVE-2026-109618/109619) | `…-version-upgrade-patch` (`version-upgrade`) | remediation strategy (`version-upgrade`, `workaround`, `expose-php-off`) |
| `sshole` | 9 × OpenSSH auth bypass (CVE-2026-123158) | `openssh-10.3p1-alpine-3.24-…` (`alpine-3-24`) | Alpine branch (`alpine-3-16` … `alpine-3-24`) |

`CATALOG.md` (regenerated by `scripts/gen_catalog.py`) renders a **Group** column:
members sort together under their handle and ★ marks the primary.

## Authoring a suite

A **suite** is a named, shareable list of selectors vulnsuite (v0.2.1+) stands up
in one run — a pentest profile, a regression set, a demo. Add a file at
`suites/<name>.txt`; it ships with the repo (`vulnsuite update-templates`) and is
referenced with the explicit `suite:` prefix (`run -t suite:<name>`). The full
grammar is [schemas/suite-format.md](../schemas/suite-format.md); in short:

- **One selector per line.** A line is an id, a group handle, a category, a
  nested `suite:<name>`, or a filter line (`-class misconfig`, same filters as
  `vulnsuite list`). `#` comments and blank lines are ignored.
- **Composition.** Lines union into one de-duplicated, order-stable set; filters
  on one line AND, separate lines OR. A group handle contributes its primary by
  default, all members under `-variants`.
- **Leading `#` block = the description.** Start it `# <name> — <one line>`;
  `scripts/gen_suites.py` reads it into `SUITES.md`.

Checklist for a new or changed suite:

- [ ] File is `suites/<name>.txt`, `<name>` lowercase-kebab, with a `# <name> — …`
      description header.
- [ ] Selectors are **durable** where possible — a group handle or a filter over
      a hand-maintained id list, so the suite tracks the corpus.
- [ ] **No CVE facts** in the file: it references targets and groups by selector
      only (severity, versions, references stay in each `contract.yaml`).
- [ ] `python3 scripts/gen_suites.py` regenerates `SUITES.md` and passes its lint
      (no selector resolves to nothing, no unknown nested suite, no cycle). CI
      runs `--check` and fails if `SUITES.md` is stale.

The shipped seeds are the pattern to copy:

| Suite | What it stands up |
| --- | --- |
| `php-rce` | the `php2shell` family (PHP mod_php RCE) |
| `ssh-bypass` | the `sshole` family (OpenSSH auth bypass) |
| `misconfig-sweep` | every `-class misconfig` target (one filter line) |
| `nightly` | both families + all misconfig/exposure targets (groups + filters) |

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
