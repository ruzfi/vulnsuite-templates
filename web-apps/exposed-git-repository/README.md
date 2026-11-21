# exposed-git-repository

> Config-axis target: one nginx image with the same deployed `.git/` directory
> in both states; the states differ only by the server config.

## Design
A site deployed with its working copy leaves `.git/` under the document root.
`files/common/git/` is a real, minimal repository: `HEAD`, `refs/heads/main`,
`config` (whose `origin` URL embeds a deploy token) and the three loose objects
of one commit (commit → tree → blob `app.py`, which holds a database password).
Anyone who can fetch these files can rebuild the source, the way `git-dumper`
and similar tools do. The objects were written by hand (zlib-compressed
`<type> <size>\0<body>`, named by their SHA-1) so the repository is byte-for-byte
reproducible.

Vulnerable is nginx with nothing in front of `.git/`. Patched adds the usual
fix, `location ~ /\.git { deny all; }`; the repository is still on disk, so
the patched state is safe only because of the config.

## Verification

| request | vulnerable | patched |
| --- | --- | --- |
| `GET /.git/HEAD` | 200, `ref: refs/heads/main` | 403 `403 Forbidden`, no `refs/heads` |
| `GET /.git/refs/heads/main` | 200, the commit id `cea9abac…` | (not probed) |
| `GET /.git/objects/b4/5b9037…` (the `app.py` blob) | 200, the 270-byte loose object | 403 `403 Forbidden` |
| `GET /.git/config` | 200, the remote URL with the leaked `deploy-token:s3cr3t@` credential | 403 `403 Forbidden`, no `deploy-token` |

Together the vulnerable probes walk HEAD → ref → loose object, which is what a
source rebuild needs, and assert the leaked credential rather than a generic
config key. The patched assertions are positive (nginx's 403 page). Rebuilding
`app.py` from the vulnerable state over HTTP (fetch, inflate, follow commit →
tree → blob) was checked by hand on 2026-11-21.

## Detection
`nuclei:git-config` fires on the vulnerable state (extracting
`deploy-token:s3cr3t`) and stays silent on the patched one (2026-11-21).

<!-- No CVE facts, severity, or version boundaries here — see contract.yaml metadata. -->
