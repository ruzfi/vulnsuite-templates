# nginx-emudhra-compromised-ca-exposure

> Stock nginx serving HTTPS with a certificate chain through a compromised
> eMudhra intermediate; the fixed state serves the same site with a
> certificate from a clean CA.

## Design

Both states are the same image: `nginx:1.25-alpine` plus a static `tlscheck`
probe binary and the certificate fixtures. The only difference is the
`default.conf` that picks the certificate pair:

- **vulnerable** (`build/default.conf`): `compromised-chain.pem` =
  `leaf <- EM DV TLS CA - G3B` (the real intermediate, chaining to the real
  emSign Root TLS CA - G3; the leaf is minted with the intermediate's
  recoverable private key, which is exactly what makes the CA compromised).
- **patched** (`files/patched/default.conf`): `clean-chain.pem` =
  `leaf <- test intermediate <- test root`, the same chain shape from a CA
  whose key is not compromised.

This is the server-side half of the eMudhra incident: a host still presenting
a certificate from one of the eight revoked, distrusted intermediates. Whether
a *client* accepts such a chain is a separate, client-side flaw; for Go see
`web-apps/golang-1.27.2-cve-2026-111943-emudhra-compromised-ca`.

The fixtures are copies of the ones generated for that target
(`sidecars/upstream/gencerts.go`): `compromised-*` = `emudhra-*`,
`clean-*` = `control-*`, `clean-root.pem` = `build/certs/control-root.pem`.
The private keys are throwaway test keys.

## Verification

| probe | vulnerable | patched |
| --- | --- | --- |
| `GET /` over TLS (control: the site is up) | 200 `VS-PORTAL customer portal` | 200, same |
| exec `/app/tlscheck` | leaf signature verifies under a presented intermediate whose SPKI SHA-256 is a compromised eMudhra key (`ebed6475…`), and that intermediate verifies under emSign Root TLS CA - G3 | no compromised SPKI in the presented chain, and the chain `x509.Verify`s to the clean test root |

`tlscheck` dials `127.0.0.1:443` inside the container and checks the presented
chain cryptographically (signatures and SPKI hashes), independently of the
nuclei template, which matches issuer distinguished-name strings. The patched
assertion is positive: the presented chain must verify to the clean root.

## Detection

2026-11-21, nuclei `ssl/emudhra-compromised-ca.yaml` (`-silent -nc -duc`):
fires on vulnerable (`[emudhra-compromised-ca] [ssl] [critical] … ["EM DV TLS CA - G3B"]`),
silent on patched.

## Building / running notes

- Multi-arch bases; runs natively on arm64 and amd64.
- The fixture leaves carry `DNS:upstream` and `DNS:localhost` and are valid
  until 2036-11-01; regenerate with the generator named above if needed.
