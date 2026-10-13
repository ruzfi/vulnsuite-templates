---
name: authoring-vulnsuite-templates
description: >-
  Turn a Nuclei template, an nmap script, or a newly published CVE into a vulnsuite
  target template (contract.yaml + files). Use when a user wants
  a vulnerable/patched target built for a specific vulnerability, especially a
  fresh CVE.
---

# Authoring a vulnsuite target template

You are helping build a **reproducible vulnerable target** the user can scan with
their own scanner. Your output is a template folder:

```
<category>/<id>/
  contract.yaml          the target contract (required)
  files/...              overlay files, patched source, config (as needed)
  src/                   Dockerfile + source (only for build-from-source sims)
```

The scanner is not your concern. Your job is a target that (a) stands up in a
**vulnerable** state, (b) stands up in a **patched** state that differs by the
minimum that toggles the flaw, and (c) proves each state with an independent
`verify` probe. Then it must pass `vulnsuite validate`.

Read the existing templates in this repository for worked examples before writing.
The full field reference is `schemas/contract.schema.json` (and vulnsuite/docs/CONTRACT.md).

---

## Step 1 — gather the facts

From the CVE / Nuclei template / advisory, pin down:

- **Product and version** that carries the flaw. The exact version matters.
- **How it is fixed** — a newer version, a config change, or a code patch.
- **The vulnerability class** (traversal, RCE, auth bypass, info disclosure, …)
  and **CWE**.
- **A request or action that demonstrates it**, and the **observable result**
  (a status code, a string in the body, a banner). This becomes `verify`.
- **References**: the advisory and the fix commit/release.

If it is a Nuclei template, the `http`/`network` request and its `matchers` tell
you the demonstrating request and the observable — but see the hard rule in
Step 4: your verify probe must be written **independently**, not copied.

---

## Step 2 — choose the base and the state mechanism

Pick the cheapest mechanism that reproduces the flaw. This decides `base.kind`
and how each state is reached.

| Situation | `base.kind` | vulnerable | patched |
| --- | --- | --- | --- |
| Flaw is in a released version; fix is a newer version | `image` | base image (vulnerable tag) | `image:` override to the fixed tag |
| Flaw needs a config to be reachable | `image` | `overlay` a vulnerable config | `overlay` the fixed config |
| Flaw is an unreleased/RC commit | `source` (repo + commit) | build at commit | `image:` fixed tag, or a fix `patch` |
| No public image reproduces it (custom device, IoT, protocol) | `build` (local `src/`) | build `src/` as-is | `overlay` a patched source file, or a `patch` |

Rules of thumb:

- Prefer `image` — it is the most portable. **Pin the digest**
  (`docker manifest inspect <img> -v | grep -m1 digest`); an unpinned base is a
  `validate` error.
- Use `overlay` when the same image is vulnerable or not depending on config
  (Apache mod_status, an aliased directory, a `requirepass`).
- Use `build` for anything with no reproducible public image — IoT devices,
  bespoke protocols, a vulnerable app you simulate in Python/Go sockets. The
  whole build context lives in the template's `src/`.
- `patched` should differ from `vulnerable` by the **minimum**. If the diff is
  large, the discrimination test is measuring more than the vulnerability.

---

## Step 3 — write the contract

Skeleton (fill every TODO):

```yaml
apiVersion: vulnsuite/v1
kind: Target
metadata:
  id: <product>-<version>-<cve>      # lowercase, hyphens/dots; unique
  summary: <one line: what and how>
  vuln_refs: [CVE-XXXX-XXXXX]        # or VS-<SLUG> for a sim/misconfig with no CVE
  cwe: [CWE-NN]
  severity: critical|high|medium|low
  tags: [<product>, <class>]
  references: [<advisory>, <fix>]
  maintainer: <you>
  added: "YYYY-MM-DD"
base:
  kind: image                         # image | source | build
  image: <image:tag>
  digest: sha256:<pin-it>
service:
  ports: [ { container: <port>, protocol: http } ]
  healthcheck: { http: { path: /, status: 200 }, timeout: 60s }
states:
  vulnerable:
    # overlay / patch / image / environment as chosen in Step 2
    verify:
      - http: { raw_path: "<demonstrating request>", status: 200, body_matches: "<proof>" }
  patched:
    image: <fixed-tag>                # or overlay/patch
    verify:
      - http: { raw_path: "<same request>", status_in: [403,404], body_absent: "<proof>" }
```

