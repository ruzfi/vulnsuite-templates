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
`nuclei:jolokia-info-disclosure` fires on the vulnerable state and stays silent
on the patched one (2026-11-21).

The probes assert `HeapMemoryUsage`, a value only a real MBean read returns.
They used to match `java.lang:type=Memory`, which is the requested path itself:
Jolokia echoes it in the response, and so does Spring's JSON 404 body on the
patched state, so the patched assertion depended on the client being served
the HTML error page.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
