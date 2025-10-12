Contributing to Naja
==============================

Naja is open source, and you are welcome and encouraged to contribute.

The following guidelines outline how to get started.

Contribution Workflow
------------------------------

The official Naja repository is at https://github.com/fossguild/naja.

Before contributing, make sure you have read the essential documentation:

- `docs/manual.md`
- `docs/CONTRIBUTING.md` (this file)

Then, follow these steps:

1. Open an issue in the repository explaining the problem or suggestion you want
to address.

2. If you would like to resolve your issue (or someone else’s), follow the usual
   contribution procedure:

* fork the project on GitHub * create a branch for the issue * make your changes
in that branch * create a pull request for Naja

* Make sure your changes follow the project's standard linting and formatting, as it will
be required for merging (specified in manual.md)

Do not submit a PR/MR unrelated to an open issue. Ensure your contribution
complies with the project’s conventions (see below).

3. Go have a treat—you’ve earned it.

Project Standards
------------------------------

To keep things consistent, we adopt conventions commonly used in open source projects:

- REUSE specification v3 [1]
- GitFlow branching strategy [2]
- Semantic Versioning 2.0.0 [3]

Code of Conduct
------------------------------

The success of an open collaborative project relies not only on technical
contributions, but also on a healthy and respectful community. Ethics and mutual
respect are values worth upholding in their own right, as the foundation for
harmonious coexistence.

As a general principle, we invite everyone to maintain a considerate attitude
toward the diversity of opinions, identities, backgrounds, and cultures.

To embody these values in practice, we have outlined conduct rules in
`docs/CODE_OF_CONDUCT.md`.

Coding Conventions
------------------------------

Conventions ensure consistency and ease of collaboration within the FOSS
community.

* Symbol names, comments, file names, etc. should always be in English.
* Follow the project style for casing, indentation, and block alignment.
* Comments are text—use proper capitalization and punctuation.

Development Setup
------------------------------

To contribute to this project, you'll need to set up the development environment:

### Quick Setup

Use the provided Makefile for the fastest setup:

```bash
make dev
```

This command will:
- Install all development dependencies (`uv sync --dev`)
- Set up pre-commit hooks (`uv run pre-commit install`)

### Development Commands

Use these Makefile commands during development:

```bash
make run      # Play the game
make          # Run all quality checks (default)
make format   # Format code with Black and Ruff
make lint     # Check code quality without fixing
make clean    # Remove temporary files and caches
```

This setup ensures your code is automatically formatted and linted before each commit.
All pull requests must pass the linting checks to be merged.

Attribution and Licensing
------------------------------

If you have substantially modified an existing source or documentation file —
more than a simple typo correction or minor bug fix — you are entitled to have
your name added to the copyright notice [1] and to the `AUTHORS` file, if you
wish.

By submitting your contribution, you agree it will be available under the same
license as Naja (GNU GPL v3 or later).

Branch Naming
------------------------------

When applicable, use the following conventions for commit messages and branch names:

**Permanent Branches**

The repository contains two GitFlow permanent branches:

- `main`: the stable branch
- `dev`: the unstable branch (also known as `develop`)

**Support Branch Names (for PRs)**

When creating a temporary branch, use the following keywords to indicate which branch your PR targets:

- `feat`: advance normal development  (merge into dev)
- `hot` : hot fix for the main branch (merge into main)
- `wip` : work-in-progress branch (will be feat or hot)
- `rel` : release preparation (GitFlow `release`)
- `aux` : miscellaneous, not related to any issue

For `feat`, `hot`, and `wip` branches, use this scheme:

```
feat/<issue-number>/<short-descriptive-note>
hot/<issue-number>/<short-descriptive-note>
wip/<issue-number>/<short-descriptive-note>
```

Use lowercase alphanumeric ASCII characters, underscores, and hyphens instead of
spaces. Avoid punctuation.

Example:

```
feat/42/modify-option-help
fix/66/crash-on-negative-input
wip/24/preliminary-attempt
```

For `rel` branches, use `rel/<release-number>`. For `aux` branches, use
`aux/<short-description>`.

Commit Messages
------------------------------

When writing a commit message, use the format:

```
tag: short description
```

The `tag` indicates the purpose of your commit:

- `code`: fix, add, or refactor source code
- `doc`: modify or extend documentation
- `build`: fix or improve the build process
- `repo`: tidy up the repository and organization
- `minor`: trivial changes (e.g., typo or cosmetics)
- `other`: something else

The short description should be in the imperative form (e.g., fix, add, remove).

Example:

```
code: correct wrong file name
code: add missing semicolon
doc:  update user manual
repo: remove build artifacts
```

If your commit addresses more than one purpose, use multiple commit messages
(one per line).

If needed, you may add a longer explanation (after a blank line) to provide
context. This should be normal text, with proper capitalization and punctuation.

Example:

```
fix: remove command-line option '--test'

This option is redundant, as the same behavior is already implemented by
the '--dry-run' option. In addition, '--test' was ambiguous.
```

Git Workflow Best Practices
------------------------------

To maintain a clean commit history and smooth collaboration:

### Keeping Your Branch Updated

**Always use rebase instead of merge** when updating your branch with the latest changes from `dev`:

```bash
# Good: Rebase to keep linear history
git pull origin dev --rebase

# Avoid: Merge creates unnecessary merge commits
git pull origin dev  # or git merge dev
```

### Resolving Conflicts

When conflicts occur during rebase:

1. Fix conflicts in the affected files
2. Stage the resolved files: `git add <files>`
3. Continue the rebase: `git rebase --continue`
4. Repeat until rebase is complete

### Before Submitting a Pull Request

1. **Rebase your branch** on the latest `dev`:
   ```bash
   git checkout your-feature-branch
   git pull origin dev --rebase
   ```

2. **Run quality checks**:
   ```bash
   make  # Runs linting, formatting, and all checks
   ```

3. **Push your changes**:
   ```bash
   git push origin your-feature-branch
   ```

### Why Rebase Over Merge?

- **Linear History**: Easier to understand project evolution
- **Cleaner Logs**: No unnecessary "merge dev into feature" commits
- **Bisect Friendly**: Makes debugging with `git bisect` more effective
- **Professional Standard**: Common practice in most open source projects

Documentation Guidelines
------------------------------

### Keep Documentation Updated

When adding new features or making changes that affect users:

1. **Update the user manual** (`docs/manual.md`):
   - Add new controls or gameplay mechanics
   - Document new command-line options or configuration
   - Update system requirements if needed

2. **Update README.md** for significant changes:
   - New major features that affect the quick start experience
   - Changes to installation or setup process

3. **Update this CONTRIBUTING.md** for development changes:
   - New development tools or processes
   - Changes to coding standards or workflow

### Documentation Best Practices

- **Write for beginners**: Assume users are new to the project
- **Include examples**: Show command usage with concrete examples
- **Test instructions**: Verify that documented steps actually work
- **Keep it concise**: Use clear, direct language without unnecessary detail

Other Conventions
------------------------------

Compliance with Keep a Changelog [5] is under consideration.

References
------------------------------

[1] REUSE Software, https://reuse.software [2] GitFlow,
https://nvie.com/posts/a-successful-git-branching-model/ [3] Semantic
Versioning, https://semver.org/ [4] Conventional Commits,
https://www.conventionalcommits.org/en/v1.0.0/ [5] Keep a Changelog,
https://keepachangelog.com/en/1.0.0/