Notes:

- `raw_path` is sent **verbatim** — use it for traversal/encoding payloads so the
  bytes survive. `path` is fine for ordinary requests (it may include a query).
- Probe kinds: `http` (request: `method` / `path` or `raw_path` / `headers` /
  `body`; assertions: `status` / `status_in` / `body_matches` / `body_absent` /
  `header_matches` / `header_absent`), `tcp` (send / banner_matches), `exec` (run
  inside the container). Exactly one kind per probe.
  - `header_matches: { Name: <regex> }` and `header_absent: [Name, ...]` assert on
    **response** headers — use them for header-based findings: CORS
    (`Access-Control-Allow-Origin` reflected + `Allow-Credentials: true`),
    open-redirect (`Location: ^https?://evil`), missing security headers, cookie
    flags. A header match counts as a strong assertion (no `weak-verify` warning).
- Per-state `environment`, `command`, and `overlay` let one image serve both
  states (e.g. redis run with a per-state `redis.conf`).

---

## Step 4 — write the verify probes (the one hard rule)

**A verify probe must be independent of the scanner's detection logic.** Do not
copy the Nuclei matcher. If your verify sends the same request and greps the same
string the scanner does, you have only proven the scanner agrees with itself, and
the target could be entirely wrong while every scan "passes".

Write verify from the **advisory and first principles**:

- Vulnerable state: demonstrate the *impact*. Read a file that should be
  unreachable and assert its contents (`root:.*:0:0:`), trigger the injected
  command and assert its output (`uid=`), reach the unauthenticated endpoint and
  assert the secret it leaks.
- Patched state: the **same request** now fails — asserted by a different status
  (`status_in: [403,404]`) and by `body_absent` of the proof string.

A good pair reads like: "vulnerable returns 200 with `root:...:0:0:`; patched
returns 404 and the body does not contain `root:...:0:0:`."

### The target must reproduce the scanner's fingerprint — even though verify is independent

These two rules live together and are easy to confuse:

- The **verify probe** is independent (above) — it proves the vuln from first
  principles, not by copying a matcher.
- The **target itself** must, when you want a specific scanner to detect it,
  reproduce that scanner template's *exact fingerprint*: the path it requests, the
  words/regex it matches in the body, the response headers it checks, and the
  status. A scanner matcher is extremely specific — e.g. Nuclei's `prometheus-metrics`
  needs a body word like `process_start_time_seconds` **and** the absence of certain
  other words **and** status 200; its `phpinfo-files` needs both `PHP Version` **and**
  `PHP Extension`; `springboot-env` needs `applicationConfig`/`activeProfiles` **and**
  `server.port` **and** a JSON content-type. A generic simulation that only conveys
  the *idea* of the vuln will not trip it.

So when porting from a Nuclei template: open the template, read its `path`,
`matchers` (words/regex/status/headers, and `matchers-condition`), and make the
target's vulnerable response satisfy every matched condition — while the patched
response fails at least one. Then record it:

```yaml
metadata:
  detection: scanner            # this target reproduces a real template's fingerprint
  detected_by: ["nuclei:laravel-env"]   # which one(s)
```

If **no** public template exists for the class (many IoT/device flaws, generic
default-logins, open-redirect, GraphQL introspection), mark it and don't expect a
stock scanner to find it:

```yaml
metadata:
  detection: custom-only        # validate with your own probes, not a stock scanner
```

Verify by running the actual scanner against both states: the template must fire on
`vulnerable` and stay silent on `patched`. (The `scanner`-tagged sims in this repository were
checked against real Nuclei v3 this way.)

---

## Step 5 — the `build` sim pattern (custom / IoT / fresh-CVE-no-image)

When nothing public reproduces it, simulate the vulnerable behaviour in a small
service. This is the pattern the IoT templates use.

```
templates/iot/<id>/
  contract.yaml
  src/
    Dockerfile           # FROM python:3.12-alpine; COPY app.py; CMD [...]
    app.py               # the VULNERABLE service
  files/
    app_patched.py       # the fixed service (overlaid onto the build context)
```

