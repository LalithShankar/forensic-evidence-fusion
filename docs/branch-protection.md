# Branch protection for `main`

Epic 1 Story 1.3 requires that direct pushes to `main` are blocked and merges require a PR with passing CI and one approval.

## Required GitHub settings (manual)

In **Settings → Branches → Branch protection rules** for `main`:

1. Require a pull request before merging (at least 1 approval).
2. Require status checks to pass before merging:
   - `backend`
   - `frontend`
   - `secret-scan`
3. Do not allow bypassing the above settings.

These rules cannot be enforced from the repository alone; a repo admin must apply them on GitHub.
