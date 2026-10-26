# vulnsuite-templates

Community templates for [vulnsuite](https://github.com/ruzfi/vulnsuite):
reproducible **vulnerable and patched target systems**, one folder per
target, that vulnsuite builds into content-addressed Docker images and runs in
a verified state. Each is a declarative contract for standing up a vulnerable
system and its patched twin.

```bash
vulnsuite update-templates                 # fetches this repo to ~/vulnsuite-templates
vulnsuite list
vulnsuite build -t web-servers -j 4
vulnsuite run -t apache-httpd-2.4.49-cve-2021-41773 -expose host
```

## Layout

```
<category>/<id>/
  contract.yaml      the target (required)
  README.md          optional; only for build/run nuance the contract can't state (no CVE facts)
  files/
    common/          overlays shared by both states
    vulnerable/      overlays applied only to the vulnerable state
    patched/         overlays applied only to the patched state
  patches/           git patches for source bases
  src/               build context that builds the genuine upstream software
  build/             build context for a minimal harness app on a real stack
schemas/contract.schema.json   the contract schema (mirrored from vulnsuite)
CATALOG.md           generated index of every target (never hand-edited)
```

The per-state overlay folders are named for the states they feed
(`states.vulnerable` / `states.patched`), so a glance at `files/` tells you which
state each overlay belongs to. A target with no overlays needs no `files/` at all.

A `base.kind: build` target carries its own build context in one of two folders,
by **whose code is inside**: **`src/`** builds the *genuine upstream software* (a
vendored release, an official source checkout); **`build/`** builds *code we
wrote* — a minimal harness that stands a real stack up in a vulnerable config
(the `misconfig/` targets, still `fidelity: real`) or a full stand-in for a
service with no reproducible image (the `iot/` sims, `fidelity: simulated`).

### Choosing a category

Pick the category by the **product you point a scanner at** — the top of the
running stack — not by the vulnerability class (that lives in `tags`/`cwe`). One
target lives in exactly one category; everything else a reader might filter on is
metadata. A **language-runtime** flaw (PHP, Node.js) reached over HTTP is a
`web-apps` target with a `runtime` tag — `web-servers` is only for the HTTP
server daemon itself (httpd, nginx).

| Category | What lives there |
| --- | --- |
| `web-servers` | the HTTP server daemon: Apache httpd, nginx, TclHttpd ... version CVEs and config misconfigurations |
| `web-apps` | applications and language runtimes served over HTTP: Grafana, WordPress, Nextcloud, PHP, Node.js ... (tag runtimes `runtime`) |
| `databases` | CouchDB, Elasticsearch, Redis ... unauthenticated / default access |
| `exposures` | leaked `.env`, phpinfo, actuator, metrics, swagger ... information disclosure |
| `misconfig` | CORS, directory listing, exposed `.git`, GraphQL introspection, open redirect |
| `default-logins` | default and weak credentials |
| `iot` | simulated devices: cameras, routers, UPnP, debug ports, backdoors |
| `network-services` | non-HTTP services (SSH, ...) |

### Naming a target

The folder name **is** `metadata.id` (the schema ties them together). Use one grammar:

```
<product>[-<version>][-<component>]-cve-<YYYY>-<NNNNN>[-<class-slug>]
```

- **product** — canonical software name, no redundant prefix (`openssh`, not `ssh-openssh`).
- **version** — only when it is load-bearing (a pure-version flaw, e.g. `grafana-8.3.0-...`).
- **component** — a sub-product where it disambiguates (`nextcloud-collabora-code-...`).
- **cve** — exactly **one** primary CVE in the id; list every CVE in `metadata.vuln_refs`.
- **class-slug** — optional human hint, always **after** the CVE (`-wp-query-sqli`).

No CVE (sims, misconfigurations): `<product>-<class>` (`redis-unauthenticated-access`),
with a `VS-<AREA>-<NAME>` id in `vuln_refs`.

Every CVE fact lives **only** in `contract.yaml metadata` — never restated in a
README — so updating a target (a rescore, a new fixed version, a new reference)
is a one-line edit in one place. Bump `metadata.updated` when you do.

Each template declares a **fidelity**: `real` runs the genuine affected software
(the default, and what you should write whenever a public image or buildable
upstream source exists); `simulated` is a faithful stand-in, reserved for
bare-OS / device / protocol flaws with no reproducible image (the `iot/` targets,
and a few exposure/misconfig sims). `vulnsuite list -fidelity real|simulated`
filters them. Prefer real: stand up the actual software, with its real database
or dependencies, over simulating it.

Each template's `metadata.detection` says what a stock scanner can do with it:

- `scanner` — the target reproduces a *specific* public scanner template's
  fingerprint, named in `detected_by` (e.g. `nuclei:laravel-env`). That
  scanner's template fires on the vulnerable state and stays quiet on the
  patched one.
- `custom-only` — a faithful simulation of a vulnerability class with **no**
  public template (device sims, generic default logins, open redirect, ...).
  A stock scanner will not flag these; they exist to test *your* detection.

## The contract in one screen

```yaml
apiVersion: vulnsuite/v1
kind: Target
metadata:
  id: grafana-8.3.0-cve-2021-43798
  summary: Grafana 8.0.0-8.3.0 unauthenticated arbitrary file read via the plugin path.
  vuln_refs: [CVE-2021-43798]
  cwe: [CWE-22]
  severity: high
  references: [https://github.com/grafana/grafana/releases/tag/v8.3.1]
base:
  kind: image
  image: grafana/grafana:8.3.0
  digest: sha256:...                      # pin it
service:
  ports: [ { container: 3000, protocol: http } ]
  healthcheck: { http: { path: /login, status: 200 }, timeout: 60s }
states:
  vulnerable:
    verify:
      - http: { raw_path: "/public/plugins/alertlist/../../../../../../../../etc/passwd", status: 200, body_matches: "root:.*:0:0:" }
  patched:
    image: grafana/grafana:8.3.1          # the fix is a newer version
    verify:
      - http: { raw_path: "/public/plugins/alertlist/../../../../../../../../etc/passwd", status_in: [400, 404], body_absent: "root:.*:0:0:" }
```

Three things make a template good: the base is **pinned**, `vulnerable` and
`patched` differ by the **minimum** that toggles the flaw, and each state has
a `verify` probe written from the **advisory**, not from a scanner's matcher.
The full field reference is in
[vulnsuite/docs/CONTRACT.md](https://github.com/ruzfi/vulnsuite/blob/main/docs/CONTRACT.md).

## Contributing a template

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version:

```bash
vulnsuite validate -t <your-template>        # clean, pinned
vulnsuite run vulnerable -t <your-template>  # verify: ok
vulnsuite run patched   -t <your-template>   # verify: ok (the flaw is gone)
```

If you work with an AI assistant, [SKILL.md](SKILL.md) is a step-by-step
authoring guide it can follow to turn a CVE, a Nuclei template or an advisory
into a template.

## Safety

These targets are deliberately vulnerable. Run them on networks you own, keep
the default `internal` exposure (nothing is published on the host) unless you
need otherwise, and never leave a vulnerable target reachable from the
Internet.

## License

MIT — see [LICENSE](LICENSE). Vendored third-party sources inside templates
(e.g. the TclHttpd tarball) keep their own licenses.
