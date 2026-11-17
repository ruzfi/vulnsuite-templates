# spring-boot-actuator-env-exposure

> Config-axis target: the same image in both states, differing only by
> `MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE`.

## Design
The vulnerable state over-exposes every actuator endpoint, including `/env`.
Patched is the secure default: only `health` and `info` are exposed, so `/env`
is not reachable. The fix for this class is the exposure configuration, not a
version bump. `/actuator/health` is exposed in both states and is the readiness
check.

## Detection
`nuclei:springboot-actuator` is declared from its fingerprint but not yet run
against both states. Set `detection: scanner` once it fires on vulnerable and
stays silent on patched.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
