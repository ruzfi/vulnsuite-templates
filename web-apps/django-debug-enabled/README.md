# django-debug-enabled

> Config-axis target: the same image in both states, differing only by
> `DJANGO_DEBUG`.

## Design
Not a version bug. The patched state is the secure default (`DEBUG` off); the
vulnerable state turns `DEBUG` on. The fix for this class is the configuration,
not a version bump.

## Verification
A request to a route that does not exist is enough. The probe uses its own
unrouted path (not the scanner's) and asserts what actually leaks rather than
the page heading:

| request | vulnerable (`DEBUG` on) | patched (`DEBUG` off) |
| --- | --- | --- |
| `GET /vulnsuite-probe-unrouted/` | 404, the URLconf listing with the project's `admin/` route, followed by the "you have `DEBUG = True`" notice | 404, Django's production page `<h1>Not Found</h1><p>The requested resource was not found on this server.</p>`, no `DEBUG = True` |

The patched assertion is positive (Django's own production 404 body), so a
target that failed to start cannot pass it. The leaked settings are never
harvested.

The healthcheck also uses an unrouted path: it answers 404 in both states as
soon as the dev server is up, which makes it a stable readiness signal.

## Detection
`nuclei:django-debug-config-enabled` fires on the vulnerable state and stays
silent on the patched one (2026-11-21).

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
