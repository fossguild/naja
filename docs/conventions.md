Contributing to <Name> ==============================

<Name> is open source, and you are welcome and encouraged to contribute.

The following guidelines outline how to get started.

Contribution Workflow
------------------------------

The official <Name> repository is at https://github.com/<proj_repo>

Before contributing, make sure you have read the essential documentation:

- `docs/manual.md`
- `docs/CONTRIBUTING.md` (this file)

Then, follow these steps:

1. Open an issue in the repository explaining the problem or suggestion you want
to address.

2. If you would like to resolve your issue (or someone else’s), follow the usual
   contribution procedure:

* fork the project on GitHub * create a branch for the issue * make your changes
in that branch * create a pull request for <Name>

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

Attribution and Licensing
------------------------------

If you have substantially modified an existing source or documentation file —
more than a simple typo correction or minor bug fix — you are entitled to have
your name added to the copyright notice [1] and to the `AUTHORS` file, if you
wish.

By submitting your contribution, you agree it will be available under the same
license as <Name> (GNU GPL v3 or later).

Branch Naming
------------------------------

When applicable, use the following conventions for commit messages and branch names:

**Permanent Branches**

The repository contains two GitFlow permanent branches:

- `main`: the stable branch
- `dev`: the unstable branch (also known as `develop`)

**Support Branch Names (for PRs)**

When creating a temporary branch, use the following keywords to indicate which branch your PR targets:

- `feat`: new feature or bug fix for the feature branch
- `hot`: hot fix for the main branch
- `wip`: work-in-progress branch (rename when ready)
- `rel`: release preparation (GitFlow `release`)
- `aux`: miscellaneous, not related to any issue

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
fix: correct wrong file name
fix: add missing semicolon
doc: update user manual
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