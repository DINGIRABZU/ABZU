# Registry Audit

This guide describes how to validate `logs/task_registry.jsonl` to keep the task log accurate.

## Validation Steps

1. **Check for duplicates**
   Run a duplicate scan on `task_id` values. Any output indicates a duplicate entry.
   ```bash
   jq -r '.task_id' ../logs/task_registry.jsonl | sort | uniq -d
   ```

2. **Verify chronological order**
   Ensure entries are sorted by their `timestamp` fields.
   ```bash
   jq -r '.timestamp' ../logs/task_registry.jsonl | awk 'NR==1{prev=$1;next}{if($1<prev){print NR":"$0};prev=$1}'
   ```
   The command should produce no output; any line number indicates misordered entries.

3. **Identify unresolved tasks**
   Entries should show a resolved status such as `merged`.
   ```bash
   jq -c 'select(.status != "merged")' ../logs/task_registry.jsonl
   ```
   Investigate and update any tasks returned by this query.

4. **Seventh task refinement**
   After six tasks, an automatic seventh task appears to refine `docs/The_Absolute_Protocol.md`. Log this refinement task in the registry as well.

## Maintenance Protocols

Follow the audit guidance in [The Absolute Protocol](The_Absolute_Protocol.md#maintenance-checklist) to align registry validation with repository maintenance practices.
