# validate-memory-record

Use `scripts/validate_memory_record.py` to validate a synthetic Engram memory record.

## Inputs

- Path to one JSON memory-record fixture.

## Preconditions

- The fixture must be synthetic.
- The fixture must not include private transcripts, local indexes, local paths, account IDs, or credentials.

## Verification

Run:

```bash
python3 scripts/validate_memory_record.py examples/memory-record.example.json
```

Expected output:

```text
ENGRAM_MEMORY_RECORD_OK
```

## Do not

- Add private memory exports to this public repo.
- Treat synthetic examples as operational memory.
- Publish local index databases or transcript stores.
