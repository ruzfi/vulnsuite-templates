# spring-boot-jolokia-exposure

> Config-axis target sharing the actuator exposure toggle
> (`MANAGEMENT_ENDPOINTS_WEB_EXPOSURE_INCLUDE`) with
> `spring-boot-actuator-env-exposure`, but demonstrating the stronger Jolokia/JMX
> surface.

## Design
Vulnerable exposes every actuator endpoint, including Jolokia. Patched is the
secure default (only `health` and `info`), so Jolokia is not reachable over
HTTP.

## Verification
The vulnerable probe reads a harmless MBean. That proves the HTTP-to-JMX bridge
is reachable without invoking any write or exec gadget.

## Detection
`nuclei:jolokia-info-disclosure` is declared from its fingerprint but not yet
run against both states. Set `detection: scanner` once it fires on vulnerable
and stays silent on patched.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
