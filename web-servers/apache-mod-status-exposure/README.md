# apache-mod-status-exposure

> Config-axis target: the same httpd image in both states.

## Design
The vulnerable state's `command` enables `mod_status` at `/server-status` with
`Require all granted`, then starts httpd — exactly the change operators make by
hand. The patched state runs the stock image (no status handler); the fix is to
not expose it. The stock "It works!" index answers 200 in both states (the
readiness check).

## Detection
`nuclei:apache-server-status` is declared from its fingerprint but not yet run
against both states. Set `detection: scanner` once it fires on vulnerable and
stays silent on patched.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
