# php-fpm-status-exposure

> Config-axis target: one nginx + PHP-FPM image; the states differ only by
> `FPM_STATUS`.

## Design
The entrypoint turns `FPM_STATUS` into a `pm.status_path` pool setting routed
through nginx. Patched is the default pool configuration: no status path, so
`/status` is not served. The fix for this class is the configuration, not a
version bump. A dummy index answers 200 in both states (the readiness check).

## Detection
`nuclei:php-fpm-status` is declared from its fingerprint but not yet run against
both states. Set `detection: scanner` once it fires on vulnerable and stays
silent on patched.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
