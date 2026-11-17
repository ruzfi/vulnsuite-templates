# graphql-introspection-enabled

> Config-axis target: a genuine Apollo GraphQL server; the same image serves
> both states, differing only by the `INTROSPECTION` env var.

## Design
The flaw is purely configuration: introspection defaults to off in production
but is often left on. The vulnerable state enables it; the patched state is the
secure default, so a `__schema` query is refused. (This target replaced an
earlier simulated stand-in.)

Apollo Server's built-in health endpoint (`/.well-known/apollo/server-health`)
answers 200 in both states and is the readiness check.

## Detection
`custom-only`: no upstream nuclei template tells introspection-on from -off
(schema detectors fire on both), so the introspection query itself is the
discriminator.

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
