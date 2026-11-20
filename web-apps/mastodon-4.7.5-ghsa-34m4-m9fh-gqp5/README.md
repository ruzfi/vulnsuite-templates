# mastodon-4.7.5-ghsa-34m4-m9fh-gqp5

Mastodon 4.7.5 (official image, bundled Ruby 4.0.9) - an unauthenticated multipart `_method` field makes `String#upcase` write one byte past a heap buffer ("Ruby2Shell").

- CVE: none assigned yet (requested, pending) - tracked as GHSA-34m4-m9fh-gqp5      - CWE: CWE-193, CWE-122
- Severity: critical
- Affected: Mastodon images up to 4.7.5 (bundled Ruby 4.0.0-4.0.9) - Fixed: 4.7.6 (bundled Ruby 4.0.10)

Mastodon's container image ships its own Ruby, so the image an operator pulls decides whether the instance is exposed. In 4.7.5 that runtime is Ruby 4.0.9. Its case mapping for the single-byte ISO-8859-x and Windows-125x encodings turns the sharp s (`0xDF`) into two bytes (`SS`) but only checks for one byte of room, so upcasing 21 or more `ß` writes one byte past the heap buffer. Mastodon is a full Rails app, so `Rack::MethodOverride` upcases the `_method` form field of every `POST`, and Rack's multipart parser tags a `text/plain` part with the charset the part declares. One anonymous request therefore reaches the overflow before routing, authentication or Rack::Attack run. Mastodon 4.7.6 is the vendor's fix: its release notes call it a Ruby update for the Docker images that fixes "multiple critical security issues".

## References
- [Ruby advisory GHSA-34m4-m9fh-gqp5](https://github.com/ruby/ruby/security/advisories/GHSA-34m4-m9fh-gqp5)
- [Mastodon v4.7.6 release](https://github.com/mastodon/mastodon/releases/tag/v4.7.6)
- [Fix: ruby/ruby#20005](https://github.com/ruby/ruby/pull/20005)
- [Writeup: Ruby2Shell (Veria Labs), with the bundled-Ruby table](https://verialabs.com/ruby2shell/)

No NVD link: no CVE id has been assigned yet.

## Design
- `src/Dockerfile` starts `FROM ghcr.io/mastodon/mastodon:v4.7.5` (pinned by digest) and adds only nginx plus the two `vulnsuite/` scripts. Mastodon's own code, gems, `config/puma.rb` (cluster mode, 2 workers, `preload_app!`) and the bundled Ruby are untouched.
- The patched state overlays `files/patched/Dockerfile`, which changes only the `FROM` line to `v4.7.6` (pinned). That is the vendor's own fix release. Besides Ruby 4.0.10 it bumps `puma`, `rails`, `sanitize`, `msgpack` and `omniauth`, so the states differ by the whole vendor release, not by Ruby alone.
- Postgres 17 and Redis 7 run as pinned sidecars. `vulnsuite/start` runs `rails db:prepare` first, because Puma preloads the app and the app needs the schema at boot. The lab keys in `contract.yaml` are throwaway values.
- nginx listens on 8080 and proxies to Puma on `127.0.0.1:3000`, like Mastodon's documented setup minus TLS. It sends `X-Forwarded-Proto: https`, because Mastodon forces SSL. It also always sends the instance domain as `Host`, because Mastodon's host allowlist rejects any other name. A real attacker just uses the instance's public domain. Without the proxy, a crashed worker would only reset the connection.
- **Corruption detector, in both states.** On a stock heap the stray byte usually lands in allocator slack and nothing visible happens. `vulnsuite/start` therefore runs Puma with glibc's heap checker (`LD_PRELOAD=libc_malloc_debug.so.0`, `GLIBC_TUNABLES=glibc.malloc.check=3`). Mastodon's Ruby is linked against jemalloc, and the preload replaces it with glibc's checking allocator in both states. On the vulnerable runtime glibc aborts the worker when `mapping_buffer_free` frees the overflowed buffer, Puma's master starts a new worker, and nginx answers the dropped request with `502`. The patched runtime routes the same request normally (`404`).
- Puma's output, the glibc diagnostic and Ruby's `[BUG]` crash report go to `/tmp/puma.log`, which is also followed to the container log.

## Verification
`verify-ruby2shell` runs inside the container. It sends a multipart `POST /about` straight to Puma on port 3000, bypassing nginx. It sends the headers nginx would add. The `_method` part is `text/plain; charset=windows-1252` and holds 23 `ß`, so it uses a different encoding table and length from the scanner's request. The script then reads only the new part of the Puma log.
- **vulnerable** passes only if all of the following hold: the request got no response because the worker died; glibc reported `malloc_check_get_size: memory corruption`; Ruby's crash backtrace names `mapping_buffer_free` (string.c) and the sink `rack/method_override.rb:36`; and `/health` answers `200` again after Puma restarts the worker.
- **patched** passes only if the same request returns `404`, no corruption diagnostic or `mapping_buffer_free` frame appears, and `/health` returns `200`.

The probe proves heap corruption from an anonymous request and goes no further. It does not try code execution.

## Detection
The candidate `nuclei:ruby2shell-casemap-overflow` sends a control `_method` of 21 `à` (`0xE0`) and then 21 `ß` (`0xDF`), both multipart ISO-8859-1, to `/`. It matches when the control gets a normal Rails answer (`X-Request-Id`, `X-Runtime`) and the trigger gets a `502`-`504`. It is tagged `dos`, so run it with `-itags dos`. Expect false negatives against stock hosts that lack the glibc checker. `detection` is left unset until the template is upstream.

## Building / running notes
- The build runs `apt-get install nginx` on top of the vendor image, so the nginx package can drift between builds. It is the same in both states.
- First boot migrates an empty database and takes about a minute. The healthcheck allows 300 s.
- The vendor images are multi-arch (`linux/amd64`, `linux/arm64`). Tested on arm64.
- Refresh a digest with `docker buildx imagetools inspect ghcr.io/mastodon/mastodon:v4.7.5`.
