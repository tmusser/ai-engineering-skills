Output assets/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 920
Set Height 620
Set TypingSpeed 20ms

Type "clear"
Enter
Sleep 400ms

Type "echo 'ai-engineering-skills sanitized terminal demo'"
Enter
Sleep 500ms

Type "rm -rf /tmp/ai-engineering-skills-demo && mkdir -p /tmp/ai-engineering-skills-demo"
Enter
Sleep 400ms

Type "cp demo/sample-data/customers.csv /tmp/ai-engineering-skills-demo/customers.csv"
Enter
Sleep 400ms

Type "cd /tmp/ai-engineering-skills-demo"
Enter
Sleep 400ms

Type "echo 'Toy project: build a tiny CSV-to-Markdown summary CLI'"
Enter
Sleep 700ms

Type "echo 'Claude Code skills available: /mini-spec /thin-plan /scope-freeze /build-one /verify-contract /handoff'"
Enter
Sleep 900ms

Type "printf '%s\n' '# Spec' '' '## Objective' 'Build a tiny CLI that reads customers.csv and writes SUMMARY.md.' '' '## Acceptance criteria' '- Count CSV rows.' '- List column names.' '- Count missing values by column.' '- Show one example row.' '' '## Verification demo' 'Run python summarize_csv.py customers.csv SUMMARY.md and inspect SUMMARY.md.' > SPEC.md"
Enter
Sleep 700ms

Type "echo '/mini-spec -> wrote SPEC.md'"
Enter
Sleep 500ms

Type "sed -n '1,16p' SPEC.md"
Enter
Sleep 1200ms

Type "printf '%s\n' '# Plan' '' '## Implementation slices' '1. Parse CSV and count rows.' '2. Add missing-value counts.' '3. Write Markdown summary.' '' '## Verification strategy' 'Use the fake customers.csv fixture and inspect SUMMARY.md.' > PLAN.md"
Enter
Sleep 600ms

Type "echo '/thin-plan -> wrote PLAN.md'"
Enter
Sleep 500ms

Type "cat PLAN.md"
Enter
Sleep 1200ms

Type "printf '%s\n' '/scope-freeze' 'Allowed files: summarize_csv.py, SUMMARY.md, SPEC.md, PLAN.md, VERIFY.md, HANDOFF.md' 'Read-only files: customers.csv' 'Forbidden operations: network calls, external services, private data' 'Stop condition: one working CSV summary only'"
Enter
Sleep 1200ms

Type "cat > summarize_csv.py <<'PY'"
Enter
Type "import csv, sys"
Enter
Type "source, target = sys.argv[1], sys.argv[2]"
Enter
Type "with open(source, newline='') as f:"
Enter
Type "    rows = list(csv.DictReader(f))"
Enter
Type "fields = list(rows[0].keys()) if rows else []"
Enter
Type "missing = {field: sum(1 for row in rows if row.get(field, '') == '') for field in fields}"
Enter
Type "with open(target, 'w') as f:"
Enter
Type "    f.write('# CSV Summary\\n\\n')"
Enter
Type "    f.write(f'- Rows: {len(rows)}\\n')"
Enter
Type "    f.write('- Columns: ' + ', '.join(fields) + '\\n')"
Enter
Type "    f.write('- Missing values: ' + ', '.join(f'{k}={v}' for k, v in missing.items()) + '\\n')"
Enter
Type "    f.write(f'- Example row: {rows[0] if rows else {}}\\n')"
Enter
Type "PY"
Enter
Sleep 700ms

Type "python summarize_csv.py customers.csv SUMMARY.md"
Enter
Sleep 500ms

Type "echo '/build-one -> wrote SUMMARY.md'"
Enter
Sleep 500ms

Type "cat SUMMARY.md"
Enter
Sleep 1400ms

Type "printf '%s\n' '# Verify' '' '## Verification' '- Command: python summarize_csv.py customers.csv SUMMARY.md' '- Result: pass' '- Evidence: SUMMARY.md contains row count, columns, missing values, and one example row.' '- Remaining risk: no argument validation yet.' > VERIFY.md"
Enter
Sleep 700ms

Type "echo '/verify-contract -> wrote VERIFY.md'"
Enter
Sleep 500ms

Type "cat VERIFY.md"
Enter
Sleep 1200ms

Type "printf '%s\n' '# Handoff' '' '## Current status' 'One toy CSV summary slice is complete.' '' '## Changed files' '- summarize_csv.py' '- SUMMARY.md' '- SPEC.md' '- PLAN.md' '- VERIFY.md' '' '## Next recommended task' 'Add CLI argument validation if this were a real project.' > HANDOFF.md"
Enter
Sleep 700ms

Type "echo '/handoff -> wrote HANDOFF.md'"
Enter
Sleep 500ms

Type "cat HANDOFF.md"
Enter
Sleep 1500ms

Type "echo 'Demo complete. All files are synthetic and live under /tmp/ai-engineering-skills-demo.'"
Enter
Sleep 1200ms
