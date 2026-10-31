# Evidence layout

Candidate patches, review records, plans, and source fingerprints are ordinary
text. Raw per-probe grading records are stored as `*-grade.json.gz` to keep the
review diff small. Decompression reproduces the exact original JSON bytes; hashes
in historical receipts refer to those uncompressed records and original paths.

`grading-records.json` maps each compressed file to its uncompressed SHA-256 and
byte count. No grading data was discarded or summarized in place of the raw logs.

On your Ubuntu machine, from the repository root, inspect one record with:

```bash
python3 -c 'import gzip; print(gzip.open("experiments/openspec-pilot/evidence/final/project-check-a-grade.json.gz", "rt").read())'
```

`initial/` retains the first evaluator and command receipts. `final/` retains the
separate source-bound validation against the fixed original snapshot and the
integrated draft. The final pass is a deterministic regrade, not another model
attempt. The separate review records identify additional defects outside the
bounded probe set and the later integrated corrections.
