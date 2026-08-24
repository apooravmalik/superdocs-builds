# Rubric + Assessment Builder

Builds a structured assessment and a deterministic matching rubric before any document is created. Each generated question ID has exactly one rubric row with identical marks.

```bash
export SUPERDOCS_API_KEY=your-key-here
python3 main.py --topic Photosynthesis --grade 8 --questions 5 --total-marks 25
python3 -m unittest discover -s tests -v
```

The CLI prints the complete question/rubric package before asking for confirmation. Use `--preview-only` to inspect without calling SuperDocs, or `--auto-approve-demo` only for demos. The use case renders one combined **Assessment and Rubric** document, keeping the review/export flow atomic while preserving visible `Qn ↔ Qn` alignment.
