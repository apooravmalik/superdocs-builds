# Bounded Run Agent

Edits a DOCX through SuperDocs with a fixed operation budget and optional deadline. Every proposed change is shown in the terminal before it can be applied.

## Setup

```bash
cd use-cases/apooravmalik/bounded-run-agent
cp .env.example .env
# Edit .env and set SUPERDOCS_API_KEY
```

## Run interactively

The CLI asks for the DOCX path, editing request, and maximum operations. It then shows each proposed before/after change and waits for `y` or `n`.

```bash
python3 main.py
```

## Run with arguments

```bash
python3 main.py \
  --file /path/to/project-report.docx \
  --resource /path/to/policy.md \
  --resource /path/to/source-notes.docx \
  --request "Rewrite the executive summary; clarify project risks" \
  --max-operations 2 \
  --deadline-seconds 120 \
  --output output/edited-report.docx
```

`--resource` is optional and repeatable. It accepts `.docx`, `.md`, and `.txt` reference files. Their text is included with each edit instruction.

The default review looks like this:

```text
Review T1 · Rewrite the executive summary
1. Edit in document section
   − Existing wording
   + Proposed wording
   Why: Concise explanation
Apply 1 proposed change(s)? [y/N]
```

Use `--auto-approve-demo` only for non-interactive demos; it bypasses that review prompt.

## Check it locally

```bash
python3 -m unittest discover -s tests -v
python3 main.py --help
```

The run summary reports completed, rejected, failed, and unattempted tasks separately. An export failure is also reported separately from edit completion.
