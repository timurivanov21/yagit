# Contributing to **YAGit**

_First off – thank you for taking the time to contribute!_  
This document explains the workflow, coding standards and quality gates that
apply to **YAGit – Yet‑Another GitLab → YandexTracker integration service**.

> **TL;DR**  
> 1. Fork → clone → create branch.  
> 2. Write tests & docs, make CI green.  
> 3. Commit with **Conventional Commits**.  
> 4. Push and open Pull Request, linking an issue.  

---

## 1·Code of Conduct
This project adheres to the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
By participating you agree to abide by its terms.

---

## 2·Before you start

| Prerequisite | Version / Link |
|--------------|----------------|
| **Python**   | 3.12  |
| **Poetry**   | ≥1.8 |
| **Docker** & **Docker Compose** | Latest stable |
| **Git**      | ≥2.40 |

```bash
# Clone your fork
git clone git@github.com:<you>/yagit.git
cd yagit

# Add upstream once
git remote add upstream https://github.com/timurivanov21/yagit.git
```

Install dependencies & pre‑commit hooks:

```bash
poetry install --with dev
poetry run pre-commit install
```

---

## 3·Creating / Working on Issues

### 3.1 Search first  
Please scan the [issue list](https://github.com/timurivanov21/yagit/issues)— duplicates help nobody.

### 3.2 Issue types & title format

| Type | Prefix in title | Labels |
|------|-----------------|--------|
| **Bug**          | `[Bug]`          | `bug` |
| **Feature**      | `[Feature]`      | `enhancement` |
| **Documentation**| `[Docs]`         | `documentation` |
| **Task / Chore** | `[Task]`         | `chore` |

Example: `[Bug] webhook returns 500 on push event`

Use the built‑in **issue templates** (Bug Report / Feature Request).  
Fill in **Steps to Reproduce**, **Expected Result**, **Actual Result** or  
**Motivation**, **Proposal**, **Alternatives** respectively.

---

## 4·Branching model

* Base branch: **`dev`**
* Feature branches: `type/short-description`, e.g.:

```
feat/merge-request-status
fix/webhook-500-push
docs/add-contributing
```

Keep branches small & focused; 1 PR ↔︎ 1 logical change.

---

## 5·Commit message convention

We follow **[Conventional Commits](https://www.conventionalcommits.org/)**.

```
<type>(<scope>): <subject>

<body>          # optional – WHAT & WHY, not HOW
<footer>        # optional – BREAKING CHANGE or links
```

Allowed **type** values: `feat`, `fix`, `docs`, `test`, `refactor`,
`perf`, `build`, `ci`, `chore`, `revert`.

Example:

```
feat(webhook): support merge_request/closed event

Closes #42.
```

---

## 6·Keeping your fork in sync

```bash
git checkout main
git fetch upstream
git merge upstream/main          # or git rebase upstream/main
git push origin main
```

Rebase your feature branch regularly:

```bash
git checkout feat/my-change
git rebase main
git push --force-with-lease
```

---

## 7·Tests & coverage

* Unit tests **must** accompany code changes.
* Use `pytest`, `pytest-asyncio`, `pytest-httpx`.
* Mock external HTTP via `httpx.MockTransport`; do **not** mock own ORM logic.
* Minimum coverage: **80% lines & branches** (`pytest --cov=yagit`).

---

## 8·Opening a Pull Request

1. Push your branch:

   ```bash
   git push -u origin feat/my-change
   ```

2. In GitHub ‑> **Compare & pull request**.
3. Ensure **base** =`timurivanov21/yagit:main`, **compare** =`<you>:feat/my-change`.
4. Fill the PR template:

   * **What & Why** – short description.
   * **Linked issues** – `Closes #xx`.
   * **Checklist** – tests, docs, CI green.

> **CI gates**:  
> • Ruff & Black (autofix)  
> • MyPy strict  
> • Pytest (coverage)  
> • Docker build  

A failing gate blocks merge.

---

## 9·Review & merge

* Address review comments via additional commits or `--amend`; then
  `git push --force-with-lease`.
* Squash & merge is the default strategy for a tidy history.
* A maintainer will label the PR and, when approved + green, merge it.

---

## 10·Release flow (maintainers only)

1. `make bump VERSION=x.y.z` (semver).  
2. Changelog generated from Conventional Commits.  
3. GitHub Release & Docker Hub image upload via GitHub Actions.

---

## 11·Documentation contributions

Site is built with **MkDocs Material**.

```bash
poetry run mkdocs serve
```

Docs live under `docs/` – one PR can update both code and docs.

---

Happy hacking!  
The **YAGit** team ❤️
