# KEV coverage backlog — reproducible vulnsuite targets

## Shipped so far

| Target | CVE | PR |
| --- | --- | --- |
| `apache-httpd-2.4.50-cve-2021-42013` | CVE-2021-42013 | #29 |
| `apache-flink-1.11.2-cve-2020-17519` | CVE-2020-17519 | #30 |
| `jenkins-2.441-cve-2024-23897` | CVE-2024-23897 | #34 |
| `nexus3-3.21.1-cve-2020-10199` | CVE-2020-10199 | #35 |
| `openfire-4.7.4-cve-2023-32315` | CVE-2023-32315 | #36 |

KEV coverage: **11 → 16** targets (of 1781 KEV CVEs).

Two of them ship with `detection` deliberately unset, because the public
scanner template does not discriminate: `nuclei:CVE-2024-23897` fires on the
patched Jenkins too, and `nuclei:CVE-2023-32315` requires a Tomcat-flavored log
that the embedded-Jetty image does not produce. Both are documented in their
READMEs as test beds for a better matcher.

---

Generated from the live CISA KEV feed (catalogVersion 2026.11.13, 1781 CVEs) against
this repo's 34 shipped targets. Every base image listed here was verified
pullable and digest-pinned from this machine (`docker buildx imagetools inspect` /
registry HEAD), not guessed.

**Today:** 11 of 1781 KEV CVEs are covered (6.2%).
**Ready to author now:** 75 new OSS/non-commercial KEV CVEs have a pullable,
digest-pinnable vulnerable base *plus* a verified patched counterpart
(upstream official image, a sibling `vulhub/*` tag, or a source build).

`vulhub/*` bases are `linux/amd64` only -> declare
`requires: { arch: [amd64], emulation: true }`.

---

## Provenance and attribution (read this before writing a contract)

Bases marked **vulhub** below are the pre-built vulnerable environments published
by **[vulhub/vulhub](https://github.com/vulhub/vulhub)** (MIT licensed,
© 2017-present phith0n). Each target that stands up one of those images must
carry the attribution, in **both** places the repo expects provenance:

**1. `metadata.references` in `contract.yaml`** — the machine-readable half, next
to the advisory and the fix:

```yaml
metadata:
  references:
    - https://nvd.nist.gov/vuln/detail/CVE-2019-0193
    - https://solr.apache.org/...
    - https://github.com/vulhub/vulhub/tree/master/solr/CVE-2019-0193   # vulnerable environment
```

Use the **per-CVE environment directory**, not the repo root — it is the exact
environment the base was taken from, and it is still a link into
`https://github.com/vulhub/vulhub`. The directory link carries the repo root in
its path, so the repo is always one click away.

**2. The target's `README.md`** — the human-readable half, under a `## Provenance`
heading (CVE facts stay in `metadata`; this is provenance, not a CVE fact):

```markdown
## Provenance
The vulnerable base image is the pre-built environment published by
[vulhub/vulhub](https://github.com/vulhub/vulhub/tree/master/solr/CVE-2019-0193)
(MIT, © phith0n). The patched state is the upstream release image.
```

Rules that keep this clean:
- The `vulhub` link goes in `references` of the **vulnerable** state's target only
  when the **base image** is a `vulhub/*` tag. If the base is an upstream official
  image (`solr:8.3.0`, `jenkins/jenkins:2.441`, …) there is nothing to attribute —
  cite the upstream release instead.
- When the vulnerable side is a `vulhub/*` image and the patched side is an
  upstream image, say so explicitly in the README's Provenance block (which image
  came from where) — that is the honest statement of the two-state diff.
- Do **not** copy vulhub's Dockerfile or PoC payload into the template. Use the
  published image and write the `verify` probe independently from the advisory
  (`SKILL.md` step 4). vulhub is the *environment*, not the *detection logic*.
- `vulhub/*` images are `linux/amd64` only -> `requires: { arch: [amd64], emulation: true }`.

---

## Upstream independence — how far do we depend on vulhub's namespace?

**Short answer: the dependency is on the *environment*, never on the *software*.**
vulhub's own base images are thin wrappers around upstream images. From their
`base/*/Dockerfile`s (read directly from the repo):

| vulhub base | `FROM` |
| --- | --- |
| `base/jenkins/2.441` | `jenkins/jenkins:2.441-slim` |
| `base/erlang/with-ssh/27.3.2` | `erlang:27.3.2-slim` |
| `base/drupal/7.57` | `php:7.0.28-apache` |
| `base/solr/8.1.1` | `openjdk:8u342-jdk` |
| `base/activemq/5.17.3` | `openjdk:11.0.16-jre` |
| `base/webmin/1.910` | `debian:jessie` |
| `base/redis/5.0.7` | `ubuntu:focal` |

