---
name: push-pr
description: Push Branch and Create Draft Pull Request
---

# Push Branch and Create Draft Pull Request

This command gets Linear ticket details, drafts a PR description, pushes the current branch, and creates a draft pull request on GitHub.

---

## Phase 1: Validate Environment and Branch

### 1.1 Get Current Branch Information
- Get the current git branch name
- Extract the ticket identifier from the branch name (e.g., "PROJ-123" from "proj-123-feature-name")
- If the current branch is `main` or `master`, stop and prompt the user to switch branches

### 1.2 Determine Base Branch
- Determine the target/base branch for the PR (typically `main` or `master`)
- Verify the base branch exists
- If base branch doesn't exist, ask the user to specify it

---

## Phase 2: Get Linear Ticket Details

### 2.1 Extract Ticket ID
- Extract the ticket identifier from the branch name
- If no ticket ID can be extracted, prompt the user to provide it

### 2.2 Load Ticket Details
- Check for ticket JSON file at: `~/.claude/data/linear-tickets/<ticket_id>.json`
- If the file doesn't exist:
  - Inform the user and suggest running the `get-linear-ticket` command
  - Optionally, attempt to fetch it using the Linear CLI (e.g., `linear issue show <ticket_id> --format json`)
- Read and parse the JSON file

### 2.3 Get Linear Ticket Link
- Get the Linear ticket URL from the `url` field in the ticket JSON
- If `url` field is not present (older tickets):
  - Prompt the user to re-fetch the ticket using `get-linear-ticket` command
  - Or prompt the user to provide the full Linear ticket URL manually

---

## Phase 3: Review Changes

### 3.1 Get Commit History
- Read git commit history with messages
- Review commit messages to understand what was done

### 3.2 Get Code Changes
- Run `git diff origin/<base_branch>...HEAD` to see changes
- Analyze the changes to understand what files were modified and what functionality was added/changed/removed

### 3.3 Review Linear Ticket Information
- Review the Linear ticket title, description, and comments
- Understand the requirements and acceptance criteria
- Use this information to inform the PR description

---

## Phase 4: Draft PR Description

### 4.1 Read PR Template
- Read the `.github/pull_request_template.md` file
- Identify all sections in the template
- Understand the format and structure of each section
- Note which sections are required vs optional based on the template

### 4.2 Fill Out PR Template Sections
Work through each section in the template. Every section should be present in the output, but not every section needs to be filled in (some may be left empty if not applicable).

For each section type, follow these guidelines:

- **Linear ticket link section** (if present):
  - Format as `[PROJ-XXX](linear-url)` where PROJ-XXX is the ticket number and the URL is the full Linear ticket link from the ticket JSON

- **Type of change section** (if present):
  - Choose the most appropriate option from the available choices in the template

- **Description/Explanation section** (or equivalent):
  - Provide a high-level description of what's different between the base branch and this PR
  - Focus on business logic, system architecture, or user experience changes—not individual files
  - Keep it concise and easy to understand for someone unfamiliar with the codebase
  - Explain the "what" and "why", not the "how"
  - Base this on the actual code changes reviewed in Phase 3
  - Example format:
    - Users can now see their course enrollment count on the course card
    - Course cards display an enrollment status badge (enrolled, pending, completed)
    - Added automatic timestamp tracking for course updates

- **Test plan/Testing section** (or equivalent):
  - If the changes don't need testing (e.g. documentation updates, config changes), mark as "N/A" or omit
  - Only include manual testing steps — do not mention automated tests (unit tests, e2e tests, etc.)
  - Be thorough, specific, and reproducible
  - Make it easy for other developers to follow
  - Provide step-by-step instructions that can be followed to verify the changes work

- **CI options section** (if present):
  - Include any checkboxes or options as specified in the template
  - For example, include the checkbox for `pytest -x` if that option exists

- **Other sections**:
  - Fill out any other sections present in the template as appropriate
  - If a section doesn't apply to this PR, leave it empty or mark as "N/A" based on template conventions

### 4.3 Review PR Description Quality
- Verify all sections from the template are present in the output
- Check that filled sections are accurate and complete
- Ensure the description section is concise, high-level, and focuses on business logic, architecture, or user experience
- Ensure the testing section is thorough, specific, and reproducible
- Verify that the description accurately reflects the changes reviewed in Phase 3

---

## Phase 5: Push Branch

### 5.1 Check Branch Status
- Check if the branch has commits to push
- Check if there are uncommitted changes
- If there are uncommitted changes, inform the user and ask if they want to commit them first

### 5.2 Push Branch
- Push the current branch to origin
- Use `git push -u origin <branch_name>` if branch doesn't exist remotely, otherwise use `git push`

---

## Phase 6: Create Draft Pull Request

### 6.1 Check for GitHub CLI
- Check if GitHub CLI (`gh`) is installed and available
- If not available, inform the user and provide installation instructions
- Verify GitHub CLI is authenticated
- If not authenticated, inform the user they need to authenticate

### 6.2 Determine Repository
- Get the GitHub repository information from git remote
- Extract repository owner and name

### 6.3 Create Draft PR
- Create a draft pull request using GitHub CLI: `gh pr create --draft --base <base_branch> --head <branch_name> --title "<PR Title>" --body "<PR Body>"`
- PR Title format: `<ticket_id>: <Linear ticket title or concise summary of changes>`
  - Start with the ticket ID (e.g., `PROJ-123`)
  - Follow with a colon and a space
  - Then use the Linear ticket title if it accurately describes the changes, otherwise use a concise summary of the changes
- PR Body should be the filled-out PR description from Phase 4
- Verify the PR was created successfully
- Extract the PR URL from the CLI output

### 6.4 Post Review Request Comment
- Post a comment on the newly created PR using GitHub CLI: `gh pr comment <PR URL> --body "@cursor review"`
- The comment must be exactly `@cursor review` (no additional text)
- Verify the comment was posted successfully

### 6.5 Display PR URL
- Get the PR URL from the CLI output (extracted in step 6.3)
- Display the PR URL as a clickable link to the user
- Format: Display as a markdown link `[PR #<number>](<PR URL>)`

---

## Important Notes

1. **PR Description Format**: Follow the template exactly. Every section should be present, but not every section needs to be filled in.

2. **Description Section**: Focus on high-level business logic, system architecture, or user experience changes—not individual files.

3. **Testing Section**: Only manual testing steps. Do not mention automated tests. Be thorough, specific, and reproducible.

4. **Draft Mode**: The PR will be created in draft mode.

5. **Linear Ticket**: Requires a Linear ticket ID (extracted from branch name or provided by user). Ticket must be fetched first using `get-linear-ticket` command.

6. **GitHub CLI Required**: Requires GitHub CLI (`gh`) to be installed and authenticated.

7. **Branch Validation**: Will not proceed if the current branch is `main` or `master`.

---

## Error Handling

- If current branch is main/master: Stop and prompt user to switch branches
- If no ticket ID can be extracted: Prompt user to provide Linear ticket ID
- If ticket file doesn't exist: Inform user and suggest fetching ticket first
- If base branch doesn't exist: Ask user to specify the base branch
- If GitHub CLI is not installed: Inform user and provide installation instructions
- If GitHub CLI is not authenticated: Inform user they need to authenticate
- If push fails: Display error and ask user to resolve issues
- If PR creation fails: Display error message and suggest manual creation
- If PR comment fails: Display error and inform user they can manually comment `@cursor review` on the PR
- If PR template doesn't exist: Use a default template format or ask user for guidance
