# Task 2 Progress

Last updated: 2026-08-25

## Status

Task 2A and Task 2B are implemented, locally tested, live-verified against SuperDocs, and pushed to the personal fork.

## Task 2A — Bounded Run Agent

Location: `use-cases/apooravmalik/bounded-run-agent/`

- [x] DOCX upload using a durable SuperDocs session.
- [x] Semicolon/newline task plan with a maximum-operation limit and optional deadline.
- [x] One edit job at a time, with terminal job verification.
- [x] Human review before changes are applied: readable before/after text, explanation, and `y/N` prompt.
- [x] Optional `.docx`, `.md`, and `.txt` reference resources via repeatable `--resource`.
- [x] Honest completed, failed, unattempted, stop-reason, and export reporting.
- [x] DOCX export after the run.
- [x] Live SuperDocs edit, approval, completion, and export verified.

## Task 2B — Rubric + Assessment Builder

Location: `use-cases/apooravmalik/rubric-assessment-builder/`

- [x] Structured `Q1`–`Qn` questions and matching rubric rows.
- [x] Validation for duplicate IDs, missing/extra rubric rows, mark mismatches, and incorrect totals.
- [x] Readable terminal assessment/rubric preview and confirmation.
- [x] `--preview-only` mode, which makes no SuperDocs request.
- [x] SuperDocs creation, terminal verification, and DOCX export.
- [x] Live five-question, 25-mark assessment export verified.

## Verification

- [x] 6 bounded-run-agent unit tests pass.
- [x] 5 rubric-assessment-builder unit tests pass.
- [x] CLI help and no-network assessment preview checked.
- [x] Generated DOCX outputs and local `.env` files are Git-ignored.

## Run commands

See the use-case READMEs for copy-paste setup and commands:

- `use-cases/apooravmalik/bounded-run-agent/README.md`
- `use-cases/apooravmalik/rubric-assessment-builder/README.md`

## Known limits

- Assessment question and rubric text are deterministic drafts and should be reviewed for subject-matter quality.
- The agent checks the deadline before each operation; it does not cancel a job that has already started.
- `--auto-approve-demo` intentionally bypasses review and is only for demos.

## Delivery

- Personal fork: <https://github.com/apooravmalik/superdocs-builds>
- Current commit before this progress file: `cd80b7a`
- Remaining external step: open a pull request from the personal fork to the upstream repository if submission requires one.