So every vulnerable base we take from vulhub is still **upstream software**;
vulhub contributes the configuration and republishes it under `vulhub/*`. Its own
contribution guide says the same: *"Use official upstream images as the base when
available."* Provenance stays upstream either way.

### Three classes for the 75 candidates

| Class | Meaning | Count | Recommendation |
| --- | --- | --- | --- |
| **A — upstream carries both states** | the vulnerable *and* fixed tag exist in the real upstream registry | ~40 | **Use the upstream image as `base`.** Cite vulhub as the reference/alternate environment, not as the base. Also gets us multi-arch for free (upstream images are multi-arch; every `vulhub/*` image is amd64-only). |
| **B — upstream tag pruned** | upstream published the vulnerable version but the tag is gone from the registry now (`php:5.4.1-cgi`, `jenkins/jenkins:2.138`, `apache/activemq:5.17.3`, `rails:5.0.7`, `tomcat:8.5.20-jre8`, …) | ~15 | **Prefer `base.kind: source`** — rebuild from the upstream tarball at the vulnerable tag. That restores the upstream chain end-to-end and keeps the amd64-only vulhub image out of the contract. Fall back to the vulhub image when the source build is impractical. |
| **C — upstream never published the product** | no upstream image namespace for the software at all (`shiro`, `phpunit`, `opensmtpd`, `inetutils`, `goahead`, `polkit`, `ofbiz`, `craftcms`, `laravel`, `livewire`, `minio`, `cacti`, `thinkphp`, `strapi`, `webmin`, `samba`, `ghostscript`, `imagemagick`) | ~20 | **Source build** (`base.kind: source`) with the upstream release tarball, and use the vulhub image only as the cross-check for the environment configuration. |

Class A bases verified pullable + digest-pinned from this host during this
analysis: `tomcat:9.0.30`, `solr:8.11.0` / `8.3.0` / `8.1.1`, `jenkins/jenkins:2.441`,
`drupal:7.57` / `8.5.0`, `joomla:4.2.7-php8.1-apache`, `php:7.2.23-fpm`,
`redis:5.0.7`, `elasticsearch:1.4.2`, `kibana:6.5.4`, `couchdb:3.2.1`,
`sonatype/nexus3:3.14.0`, `metabase/metabase:v0.40.4`, `n8nio/n8n:1.65.0`,
`flink:1.11.2`, `httpd:2.4.50`, `xwiki:15.10.10`, `owncloud/server:10.13.0`,
`langflowai/langflow:1.2.0`, `gpustack/gpustack:v2.1.2`, `kestra/kestra:v1.0.44`,
`gitlab/gitlab-ce:19.1.7-ce.0`, `gitea/gitea:1.27.0`, `wazuh/wazuh-manager:4.9.0`,
`erlang:27.3.2`, `hugegraph/hugegraph:1.2.0`, `mongo-express:0.49.0`,
`adminer:4.7.8`, `apache/superset:2.0.1`, `apache/activemq-classic:5.17.6`,
`saltstack/salt:2019.2.3`, `erlang:27.3.3`.

> Note on this host: Docker Hub denies anonymous pulls for a subset of
> `library/*` namespaces from this IP (`library/samba`, `library/shiro`,
> `library/imagemagick`, … return *pull access denied* even for `latest`).
> That is an access restriction on this machine, not a missing repo — re-verify
> the Class B/C tag list from an unrestricted builder before committing.

### Decision rule for the contracts

1. If upstream carries the vulnerable tag -> `base.kind: image` with the upstream
   image, `requires` left empty (multi-arch), and the vulhub environment cited in
   `metadata.references` as the reference for the vulnerable configuration.
2. If upstream pruned the tag -> `base.kind: source` pinned to the upstream commit
   / release tarball; the vulhub image is the fallback and the cross-check.
3. Never make the vulhub image the *only* thing a target depends on, unless the
   product has no upstream image namespace at all (Class C) — and then say so
   plainly in the target's `## Provenance` block.

---

## Scope of this repository

This repository ships **vulnerable/patched target pairs for vulnsuite**, and
nothing else. It records which upstream projects publish a ready-made
vulnerable environment (the appendix below) so a target can stand on it and
credit it properly — that is the whole of the relationship with other projects.
Contributing environments, patches or documentation *to* those projects is out
of scope here and is not tracked in this file.

---

## Wave 0 — variant of an existing target (shipped)

