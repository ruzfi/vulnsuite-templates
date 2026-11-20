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
`nuclei:springboot-env` fires on the vulnerable state and stays silent on the
patched one (2026-11-21).

`nuclei:springboot-actuator` was declared before and is not a detector for
this finding: it is a technology fingerprint that lists whatever actuator
endpoints exist, and the patched state still exposes `health` and `info`, so it
fires on both states.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
