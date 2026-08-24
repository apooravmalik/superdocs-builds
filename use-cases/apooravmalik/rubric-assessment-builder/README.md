# Rubric + Assessment Builder

Builds a structured assessment and a deterministic matching rubric before any document is created. Each generated question ID has exactly one rubric row with identical marks.

```bash
export SUPERDOCS_API_KEY=your-key-here
python3 main.py --topic Photosynthesis --grade 8 --questions 5 --total-marks 25 --auto-approve-demo
python3 -m unittest discover -s tests -v
```

The use case renders one combined **Assessment and Rubric** document: this keeps the review/export flow atomic while preserving visible `Qn ↔ Qn` alignment. It creates the exact HTML in a SuperDocs session, asks for explicit user review before finalization unless demo approval is selected, then exports DOCX.
