
<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools).

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and completion
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

## Committing Changes After Task Completion

When you complete a backlog task (marking it as "Done"):

1. **ALWAYS commit the changes** using git
2. **Include ALL changes**:
   - Source code files
   - Test files
   - Backlog folder changes (task markdown files)
   - Any other modified files
3. **Use the standard commit workflow**:
   - Run `git status` to see all changes
   - Run `git diff` to review changes
   - Add all relevant files including `backlog/` folder
   - Create a descriptive commit message referencing the task
   - The commit message should follow the format: "Complete task-X: [brief description]"
4. **Do NOT push** unless explicitly requested by the user

Example workflow:
```bash
git add .
git commit -m "Complete task-2: Implement device discovery and relay control in API client

- Add async_get_devices() with caching
- Add async_set_relay() with validation
- Add comprehensive test coverage
- Update backlog task status to Done"
```

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->
