# Contributing to FInee.ai

Thank you for contributing to **FInee.ai** (Compliance-Grounded Financial Advisory RAG Platform). To maintain code quality, security, and project stability, all contributors must follow this workflow.

---

## 1. Branching Strategy

We follow **GitHub Flow**.

- **`main`**: The primary, stable, and releasable branch.
- **Never commit development work directly to `main`.** All work must be conducted in dedicated feature, fix, or maintenance branches.

### Branch Naming Conventions

Prefix your branch name with one of the following categories, followed by a short, hyphen-separated description:

- `feature/<short-description>`: New platform capability or module
- `fix/<short-description>`: Bug fix or error resolution
- `docs/<short-description>`: Documentation changes or additions
- `refactor/<short-description>`: Code restructuring without feature changes
- `test/<short-description>`: Adding or updating test suites
- `chore/<short-description>`: Maintenance, tooling, or dependency updates

#### Examples
- `feature/document-ingestion`
- `feature/embedding-pipeline`
- `feature/vector-storage`
- `feature/semantic-retrieval`
- `feature/chat-api`
- `fix/document-parser-error`
- `docs/update-setup-guide`

---

## 2. Issue Workflow

1. **Check Existing Issues**: Search existing GitHub Issues before creating a new one.
2. **Use Templates**: Create issues using the appropriate template:
   - Feature Request (`feature`)
   - Bug Report (`bug`)
   - Documentation Task (`documentation`)
3. **Fill Required Fields**: Include title, description, motivation/why needed, acceptance criteria, priority, and relevant labels (`feature`, `bug`, `documentation`, `in-progress`, `high-priority`, `backend`, `rag`, `frontend`).
4. **Assignee**: Assign the issue to yourself or the relevant owner before starting work.

---

## 3. Commit Message Convention

We enforce **Conventional Commits** to keep the git history structured and readable.

### Commit Format
```text
<type>: <short description>
```

### Commit Types
- `feat:` New feature or functionality
- `fix:` Bug fix or error patch
- `docs:` Documentation updates only
- `refactor:` Code refactoring (no functional or API contract changes)
- `test:` Adding, updating, or fixing tests
- `chore:` Tooling, configuration, or environment updates

### Examples for FInee.ai
- `feat: add document ingestion module`
- `feat: add semantic retrieval service`
- `fix: correct chunk metadata mapping`
- `docs: update workspace setup guide`
- `test: add retrieval pipeline tests`
- `refactor: separate embedding service from ingestion`

---

## 4. Pull Request Workflow

1. **Create a Branch**: `git checkout -b feature/semantic-retrieval`
2. **Develop & Commit**: Make focused changes following conventional commit messages.
3. **Push to Remote**: `git push origin feature/semantic-retrieval`
4. **Open Pull Request**: Create a PR targeting `main` using the PR template.
5. **Link Related Issue**: Include `Closes #<issue-number>` in the PR description.
6. **Pass CI Status Checks**: Ensure automated pytest runs pass successfully.
7. **Code Review**: Request review from at least one maintainer.
8. **Merge & Clean Up**: Merge into `main` after approval, then delete the feature branch.

---

## 5. Code Review Expectations

All pull requests merged into `main` must meet the following criteria:
- [x] Code adheres to the established project structure and architectural boundaries.
- [x] Automated tests cover new code paths, and all existing tests pass cleanly.
- [x] No secrets, API keys, or `.env` files are committed.
- [x] All reviewer comments and conversations are resolved.
- [x] Documentation is updated where appropriate.
