# django-debug-enabled

> Config-axis target: the same image in both states, differing only by
> `DJANGO_DEBUG`.

## Design
Not a version bug. The patched state is the secure default (`DEBUG` off); the
vulnerable state turns `DEBUG` on. The fix for this class is the configuration,
not a version bump.

## Verification
A request to a route that does not exist is enough: with `DEBUG` on the 404
lists the URLconf ("Django tried these URL patterns"); with it off, a plain 404.
The leaked settings are never harvested.

The healthcheck also uses an unrouted path: it answers 404 in both states as
soon as the dev server is up, which makes it a stable readiness signal.

## Detection
`nuclei:django-debug-config-enabled` is declared from its fingerprint but not yet
run against both states. Set `detection: scanner` once it fires on vulnerable
and stays silent on patched.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
