# Rubric + Assessment Builder

Creates an assessment and matching rubric, then validates that every question ID has exactly one rubric row with matching marks before SuperDocs is called.

## Setup

```bash
cd use-cases/apooravmalik/rubric-assessment-builder
cp .env.example .env
# Edit .env and set SUPERDOCS_API_KEY
```

## Preview without creating a document

```bash
python3 main.py \
  --topic Photosynthesis \
  --grade 8 \
  --questions 5 \
  --total-marks 25 \
  --preview-only
```

This prints a readable `Q1`–`Q5` assessment and its matching rubric, with no SuperDocs API call.

## Create and export

```bash
python3 main.py \
  --topic Photosynthesis \
  --grade 8 \
  --questions 5 \
  --total-marks 25 \
  --output output/photosynthesis-assessment.docx
```

The CLI displays the full assessment and rubric, then asks for confirmation before creating the SuperDocs document and exporting the DOCX.

For an interactive prompt-driven run, omit the required values:

```bash
python3 main.py
```

Use `--auto-approve-demo` only for non-interactive demos; it bypasses confirmation.

## Check it locally

```bash
python3 -m unittest discover -s tests -v
python3 main.py --help
```

Invalid packages are not exported: duplicate question IDs, missing rubric rows, mismatched marks, and incorrect totals all stop the workflow before SuperDocs is called.