- `base: { kind: build, context: src }`.
- `vulnerable` builds `src/` as-is.
- `patched` overlays the fix: `overlay: [ { src: files/app_patched.py, dest: app.py } ]`.
  vulnsuite copies the context, replaces `app.py`, and builds.
- Keep the two apps identical except for the vulnerable code path, so the only
  difference is the flaw.
- Make the sim faithful to the real vulnerability class, not a toy: real
  endpoints, real-looking data, the actual sink (a shell for command injection,
  an unguarded route for auth bypass).

You can prove a sim works without Docker: run `app.py`, run the vulnerable verify
against it (expect pass); run `app_patched.py`, run the patched verify (expect
pass). Do that before shipping.

---

## Step 6 — validate

```
vulnsuite validate -t <id>
vulnsuite run vulnerable -t <id>     # verify: ok
vulnsuite run patched   -t <id>     # verify: ok (the flaw is gone)
```

`validate` must be clean (warnings about an unpinned digest are the only
acceptable ones during authoring — pin before merging). Both runs must print
`verify: ok`. If `run vulnerable` shows a verify failure, the target is not
actually vulnerable and the template is wrong — fix it before anything scans it.

---

## Container hardening — when an image won't boot

Targets run with Docker's **default capabilities** + `no-new-privileges` (not
`cap-drop ALL` — see the README). Most images just work. If `vulnsuite run` fails at
startup with a permission error, the image's entrypoint needs something the
default set doesn't cover, or it refuses to run as root:

| Startup error | Cause | Fix in `service:` |
| --- | --- | --- |
| `chroot: ... Operation not permitted` | entrypoint drops root via `chroot --userspec` (elasticsearch) | `user: "1000:0"` (skip the root path), or `cap_add: [CAP_SYS_CHROOT]` |
| `su-exec`/`gosu: Operation not permitted` | drops root→service user (redis, couchdb) | run as that user, e.g. `user: "999:0"`, or `cap_add: [CAP_SETUID, CAP_SETGID, CAP_CHOWN]` |
| `make_sock: could not bind to :80` | binding a privileged port as non-root without the cap | usually already covered by the default set; if you dropped caps, `cap_add: [CAP_NET_BIND_SERVICE]` |

Prefer `user:` over `cap_add:` when the image has a valid non-root runtime user —
it needs zero extra caps and runs the vulnerable service unprivileged. Reach for
`cap_drop: [ALL]` only for a hand-audited target where you then `cap_add` back the
exact caps it needs.

---

## Worked example: a freshly published CVE

> "CVE-2025-XXXXX: Acme Portal 3.2.0 exposes `/api/debug/env` without auth,
> leaking `DB_PASSWORD`. Fixed in 3.2.1."

1. Facts: product Acme Portal, version 3.2.0, class info-disclosure (CWE-200),
   fix = 3.2.1, demonstrating request `GET /api/debug/env`, proof `DB_PASSWORD`.
2. Base: an `image` if `acme/portal:3.2.0` exists — vulnerable = that tag,
   patched = `image: acme/portal:3.2.1`. If no image exists, a `build` sim of the
   endpoint.
3. Contract: id `acme-portal-3.2.0-cve-2025-xxxxx`, ports 8080/http, references
   the advisory + the 3.2.1 release.
4. Verify vulnerable: `GET /api/debug/env` → 200, `body_matches: "DB_PASSWORD"`.
   Verify patched: same request → `status_in: [401,404]`, `body_absent: "DB_PASSWORD"`.
5. `vulnsuite validate` → pin the digest → `vulnsuite run vulnerable/patched` → both
   `verify: ok`.

---

## Checklist before you finish

- [ ] `id` is unique, lowercase, and names the product + version + CVE.
- [ ] `base` is pinned (image digest, source commit, or a self-contained build).
- [ ] `vulnerable` and `patched` differ by the minimum that toggles the flaw.
- [ ] Each state has a `verify` probe written independently of any scanner matcher.
- [ ] Vulnerable verify asserts the impact; patched verify asserts it is gone.
- [ ] `references` link the advisory and the fix.
- [ ] `vulnsuite validate -t <id>` is clean; both `vulnsuite run` states show `verify: ok`.
