# Race-condition UAF experiment for vulnsuite#98

Evidence for [ruzfi/vulnsuite#98](https://github.com/ruzfi/vulnsuite/issues/98), kept here because it is not a template. It contains no `contract.yaml`, so vulnsuite ignores it. Findings are in [REPORT.md](REPORT.md).

## Layout

- `Dockerfile`: the ASan nginx build from the issue comment. It adds a `PATCHES` build-arg and a writable `/var/log/asan` (mode 1777) for ASan logs.
- `Dockerfile.debug`: the same build with `--with-debug`, used only for diagnosis.
- `patches/`: the upstream fixes `e39708edc69a` (resolver) and `754fe68c2e0f` (mail).
- `harness/`:
  - drivers: `resolver_driver.py`, `mail_driver.py`, `common.py`
  - holding sidecars: `fakedns.py`, `authstub.py`
  - nginx configs, plus `run_*.sh` and `matrix_*.sh`
- `harness/out/`: per-attempt logs, the result matrices and full ASan reports from the run.

## Reproduce

```sh
git clone https://github.com/nginx/nginx && cd nginx && git checkout 140aa942711868a8daeb95810bc9a81f272ada72
mkdir _patches && cp <this dir>/patches/*.patch _patches/
docker build -f <this dir>/Dockerfile -t uaf98-ngx:vuln .
docker build -f <this dir>/Dockerfile --build-arg PATCHES=resolver -t uaf98-ngx:fix-resolver .
docker build -f <this dir>/Dockerfile --build-arg PATCHES=mail     -t uaf98-ngx:fix-mail .
cd <this dir>/harness && ./matrix_resolver.sh && ./matrix_mail.sh
```

Tested on OrbStack, linux/arm64, with `worker_processes 1`.
