## Target

<!-- The target id this adds or changes. -->
Target id:
CVE / advisory:

## Checklist

- [ ] `vulnsuite validate -t <id>` is clean — the base is **pinned**, no warnings under `-strict`.
- [ ] `vulnsuite run vulnerable -t <id>` verifies ok, and `vulnsuite run patched -t <id>` verifies ok (the flaw is gone).
- [ ] `vulnerable` and `patched` differ by the **minimum** that toggles the flaw.
- [ ] `verify` probes come from the advisory — reachability / disclosure / version, **not** a working weaponized exploit, and independent of the scanner's matcher.
- [ ] `metadata.detection` is set (`scanner` with `detected_by`, or `custom-only`); `references` link the advisory and the fix.
- [ ] Nothing points `base` at an image or source that does more than stand up the affected service.
