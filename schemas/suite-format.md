# Suite file format

A **suite** is a named, shareable list of selectors that `vulnsuite` stands up in
one run. The suite *source* lives in this repo under `suites/`; vulnsuite core
(v0.2.1+) owns resolution. A suite named `<name>` is the file `suites/<name>.txt`,
reached from the CLI with the explicit `suite:` prefix:

```bash
vulnsuite run  -t suite:nightly              # stand up the nightly set
vulnsuite run  -t suite:nightly -variants    # expand every group member in it
vulnsuite build -f suites/nightly.txt        # same file as an ad-hoc -f list
```

The format is deliberately the **same line grammar** as an ad-hoc `-f` file, so a
suite is just a named `-f` file.

## Grammar

One **selector per line**. Blank lines and lines beginning with `#` are ignored.
Each remaining line is one of:

| Line | Resolves to | Example |
| --- | --- | --- |
| an **id** | that one target | `grafana-8.3.0-cve-2021-43798` |
| a **group handle** | the family primary (all members under `-variants`) | `php2shell` |
| a **category** | every target in that product/surface folder | `web-apps` |
| a **nested suite** | that suite's members (`suite:` prefix; cycles are broken) | `suite:misconfig-sweep` |
| a **filter line** (starts with `-`) | every target matching the filter(s) | `-class misconfig` |

Bare-selector precedence matches core: **exact id → exact group → category folder
→ unique substring.** A suite is reached only through the explicit `suite:`
prefix, never a bare handle.

### Filter lines

A filter line begins with `-` and uses the same filters as `vulnsuite list`:
`-class`, `-tag`, `-category`/`-product`, `-cve`/`-no-cve`, `-ref`, `-year`,
`-since`, `-fidelity`, `-kev`/`-no-kev`. Multiple filters **on one line AND**
(a target must match all of them). Separate lines **union (OR)**.

## Composition and ordering

Every line selects a set; the run stands up the **union of all lines**,
de-duplicated and order-stable (lines resolved top to bottom, targets within a
line by path). Overlapping lines never start the same target twice. `-variants`
passed on the command line propagates into every group handle, including those
reached through a nested suite.

## Conventions this repo follows

- **No CVE facts in a suite.** A suite references targets and groups by selector
  only; severity, versions and references live in each target's `contract.yaml`.
- **Description header.** The leading `#` comment block is the suite's
  human description; `scripts/gen_suites.py` reads it into `SUITES.md`. Start it
  with `# <name> — <one line>`.
- **Prefer durable selectors.** Reference a group handle or a filter over a long
  list of ids where you can, so the suite tracks the corpus as it grows.
- `SUITES.md` is generated from this directory by `scripts/gen_suites.py` and is
  never hand-edited; CI fails if it is stale.
