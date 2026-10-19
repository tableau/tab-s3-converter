# Contributing Guide For tab-s3-converter

This page lists the operational governance model of this project, as well as the recommendations and requirements for how to best contribute to tab-s3-converter. We strive to obey these as best as possible. As always, thanks for contributing – we hope these guidelines make it easier and shed some light on our approach and processes.

# Governance Model

## Salesforce Sponsored

The intent and goal of open sourcing this project is to increase the contributor and user base. However, only Salesforce employeeshts and will be the final arbiters of what contributions are accepted or not.

# Getting started

tab-s3-converter is a small Python tool with no runtime dependencies. To work on it you need Python 3.11+ and [uv](https://docs.as

```sh
git clone https://github.com/tableau/tab-s3-converter.git
cd tab-s3-converter
uv run pytest          # create the dev environment and run the test suite
uvx ruff check .       # lint
uvx ruff format .      # format
```

To try the converter on a file:

```sh
uv run python -m tab_s3_converter path/to/workbook.twbx -o converted.twbx
```

See the [README](README.md) for full usage and a description of what the conversion does.

# Issues, requests & ideas

Use GitHub Issues page to submit issues, enhancement requests and discuss ideas.

### Bug Reports and Fixes
-  If you find a bug, please search for it in the [Issues](https://github.com/tableau/tab-s3-converter/issues), and if it isn't already tracked,
   [create a new issue](https://github.com/tableau/tab-s3-converter/issues/new). Please include:
   -  The file type (`.twb`, `.tds`, `.twbx`, or `.tdsx`) and the Tableau version that produced it.
   -  The exact command you ran and its output. Re-run with `--debug` to include the full traceback.
   -  A minimal file that reproduces the problem, if you can share one. **Do not attach workbooks or data sources that contain real credentials, bucket names, or customer data.** Replace them with placeholders first.
-  Even if an Issue is closed, feel free to comment and add details, it will still be reviewed.
-  Issues that have already been identified as a bug (note: able to reproduce) will be labelled `bug`.
-  If you'd like to submit a fix for a bug, [send a Pull Request](#creating-a-pull-request) and mention the Issue number.
   -  Include tests that isolate the bug and verify that it was fixed.

### New Features
-  If you'd like to add new functionality to this project, describe the problem you want to solve in a [new Issue](https://github.com/tableau/tab-s3-converter/issues/new).
-  Issues that have been identified as a feature request will be labelled `enhancement`.
-  If you'd like to implement the new feature, please wait for feedback from the project
   maintainers before spending too much time writing the code. In some cases, `enhancement`s may
   not align well with the project objectives at the time.

### Tests, Documentation, Miscellaneous
-  If you'd like to improve the tests, you want to make the documentation clearer, you have an
   alternative implementation of something that may have advantages over the way it's currently
   done, or you have any other change, we would be happy to hear about it!
   -  If it's a trivial change, go ahead and [send a Pull Request](#creating-a-pull-request) with the changes you have in mind.
   -  If not, [open an Issue](https://github.com/tableau/tab-s3-converter/issues/new) to discuss the idea first.

If you're new to our project and looking for some way to make your first contribution, look for
Issues labelled `good first contribution`.

# Contribution Checklist

- [x] Clean, simple, well styled code
  - Code must pass `uvx ruff check .` and be formatted with `uvx ruff format .` (configured in `pyproject.toml`: line length 100, Python 3.11 target).
- [x] Commits should be atomic and messages must be descriptive. Related issues should be mentioned by Issue number.
- [x] Comments
  - Module-level & function-level comments.
  - Comments on complex blocks of code or algorithms (include references to sources).
- [x] File headers
  - Every new source and test file starts with the license header:
    ```python
    # Copyright (c) 2026, Salesforce, Inc.
    # SPDX-License-Identifier: Apache-2.0
    ```
- [x] Tests
  - The test suite (`uv run pytest`) must be complete and pass.
  - Increase code coverage, not the other way around.
  - Each module in `tab_s3_converter/` has a matching `tests/test_<module>.py`; borrow inspiration from existing tests. Tests against whole sample files go in `tests/test_end_to_end.py`, with sample files in `tests/fixtures/`.
  - Fixtures must not contain real identifiers. Use placeholders such as `example-bucket` for bucket names and AWS's documented example key `AKIAIOSFODNN7EXAMPLE` for access key IDs.
  - The converter never modifies the input file, and it preserves supporting files inside `.twbx`/`.tdsx` archives byte-for-byte. Changes that touch these code paths must keep both guarantees and test them.
- [x] Dependencies
  - The converter has **no runtime dependencies** and must stay standard-library only. Do not add entries to `dependencies` in `py
  - Keep dev-only tooling in the `dev` dependency group to a minimum, and commit the updated `uv.lock` with any change to it.
  - Prefer Apache 2.0, BSD3, MIT, ISC and MPL licenses.
- [x] Reviews
  - Changes must be approved via peer code review

# Creating a Pull Request

1. **Ensure the bug/feature was not already reported** by searching on GitHub under Issues.  If none exists, create a new issue so that other contributors can keep track of what you are trying to add/fix and offer suggestions (or let you know if there is already an effort in progress).
2. **Fork** the repo on GitHub and **clone** your fork to your machine.
3. **Create** a new branch to contain your work (e.g. `git checkout -b fix-issue-11`)
4. **Commit** changes to your own branch.
5. **Push** your work back up to your fork. (e.g. `git push origin fix-issue-11`)
6. **Submit** a Pull Request against the `main` branch and refer to the issue(s) you are fixing. Try not to pollute your pull request with unintended changes. Keep it simple and small.
7. **Sign** the Salesforce CLA (you will be prompted to do so when submitting the Pull Request)

> **NOTE**: Be sure to [sync your fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork) before making a pull request.

# Contributor License Agreement ("CLA")
In order to accept your pull request, we need you to submit a CLA. You only need
to do this once to work on any of Salesforce's open source projects.

Complete your CLA here: <https://cla.salesforce.com/sign-cla>

# Issues
We use GitHub issues to track public bugs. Please ensure your description is
clear and has sufficient instructions to be able to reproduce the issue.

# Code of Conduct
Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

# License
By contributing your code, you agree to license your contribution under the terms of our project [LICENSE](LICENSE) and to sign the [Salesforce CLA](https://cla.salesforce.com/sign-cla)

A few things to check before you commit:

- Governance model: I chose Salesforce Sponsored, since it's the usual choice for Salesforce and Tableau repos. If this is a one-off migration tool you don't plan to maintain, swap in "Published but not supported".
- Repo slug: I assumed the public repo will be tableau/tab-s3-converter, because your origin is git.soma.salesforce.com/Tableau/tab-s3-converter. If the public org or name is different, do a find/replace.
- Missing files:
  - LICENSE: The repo has no LICENSE file, but both NOTICE and this guide link to one, so you'll need to add it before publishing. I linked to LICENSE to match NOTICE, not the template's LICENSE.txt.
  - CODE_OF_CONDUCT.md: This doesn't exist yet either.
  - ROADMAP.md: There's no roadmap file and no community channel, so I replaced the "join the community / roadmap" paragraph with dev setup steps.
  - Issue templates: There aren't any, so I replaced "fill out the Bug Report template" with a list of what to include.
- Changes to the template text:
  - Typos and commands: I fixed "arbitrars" (now "arbiters"), "not versa", git br (now git checkout -b) and the git push example, which was missing the remote.
  - Links: The #creating_a_pull_request anchor now uses the hyphens GitHub generates. I also added a "Fork" step and updated the outdated "sync your fork" link.
  - Scala example: I replaced the template's Scala testkit example (com.salesforce.op.test._) with this repo's test layout.
- Project-specific rules: I added rules for the license header, the stdlib-only requirement and placeholder-only fixtures. They coers, the README and commit bead642, which scrubbed real values from the fixtures.
