# php-fpm-status-exposure

> Config-axis target: one nginx + PHP-FPM image; the states differ only by
> `FPM_STATUS`.

## Design
The entrypoint turns `FPM_STATUS` into a `pm.status_path` pool setting routed
through nginx. Patched is the default pool configuration: no status path, so
`/status` is not served. The fix for this class is the configuration, not a
version bump. A dummy index answers 200 in both states (the readiness check).

## Verification
The probe asserts the leak itself, in the JSON view (the scanner reads the text
view): the per-process `full` status records every worker's last request URI,
query string included, so the probe sends a marker in its own query string and
reads it back.

| request | vulnerable (`FPM_STATUS=1`) | patched (`FPM_STATUS=0`) |
| --- | --- | --- |
| `GET /status?json&full&vs=7f3a9c` | 200, JSON with `"process manager":"dynamic"` and a process entry `"request uri":"\/status?json&full&vs=7f3a9c"` | 404, PHP-FPM's `File not found.` (the pool has no status path), no `process manager` |

The patched assertion is positive (FPM's own refusal), so a target that failed
to start cannot pass it.

## Detection
`nuclei:php-fpm-status` fires on the vulnerable state and stays silent on the
patched one (2026-11-21).

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
