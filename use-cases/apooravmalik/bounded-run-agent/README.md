# Bounded Run Agent

Runs a multi-step DOCX editing request through SuperDocs with an explicit operation/deadline bound. A task is complete only after its SuperDocs job completes after approval.

```bash
export SUPERDOCS_API_KEY=your-key-here
python3 main.py --file /path/to/project-report.docx --request "Rewrite the executive summary; fix tone; add risks; improve conclusion" --max-operations 3 --auto-approve-demo
python3 -m unittest discover -s tests -v
```

`--auto-approve-demo` is explicit; otherwise each proposed edit asks for terminal confirmation. Uses documented upload, async HITL edit, job polling, approval, and export endpoints.