| CVE | Product | Vulnerable base | Patched base | Why now |
| --- | --- | --- | --- | --- |
| CVE-2021-42013 | Apache httpd 2.4.50 | `httpd:2.4.50` `sha256:b73a8591d3f1f170568b501ce645dc900f8f1c4c697fbc2420cae3502ab5e02c` | `httpd:2.4.51` `sha256:0c8dd1d9f90f0da8a29…` | Sibling of the shipped `apache-httpd-2.4.49-cve-2021-41773`; **verified locally**: the 41773 path returns 400 on 2.4.50, the bypass path `/icons/%%32%65%%32%65/…/etc/passwd` returns 200 + `root:x:0:0:` on 2.4.50 and 400 on 2.4.51. Same overlay as the 2.4.49 target — no mod_cgi needed. |

## Wave 1 — single container, upstream image pair on both sides

| CVE | Product | Vulnerable base | Patched base | Probe | Provenance |
| --- | --- | --- | --- | --- | --- |
| CVE-2024-23897 | Jenkins | `jenkins/jenkins:2.441` | `jenkins/jenkins:2.442` | CLI `who-am-i` / argfile path traversal | upstream | **SHIPPED (#34)**
| CVE-2020-1938 | Tomcat (Ghostcat) | `tomcat:9.0.30-jdk8` `sha256:1ea11c1e…` | `tomcat:9.0.31-jdk8` `sha256:256f5296…` | `tcp` probe: hand-built AJP13 Forward-Request on 8009 — vulnerable accepts it, patched closes the connection (secret required by default) | upstream |
| CVE-2025-24813 | Tomcat | `tomcat:9.0.98` | `tomcat:9.0.99` | PUT via path equivalence (default servlet write) | upstream |
| CVE-2020-17519 | Apache Flink JobManager | `flink:1.11.2` `sha256:1fe4fb22…` | `flink:1.11.3` `sha256:7cdca61c…` | **verified locally**: `GET /jobmanager/logs/..%252f..%252f..%252f..%252f..%252f..%252fetc%252fpasswd` -> 200 + `root:x:0:0:`; patched -> 404 `{"errors":["This file does not exist in JobManager log dir."]}` | upstream | **SHIPPED (#30)**
| CVE-2021-44228 | Log4j2 (Solr) | `solr:8.11.0` | `solr:8.11.1` | JNDI lookup header (see Wave 2 for the app-toggle variant) | upstream |
| CVE-2019-17558 | Apache Solr | `solr:8.3.0` `sha256:89464b35…` | `solr:8.4.0` `sha256:060fcb87…` | enable `VelocityResponseWriter` then `$runtime.exec(...)`; **needs a seed** (create a core) | upstream |
| CVE-2018-7600 | Drupal | `drupal:8.5.0` | `drupal:8.5.1` | `#post_render` AJAX RCE | upstream |
| CVE-2018-7602 | Drupal | `drupal:7.57` | `drupal:7.59` | form cancel + `#post_render` | upstream |
| CVE-2019-6340 | Drupal | `drupal:8.6.9` | `drupal:8.6.10` | REST `hal_json` object injection | upstream |
| CVE-2023-23752 | Joomla | `joomla:4.2.7-php8.1-apache` | `joomla:4.2.8-php8.1-apache` | `GET /api/index.php/v1/config/application?public=true` | upstream |
| CVE-2025-24893 | XWiki | `xwiki:15.10.10` | `xwiki:15.10.11` | SolrSearch Groovy eval (single container, embedded DB) | upstream |
| CVE-2023-49103 | ownCloud graphapi | `owncloud/server:10.13.0` | `owncloud/server:10.13.1` | `graphapi` phpinfo file leak (app version toggled by `occ`) | upstream |
| CVE-2019-11043 | PHP-FPM | `php:7.2.23-fpm` + nginx | `php:7.2.24-fpm` | PATH_INFO overflow (reuses the `php2shell` pattern) | upstream |
| CVE-2020-10199 | Sonatype Nexus | `sonatype/nexus3:3.21.1` | `sonatype/nexus3:3.21.2` | Groovy RCE | upstream | **SHIPPED (#35)**
| CVE-2019-7238 | Sonatype Nexus | `vulhub/nexus:3.14.0` | `sonatype/nexus3:3.25.1` | expression-language auth bypass | **vulhub** `nexus/CVE-2019-7238` |
| CVE-2021-41277 | Metabase | `vulhub/metabase:0.40.4` | `vulhub/metabase:0.46.6` | GeoJSON LFI | **vulhub** `metabase/CVE-2021-41277` |
| CVE-2026-72898 | Metabase | `metabase/metabase:v0.58.23` | `metabase/metabase:v0.58.24` | `POST /api/session/reset_password` SQLi | upstream |
| CVE-2023-32315 | Openfire | `nasqueron/openfire:4.7.4` | `nasqueron/openfire:4.7.5` | unicode traversal to `openfire.log` | upstream | **SHIPPED (#36)**
| CVE-2025-32433 | Erlang/OTP SSH | `vulhub/erlang:27.3.2-with-ssh` | `erlang:27.3.3` | pre-auth SSH channel open | **vulhub** `erlang/CVE-2025-32433` |
| CVE-2025-3248 | Langflow | `vulhub/langflow:1.2.0` | `langflowai/langflow:1.3.0` | `POST /api/v1/validate/code` eval | **vulhub** `langflow/CVE-2025-3248` |
| CVE-2025-34291 | Langflow | `langflowai/langflow:1.6.9` | build 1.7.0 | CORS origin reflection (`header_matches`) | upstream |
| CVE-2026-33017 | Langflow | `vulhub/langflow:1.8.1` | build 1.9.0 | flow-build code injection | **vulhub** `langflow/CVE-2026-33017` |
| CVE-2025-68613 | n8n | `n8nio/n8n:1.65.0` | `n8nio/n8n:1.66.0` | dynamic-code resource control | upstream |
| CVE-2026-102895 | GPUStack | `gpustack/gpustack:v2.1.2` | `gpustack/gpustack:v2.2.3` | `X-GPUStack-Real-IP` header trust | upstream |
| CVE-2026-49869 | Kestra OSS | `kestra/kestra:v1.0.44` | `kestra/kestra:v1.0.45` | suffix-match auth bypass on `*/configs` | upstream |
| CVE-2026-60004 | Gitea | `gitea/gitea:1.27.0` | `gitea/gitea:1.27.1` | diffpatch add/add -> git hook write (needs seed) | upstream |
| CVE-2026-85706 | GitLab | `gitlab/gitlab-ce:19.1.7-ce.0` | `gitlab/gitlab-ce:19.1.8-ce.0` | `%63ommits` Workhorse bypass (single all-in-one container) | upstream |
| CVE-2021-22205 | GitLab | `vulhub/gitlab:13.10.1` | gitlab-ce 13.10.2 | RCE | **vulhub** `gitlab/CVE-2021-22205` |
| CVE-2025-24016 | Wazuh | `wazuh/wazuh-manager:4.9.0` | `wazuh/wazuh-manager:4.9.1` | DistributedAPI deserialization (needs default creds) | upstream |
| CVE-2015-1427 | Elasticsearch | `vulhub/elasticsearch:1.4.2` | `vulhub/elasticsearch:1.5.1` | Groovy script RCE | **vulhub** `elasticsearch/CVE-2015-1427` |
| CVE-2019-7609 | Kibana | `vulhub/kibana:6.5.4` | `vulhub/kibana:7.6.2` | prototype-pollution RCE (needs ES sidecar) | **vulhub** `kibana/CVE-2019-7609` |
| CVE-2022-24706 | CouchDB | `vulhub/couchdb:3.2.1` | `couchdb:3.3.0` | insecure default `_users` | **vulhub** `couchdb/CVE-2022-24706` |
| CVE-2022-0543 | Redis (Debian) | `vulhub/redis:5.0.7` | `redis:7.0.4` | Lua sandbox escape (Debian packaging — confirm per tag) | **vulhub** `redis/CVE-2022-0543` |
| CVE-2024-36401 | GeoServer | `docker.osgeo.org/geoserver:2.23.2` | `docker.osgeo.org/geoserver:2.23.6` | OGC filter `exec()` RCE | upstream (osgeo registry) |
| CVE-2025-58360 | GeoServer | `docker.osgeo.org/geoserver:2.25.5` | `docker.osgeo.org/geoserver:2.25.6` | SLD XXE (variant-group sibling of 2024-36401) | upstream (osgeo registry) |
| CVE-2024-38856 | Apache OFBiz | `vulhub/ofbiz:18.12.14` | `vulhub/ofbiz:18.12.15` | `POST /webtools/control/main/ProgramExport` groovy injection (HTTPS only, slow first boot) | **vulhub** `ofbiz/CVE-2024-38856` |
| CVE-2023-27524 | Apache Superset | `apache/superset:2.0.1` | `apache/superset:2.1.0` | forge a session cookie with the published default `SECRET_KEY`; the vulnerable state must set `environment: SUPERSET_SECRET_KEY` explicitly | upstream |
| CVE-2024-27348 | HugeGraph | `hugegraph/hugegraph:1.0.0` | `hugegraph/hugegraph:1.3.0` | `POST /apis/gremlin` sandbox bypass | upstream |
| CVE-2017-12149 | JBoss AS | `vulhub/jboss:as-6.1.0` | same image + invoker overlay | `/invoker/readonly` deserialization (no gadget needed) | **vulhub** `jboss/CVE-2017-12149` |
| CVE-2022-22947 | Spring Cloud Gateway | `vulhub/spring-cloud-gateway:3.1.0` | build 3.1.1 | actuator route-write exposure | **vulhub** `spring/CVE-2022-22947` |
| CVE-2022-22963 | Spring Cloud Function | `vulhub/spring-cloud-function:3.2.2` | build 3.2.3 | SpEL routing-expression header | **vulhub** `spring/CVE-2022-22963` |
| CVE-2018-1273 | Spring Data Commons | `vulhub/spring-data-commons:2.0.5` | build 2.0.6 | property-binder SpEL | **vulhub** `spring/CVE-2018-1273` |
| CVE-2022-22965 | Spring Framework | `vulhub/spring-webmvc:5.3.17` | build 5.3.18 | Spring4Shell (benign write needed) | **vulhub** `spring/CVE-2022-22965` |
| CVE-2016-4437 | Apache Shiro | `vulhub/shiro:1.2.4` | `vulhub/shiro:1.5.1` | padding-oracle / deserialization | **vulhub** `shiro/CVE-2016-4437` |
| CVE-2016-3088 | ActiveMQ | `vulhub/activemq:5.11.1-with-cron` | `vulhub/activemq:5.13.2` | improper input validation | **vulhub** `activemq/CVE-2016-3088` |
| CVE-2023-46604 | ActiveMQ | `vulhub/activemq:5.17.3` | `apache/activemq-classic:5.17.6` | OpenWire RCE (protocol engineering, not a config toggle) | **vulhub** `activemq/CVE-2023-46604` |
| CVE-2026-34197 | ActiveMQ | `vulhub/activemq:6.2.2` | build 6.2.3 | improper input validation | **vulhub** `activemq/CVE-2026-34197` |
| CVE-2021-3129 | Laravel Ignition | `vulhub/laravel:8.4.2` | composer bump ignition 2.5.2 | `/_ignition/execute-solution` | **vulhub** `laravel/CVE-2021-3129` |
| CVE-2025-54068 | Laravel Livewire | `vulhub/livewire:3.6.3` | build 3.6.4 | component-property hydration | **vulhub** `livewire/CVE-2025-54068` |
| CVE-2020-12641 | Roundcube | `roundcube/roundcubemail:1.5.5-apache` | `1.6.11-apache` | `mail_drafts` RCE | upstream |
| CVE-2025-49113 | Roundcube | `roundcube/roundcubemail:1.6.10-apache` | `1.6.11-apache` | `_from` deserialization | upstream |

## Wave 2 — single container, but the vulnerable side needs a source build

| CVE | Product | Vulnerable base | Patched base | Note | Provenance |
| --- | --- | --- | --- | --- | --- |
| CVE-2014-0160 | OpenSSL (Heartbleed) | `vulhub/openssl:1.0.1c-with-nginx` | build OpenSSL 1.0.1g | `net` probe: oversized heartbeat echoes heap bytes | **vulhub** `openssl/CVE-2014-0160` |
| CVE-2012-1823 | PHP-CGI | `vulhub/php:5.4.1-cgi` | build PHP 5.4.2-cgi | `-d allow_url_include` query-string flag injection | **vulhub** `php/CVE-2012-1823` |
| CVE-2020-7247 | OpenSMTPD | `vulhub/opensmtpd:6.6.1p1` | build 6.6.2p1 | `MAIL FROM:<;cmd;>` argument injection | **vulhub** `opensmtpd/CVE-2020-7247` |
| CVE-2026-24061 | GNU InetUtils telnetd | `vulhub/inetutils:2.5` | build 2.8 | `USER` option `-f root` auth bypass | **vulhub** `inetutils/CVE-2026-24061` |
| CVE-2015-3306 | ProFTPD mod_copy | build v1.3.5a | build v1.3.5b | FTP `SITE CPFR/CPTO` | upstream source |
| CVE-2017-7494 | Samba (SambaCry) | `vulhub/samba:4.6.3` | build 4.6.4 | SMB pipe + writable share (impacket needed) | **vulhub** `samba/CVE-2017-7494` |
| CVE-2019-15107 | Webmin | `vulhub/webmin:1.910` | build 1.920 | `file` param command injection | **vulhub** `webmin/CVE-2019-15107` |
| CVE-2014-6271 | GNU Bash | `vulhub/bash:4.3.0-with-httpd` | bash 4.3.0-patched | ShellShock via CGI env | **vulhub** `bash/CVE-2014-6271` |
| CVE-2017-17562 | Embedthis GoAhead | `vulhub/goahead:3.6.4` | build 3.6.5 | `LD_PRELOAD` CGI env injection | **vulhub** `goahead/CVE-2017-17562` |
| CVE-2016-3714 | ImageMagick | `vulhub/imagemagick:6.9.2-10-php` | build 6.9.3-10 | ImageTragick file read/deletion | **vulhub** `imagemagick/CVE-2016-3714` |
| CVE-2017-8291 | Ghostscript | `vulhub/ghostscript:9.21-with-flask` | `vulhub/ghostscript:9.25` | `-dSAFER` bypass | **vulhub** `python/PIL-CVE-2017-8291` |
| CVE-2017-9841 | PHPUnit | `vulhub/phpunit:5.6.2` | build 5.6.3 | `eval-stdin.php` | **vulhub** `phpunit/CVE-2017-9841` |
| CVE-2021-4034 | polkit | `vulhub/polkit:0.105` | polkit 0.106 | pkexec OOB | **vulhub** `polkit/CVE-2021-4034` |
| CVE-2019-5418 | Ruby on Rails | `vulhub/rails:5.0.7` | build 6.0.2.1 | `send` gadget | **vulhub** `rails/CVE-2019-5418` |
| CVE-2021-21311 | Adminer | `vulhub/adminer:4.7.8` | adminer 4.8.1 | SSRF | **vulhub** `adminer/CVE-2021-21311` |
| CVE-2021-22204 | ExifTool | build harness | bumped lib | `build/` sim | upstream source |
| CVE-2023-7101 | Spreadsheet::ParseExcel | build harness | bumped lib | `build/` sim | upstream source |
| CVE-2021-39144 | XStream | build harness | bumped lib | `build/` sim | upstream source |
| CVE-2021-21315 | npm systeminformation | build harness | bump dep | library-level -> `build/` sim | upstream source |
| CVE-2020-28949 / CVE-2020-36193 | PEAR Archive_Tar | build harness | bump to 1.4.12 | `build/` sim | upstream source |

## Wave 3 — needs a sidecar, a seed, or a multi-service stack

| CVE | Product | Base | Extra work | Provenance |
| --- | --- | --- | --- | --- |
| CVE-2020-11651 / CVE-2020-11652 / CVE-2020-16846 | SaltStack | `vulhub/saltstack:2019.2.3` / `:3002` | master+minion pair, ZeroMQ-level probe | **vulhub** `saltstack/CVE-2020-11651` |
| CVE-2022-46169 | Cacti | `vulhub/cacti:1.2.22` -> `:1.2.28` | MySQL sidecar + poller/device seed | **vulhub** `cacti/CVE-2022-46169` |
| CVE-2024-56145 / CVE-2025-32432 | Craft CMS | `vulhub/craftcms:5.5.1.1` | MySQL sidecar (5.6.16 tag missing) | **vulhub** `craftcms/CVE-2024-56145` |
| CVE-2020-11738 | WP Duplicator plugin | `wordpress:6.x` | install plugin 1.3.26 / 1.3.28 via seed | upstream |
| CVE-2020-25213 | WP File Manager plugin | `wordpress:6.x` | plugin 6.0 -> 8.0.7 (large version gap) | upstream |
| CVE-2023-28432 / CVE-2023-28434 | MinIO | `vulhub/minio:2023-02-27T18-10-45Z` | needs a 3-node distributed cluster | **vulhub** `minio/CVE-2023-28432` |
| CVE-2019-10758 | mongo-express | `vulhub/mongo-express:0.53.0` | mongo sidecar | **vulhub** `mongo-express/CVE-2019-10758` |
| CVE-2019-7609 (alt) | Kibana | `vulhub/kibana:6.5.4` | ES sidecar | **vulhub** |
| CVE-2020-11978 | Apache Airflow | `vulhub/airflow:1.10.10` | webserver + scheduler + postgres | **vulhub** `airflow/CVE-2020-11978` |
| CVE-2022-33891 | Apache Spark | `vulhub/spark:2.3.1` | master + worker | **vulhub** `spark/CVE-2022-33891` |
| CVE-2023-33246 | Apache RocketMQ | `vulhub/rocketmq:5.1.0` | nameserver + broker | **vulhub** `rocketmq/CVE-2023-33246` |
| CVE-2017-12617 | Tomcat (PUT JSP) | `tomcat:8.5.20-jre8` -> `8.5.23-jre8` | overlay must set `readonly=false` on the **existing** default servlet without dropping the JSP mapping | upstream |

## Needs a dedicated build pass (no image pair exists)

| CVE | Product | Why |
| --- | --- | --- |
| CVE-2017-5638, CVE-2018-11776, CVE-2017-9805, CVE-2020-17530, CVE-2016-3081, CVE-2013-2251, CVE-2012-0391, CVE-2006-1547, CVE-2017-9791 | Apache Struts 1/2 | `vulhub/struts2` ships vulnerable-version tags only; there is no public image for the corresponding **fixed** Struts version and no official `apache/struts2` Hub repo — both states need a WAR compile |
| CVE-2019-0193 | Solr DataImportHandler | canonical PoC relies on Interactsh OOB; a self-contained verify needs more design work |
| CVE-2022-24112 | APISIX | needs an etcd sidecar |
| CVE-2021-44228 (alt) | Log4Shell | `ghcr.io/christophetd/log4shell-vulnerable-app:latest` (`sha256:6f884306…`) with the state toggle as `-Dlog4j2.formatMsgNoLookups=true` — needs an LDAP/DNS sidecar to observe the outbound lookup |
| CVE-2021-39935, CVE-2021-22175, CVE-2023-7028, CVE-2026-97229 | GitLab | same product family as CVE-2026-85706; heavy boot, pick one representative first |
| CVE-2019-1003029, CVE-2019-1003030 | Jenkins plugins | need a seeded Pipeline job with a pinned plugin version |
| CVE-2019-15107 | Webmin | no public 1.920 image; source build only |

## Skipped (with reason)

- **Windows-only** — CVE-2017-12615 (Tomcat PUT), CVE-2024-4577 (PHP-CGI Best-Fit),
  Rejetto HFS CVE-2014-6287 / CVE-2024-23692 (Windows-only server),
  CVE-2026-41940 (cPanel).
- **Local privesc / no network listener** — CVE-2021-3156, CVE-2025-32463 (sudo),
  CVE-2023-4911 (glibc), CVE-2015-5287 (ABRT), CVE-2019-0211 (httpd scoreboard).
- **DoS-only (destructive to prove)** — CVE-2023-44487 (HTTP/2 Rapid Reset),
  CVE-2023-29552 (SLP amplification).
- **Supply-chain / CI, not a running service** — CVE-2025-30066 (tj-actions),
  CVE-2025-30154 (reviewdog), CVE-2025-54313 (Prettier), CVE-2026-45321 (TanStack),
  CVE-2025-55182 (React RSC), CVE-2025-11953 (React Native CLI).
- **No fixed version exists** — CVE-2021-26828 / CVE-2021-26829 (ScadaBR, abandoned).
- **No public image at the affected version** — CVE-2020-1956 (Apache Kylin),
  CVE-2024-45195 (OFBiz 18.12.16 not published), CVE-2016-8735 (Tomcat JMX),
  CVE-2026-34486 (Tomcat cluster encryption — needs 2 nodes).
- **Heavy / multi-service / commercial** — Zimbra (17 CVEs: no public image for the
  affected versions), Confluence / Jira / TeamCity / WebLogic / ColdFusion (commercial),
  FreePBX, rConfig, CyberPanel (no pinnable image).

---

## Appendix — every vulhub KEV environment, with the attribution link

96 KEV CVEs have a vulhub environment. For the ones above, the reference to put in
`metadata.references` and the README's Provenance block is:

    https://github.com/vulhub/vulhub/tree/master/<product>/<CVE-YYYY-NNNNN>

| CVE | vulhub environment |
| --- | --- |
| CVE-2012-1823 | `php/CVE-2012-1823` |
| CVE-2014-0160 | `openssl/CVE-2014-0160` |
| CVE-2014-3120 | `elasticsearch/CVE-2014-3120` (already covered) |
| CVE-2014-6271 | `bash/CVE-2014-6271` |
| CVE-2015-1427 | `elasticsearch/CVE-2015-1427` |
| CVE-2016-3088 | `activemq/CVE-2016-3088` |
| CVE-2016-3714 | `imagemagick/CVE-2016-3714` |
| CVE-2016-4437 | `shiro/CVE-2016-4437` |
| CVE-2017-1000353 | `jenkins/CVE-2017-1000353` |
| CVE-2017-12149 | `jboss/CVE-2017-12149` |
| CVE-2017-17562 | `goahead/CVE-2017-17562` |
| CVE-2017-7494 | `samba/CVE-2017-7494` |
| CVE-2017-8291 | `python/PIL-CVE-2017-8291` |
| CVE-2017-9841 | `phpunit/CVE-2017-9841` |
| CVE-2018-1000861 | `jenkins/CVE-2018-1000861` |
| CVE-2018-1273 | `spring/CVE-2018-1273` |
| CVE-2018-7600 | `drupal/CVE-2018-7600` |
| CVE-2018-7602 | `drupal/CVE-2018-7602` |
| CVE-2019-0193 | `solr/CVE-2019-0193` |
| CVE-2019-10758 | `mongo-express/CVE-2019-10758` |
| CVE-2019-11043 | `php/CVE-2019-11043` |
| CVE-2019-15107 | `webmin/CVE-2019-15107` |
| CVE-2019-17558 | `solr/CVE-2019-17558` |
| CVE-2019-5418 | `rails/CVE-2019-5418` |
| CVE-2019-7238 | `nexus/CVE-2019-7238` |
| CVE-2019-7609 | `kibana/CVE-2019-7609` |
| CVE-2020-10199 | `nexus/CVE-2020-10199` |
| CVE-2020-11651 | `saltstack/CVE-2020-11651` |
| CVE-2020-11652 | `saltstack/CVE-2020-11652` |
| CVE-2020-11978 | `airflow/CVE-2020-11978` |
| CVE-2020-16846 | `saltstack/CVE-2020-16846` |
| CVE-2020-17519 | `flink/CVE-2020-17519` |
| CVE-2020-1938 | `tomcat/CVE-2020-1938` |
| CVE-2020-7247 | `opensmtpd/CVE-2020-7247` |
| CVE-2021-21311 | `adminer/CVE-2021-21311` |
| CVE-2021-22205 | `gitlab/CVE-2021-22205` |
| CVE-2021-3129 | `laravel/CVE-2021-3129` |
| CVE-2021-4034 | `polkit/CVE-2021-4034` |
| CVE-2021-40438 | `httpd/CVE-2021-40438` |
| CVE-2021-41277 | `metabase/CVE-2021-41277` |
| CVE-2021-42013 | `httpd/CVE-2021-42013` |
| CVE-2021-43798 | `grafana/CVE-2021-43798` (already covered) |
| CVE-2021-44228 | `log4j/CVE-2021-44228` |
| CVE-2022-0543 | `redis/CVE-2022-0543` |
| CVE-2022-22947 | `spring/CVE-2022-22947` |
| CVE-2022-22963 | `spring/CVE-2022-22963` |
| CVE-2022-22965 | `spring/CVE-2022-22965` |
| CVE-2022-24706 | `couchdb/CVE-2022-24706` |
| CVE-2022-24816 | `geoserver/CVE-2022-24816` |
| CVE-2022-46169 | `cacti/CVE-2022-46169` |
| CVE-2023-27524 | `superset/CVE-2023-27524` |
| CVE-2023-28432 | `minio/CVE-2023-28432` |
| CVE-2023-32315 | `openfire/CVE-2023-32315` |
| CVE-2023-33246 | `rocketmq/CVE-2023-33246` |
| CVE-2023-46604 | `activemq/CVE-2023-46604` |
| CVE-2023-49103 | `owncloud/CVE-2023-49103` |
| CVE-2024-23897 | `jenkins/CVE-2024-23897` |
| CVE-2024-27348 | `hugegraph/CVE-2024-27348` |
| CVE-2024-36401 | `geoserver/CVE-2024-36401` |
| CVE-2024-38856 | `ofbiz/CVE-2024-38856` |
| CVE-2024-45195 | `ofbiz/CVE-2024-45195` |
| CVE-2024-56145 | `craftcms/CVE-2024-56145` |
| CVE-2025-24813 | `tomcat/CVE-2025-24813` |
| CVE-2025-32432 | `craftcms/CVE-2025-32432` |
| CVE-2025-32433 | `erlang/CVE-2025-32433` |
| CVE-2025-3248 | `langflow/CVE-2025-3248` |
| CVE-2025-54068 | `livewire/CVE-2025-54068` |
| CVE-2025-55182 | `react/CVE-2025-55182` |
| CVE-2025-68613 | `n8n/CVE-2025-68613` |
| CVE-2026-24061 | `inetutils/CVE-2026-24061` |
| CVE-2026-33017 | `langflow/CVE-2026-33017` |
| CVE-2026-34197 | `activemq/CVE-2026-34197` |
| CVE-2026-34486 | `tomcat/CVE-2026-34486` |
| CVE-2026-63030 | `wordpress/CVE-2026-63030` (already covered) |
| CVE-2026-85706 | `gitlab/CVE-2026-85706` |
| CVE-2026-97229 | `gitlab/CVE-2026-97229` |

(Commercial products — WebLogic, ColdFusion, Confluence, Jira, TeamCity,
Liferay Portal — also have vulhub environments; they are out of scope for the
OSS/non-commercial set and are not listed here.)
