# GitHub Team Workflow & Branch Protection Guide

This document outlines the standard end-to-end GitHub development process for **FInee.ai** and provides manual configuration instructions for repository administrators to set up `main` branch protection rules.

---

## End-to-End Development Process

Follow this 11-step workflow for all contributions to the repository:

1. **Check GitHub Issues**: Review existing open issues to ensure the task is identified and prioritized.
2. **Select or Create an Issue**: Choose an unassigned issue or create a new issue using the appropriate template (`feature_request`, `bug_report`, or `documentation_task`).
3. **Create a Branch**: Create a dedicated branch linked to that task from `main` using the standard branch naming convention (`feature/...`, `fix/...`, `docs/...`, `refactor/...`, `test/...`, `chore/...`).
4. **Make Changes on Branch**: Execute code changes exclusively on the feature branch. Never commit directly to `main`.
5. **Use Conventional Commits**: Structure all commit messages according to the Conventional Commit specification (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
6. **Push the Branch**: Push your branch to GitHub (`git push origin <branch-name>`).
7. **Open a Pull Request**: Open a pull request targeting the `main` branch.
8. **Link Issue**: Include `Closes #<issue-number>` in the PR description to ensure automatic issue closure upon merging.
9. **Request Review**: Assign at least one team member or maintainer for code review.
10. **Merge After Approval & Passing CI**: Merge into `main` only after receiving at least one approving review and ensuring all automated GitHub Actions CI status checks pass.
11. **Delete Feature Branch**: Delete the remote and local feature branch after merging to keep the repository clean.

---

## Recommended `main` Branch Protection Rules

To safeguard project stability and enforce compliance review, the `main` branch must be configured with the following protection settings:

- **Require a pull request before merging**: Prevents direct pushes to `main`.
- **Require approvals**: At least 1 approving review is required before merging.
- **Require status checks to pass before merging**: Requires the `CI Pipeline / Run Test Suite` job to pass.
- **Require conversation resolution before merging**: All review comments must be resolved before a PR can be merged.
- **Do not allow bypassing the above settings**: Enforce rules for administrators and team members alike.

---

## Manual GitHub Branch Protection Configuration Guide

Repository administrators should execute the following steps in the GitHub UI to enforce branch protection:

1. Navigate to your repository on GitHub (`https://github.com/<owner>/<repo>`).
2. Click on **Settings** in the top navigation bar.
3. In the left sidebar under *Code and automation*, click on **Branches**.
4. Click **Add branch protection rule** (or **Add rule**).
5. In **Branch name pattern**, enter `main`.
6. Enable the following settings:
   - Check **Require a pull request before merging**.
     - Check **Require approvals** and set *Required number of approvals before merging* to `1`.
   - Check **Require status checks to pass before merging**.
     - Check **Require branches to be up to date before merging**.
     - In the search bar for status checks, search and select `test` / `Run Test Suite` (from `.github/workflows/ci.yml`).
   - Check **Require conversation resolution before merging**.
   - Check **Do not allow bypassing the above settings** (Optional but recommended for strict compliance).
7. Click **Create** or **Save changes** at the bottom of the page.
