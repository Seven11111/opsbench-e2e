# Provenance Status

This snapshot intentionally records a limitation for expert review.

The two case manifests currently contain:

```text
source.evidence_bundle_id: dynamic_bundle_0001
source.evidence_refs: []
```

No API key is included. The package contains the case-level scenario, public
task, runtime implementation, verifier, and evaluation traces, but not the
original document corpus or exact evidence spans. It is therefore:

```text
runtime-validated: yes
document-provenance-complete: no
empirically-calibrated: no
```

This distinction is deliberate so reviewers can assess runtime correctness
separately from document-grounded generation quality.
