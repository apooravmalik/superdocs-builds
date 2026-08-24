# Bounded Run Agent

Runs a multi-step DOCX editing request through SuperDocs with an explicit operation/deadline bound. A task is complete only after its SuperDocs job completes after approval.

```bash
export SUPERDOCS_API_KEY=your-key-here
python3 main.py --file /path/to/project-report.docx --resource policy.md --request "Rewrite the executive summary; fix tone; add risks; improve conclusion" --max-operations 3
python3 -m unittest discover -s tests -v
```

`--resource` accepts a repeatable `.docx`, `.md`, or `.txt` reference. Before every edit, the CLI prints SuperDocs' proposed diffs and asks for terminal confirmation. `--auto-approve-demo` is only for demos. Uses documented upload, async HITL edit, job polling, approval, and export endpoints.
