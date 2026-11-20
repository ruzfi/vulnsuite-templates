# openproject-17.9.7-ghsa-34m4-m9fh-gqp5

OpenProject 17.9.7 (official slim image, bundled Ruby 4.0.9) - an unauthenticated multipart `_method` field makes `String#upcase` write one byte past a heap buffer ("Ruby2Shell").

- CVE: none assigned yet (requested, pending) - tracked as GHSA-34m4-m9fh-gqp5      - CWE: CWE-193, CWE-122
- Severity: critical
- Affected: OpenProject images up to 17.9.7 (bundled Ruby 4.0.0-4.0.9) - Fixed: 17.9.8 (bundled Ruby 4.0.10)

OpenProject's container image ships its own Ruby, so the image an operator pulls decides whether the instance is exposed. In 17.9.7 that runtime is Ruby 4.0.9. Its case mapping for the single-byte ISO-8859-x and Windows-125x encodings turns the sharp s (`0xDF`) into two bytes (`SS`) but only checks for one byte of room, so upcasing 21 or more `ß` writes one byte past the heap buffer. OpenProject is a full Rails app (Rack 2.2), so `Rack::MethodOverride` upcases the `_method` form field of every `POST`, and Rack's multipart parser tags a `text/plain` part with the charset the part declares. One anonymous request therefore reaches the overflow before routing or authentication runs. The 17.9.8 image bundles Ruby 4.0.10. Its release notes list only OpenProject's own advisories, not the Ruby update; Veria Labs lists 17.9.8 as fixed.

## References
- [Ruby advisory GHSA-34m4-m9fh-gqp5](https://github.com/ruby/ruby/security/advisories/GHSA-34m4-m9fh-gqp5)
- [OpenProject 17.9.8 release notes](https://www.openproject.org/docs/release-notes/17-9-8/)
- [Fix: ruby/ruby#20005](https://github.com/ruby/ruby/pull/20005)
- [Writeup: Ruby2Shell (Veria Labs), with the bundled-Ruby table](https://verialabs.com/ruby2shell/)

No NVD link: no CVE id has been assigned yet.

## Design
- `src/Dockerfile` starts `FROM openproject/openproject:17.9.7-slim` (pinned by digest) and adds only nginx plus the two `vulnsuite/` scripts. OpenProject's code, gems, `config/puma.rb` (cluster mode, `preload_app!`), its `docker/prod/web` launcher and the bundled Ruby are untouched.
- The patched state overlays `files/patched/Dockerfile`, which changes only the `FROM` line to `17.9.8-slim` (pinned). That is the vendor's own fix release. Besides Ruby 4.0.10 it carries eight OpenProject advisories (authorization, cache leaks, SSRF), so the states differ by the whole vendor release, not by Ruby alone.
- Postgres 17 runs as a pinned sidecar. `vulnsuite/start` runs `rake db:migrate` first, as the compose stack's seeder does. The lab `SECRET_KEY_BASE` in `contract.yaml` is a throwaway value.
- nginx listens on 8080 and proxies to Puma on `127.0.0.1:3000`, standing in for the compose stack's `proxy` service. It always sends the configured host name as `Host`, because OpenProject's host allowlist rejects any other name. A real attacker just uses the instance's public name. `OPENPROJECT_HTTPS=false` keeps Rails from redirecting the plain-HTTP lab. Without the proxy, a crashed worker would only reset the connection.
- **Corruption detector, in both states.** On a stock heap the stray byte usually lands in allocator slack and nothing visible happens. `vulnsuite/start` therefore runs Puma with glibc's heap checker (`LD_PRELOAD=libc_malloc_debug.so.0`, `GLIBC_TUNABLES=glibc.malloc.check=3`). The image already leaves jemalloc off (`USE_JEMALLOC=false`). On the vulnerable runtime glibc aborts the worker when `mapping_buffer_free` frees the overflowed buffer, Puma's master starts a new worker, and nginx answers the dropped request with `502`. The patched runtime handles the same request normally (`422`, Rails' CSRF rejection of the anonymous `POST /login`).
- Puma's output, the glibc diagnostic and Ruby's `[BUG]` crash report go to `/tmp/puma.log`, which is also followed to the container log.

## Verification
`verify-ruby2shell` runs inside the container. It sends a multipart `POST /login` straight to Puma on port 3000, bypassing nginx. It sends the `Host` nginx would set. The `_method` part is `text/plain; charset=windows-1252` and holds 23 `ß`, so it uses a different encoding table, length and path from the scanner's request. The script then reads only the new part of the Puma log.
- **vulnerable** passes only if all of the following hold: the request got no response because the worker died; glibc reported `malloc_check_get_size: memory corruption`; Ruby's crash backtrace names `mapping_buffer_free` (string.c) and the sink `rack/method_override.rb:32` (Rack 2.2); and `/health_check` answers `200` again after Puma restarts the worker.
- **patched** passes only if the same request returns `422`, no corruption diagnostic or `mapping_buffer_free` frame appears, and `/health_check` returns `200`.

The probe proves heap corruption from an anonymous request and goes no further. It does not try code execution.

## Detection
The candidate `nuclei:ruby2shell-casemap-overflow` sends a control `_method` of 21 `à` (`0xE0`) and then 21 `ß` (`0xDF`), both multipart ISO-8859-1, to `/`. It matches when the control gets a normal Rails answer (`X-Request-Id`, `X-Runtime`) and the trigger gets a `502`-`504`. It is tagged `dos`, so run it with `-itags dos`. Expect false negatives against stock hosts that lack the glibc checker. `detection` is left unset until the template is upstream.

## Building / running notes
- The build runs `apt-get install nginx` on top of the vendor image, so the nginx package can drift between builds. It is the same in both states.
- First boot migrates an empty database and takes about a minute. The healthcheck allows 300 s.
- The vendor images are multi-arch (`linux/amd64`, `linux/arm64`). Tested on arm64.
- Refresh a digest with `docker buildx imagetools inspect openproject/openproject:17.9.7-slim`.
