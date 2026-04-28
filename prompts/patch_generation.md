Create a unified diff patch for this task.

Rules:
- Return only the diff.
- Use repository-relative paths.
- Keep the patch scoped to the requested task.
- Preserve existing behavior unless the task asks to change it.
- Keep fallback behavior for gpt-oss-120B.
- Add or update tests only when practical within the provided files.

Task:
{{TASK}}
