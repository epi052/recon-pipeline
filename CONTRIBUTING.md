# Contributor's guide

<!-- this guide is a modified version of the guide used by the awesome guys that wrote cmd2 -->

First of all, thank you for contributing! Please follow these steps to contribute:

1. Find an issue that needs assistance by searching for the [Help Wanted](https://github.com/epi052/recon-pipeline/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) tag
2. Let us know you're working on it by posting a comment on the issue
3. Follow the [Contribution guidelines](#contribution-guidelines) to start working on the issue

Remember to feel free to ask for help by leaving a comment within the Issue.

Working on your first pull request? You can learn how from this *free* series
[How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

###### If you've found a bug that is not on the board, [follow these steps](README.md#found-a-bug).

---

## Contribution guidelines

- [Prerequisites](#prerequisites)
- [Forking the project](#forking-the-project)
- [Creating a branch](#creating-a-branch)
- [Setting up for recon-pipeline development](#setting-up-for-recon-pipeline-development)
- [Making changes](#making-changes)
- [Static code analysis](#static-code-analysis)
- [Running the test suite](#running-the-test-suite)
- [Squashing your commits](#squashing-your-commits)
- [Creating a pull request](#creating-a-pull-request)
- [How we review and merge pull requests](#how-we-review-and-merge-pull-requests)
- [Next steps](#next-steps)
- [Other resources](#other-resources)
- [Advice](#advice)

### Forking the project

#### Setting up your system

1. Install your favorite `git` client
2. Create a parent projects directory on your system. For this guide, it will be assumed that it is `~/projects`.

#### Forking recon-pipeline

1. Go to the top-level recon-pipeline repository: <https://github.com/epi052/recon-pipeline>
2. Click the "Fork" button in the upper right hand corner of the interface
([more details here](https://help.github.com/articles/fork-a-repo/))
3. After the repository has been forked, you will be taken to your copy of the recon-pipeline repo at `your_username/recon-pipeline`

#### Cloning your fork

1. Open a terminal / command line / Bash shell in your projects directory (_e.g.: `~/projects/`_)
2. Clone your fork of recon-pipeline, making sure to replace `your_username` with your GitHub username. This will download the
entire recon-pipeline repo to your projects directory.

```sh
$ git clone https://github.com/your_username/recon-pipeline.git
```

#### Set up your upstream

1. Change directory to the new recon-pipeline directory (`cd recon-pipeline`)
2. Add a remote to the official recon-pipeline repo:

```sh
$ git remote add upstream https://github.com/epi052/recon-pipeline.git
```

Now you have a local copy of the recon-pipeline repo!

#### Maintaining your fork

Now that you have a copy of your fork, there is work you will need to do to keep it current.

##### **Rebasing from upstream**

Do this prior to every time you create a branch for a PR:

1. Make sure you are on the `master` branch

  > ```sh
  > $ git status
  > On branch master
  > Your branch is up-to-date with 'origin/master'.
  > ```

  > If your aren't on `master`, resolve outstanding files and commits and checkout the `master` branch

  > ```sh
  > $ git checkout master
  > ```

2. Do a pull with rebase against `upstream`

  > ```sh
  > $ git pull --rebase upstream master
  > ```

  > This will pull down all of the changes to the official master branch, without making an additional commit in your local repo.

3. (_Optional_) Force push your updated master branch to your GitHub fork

  > ```sh
  > $ git push origin master --force
  > ```

  > This will overwrite the master branch of your fork.

### Creating a branch

Before you start working, you will need to create a separate branch specific to the issue or feature you're working on.
You will push your work to this branch.

#### Naming your branch

Name the branch something like `23-xxx` where `xxx` is a short description of the changes or feature
you are attempting to add and 23 corresponds to the Issue you're working on.

#### Adding your branch

To create a branch on your local machine (and switch to this branch):

```sh
$ git checkout -b [name_of_your_new_branch]
```

and to push to GitHub:

```sh
$ git push origin [name_of_your_new_branch]
```

##### If you need more help with branching, take a look at _[this](https://github.com/Kunena/Kunena-Forum/wiki/Create-a-new-branch-with-git-and-manage-branches)_.

### Setting up for recon-pipeline development
For doing recon-pipeline development, it is recommended you create a virtual environment and install both the project
dependencies as well as the development dependencies.

#### Create a new environment for recon-pipeline using Pipenv
`recon-pipeline` has support for using [Pipenv](https://docs.pipenv.org/en/latest/) for development.

`Pipenv` essentially combines the features of `pip` and `virtualenv` into a single tool.  `recon-pipeline` contains a Pipfile which
 makes it extremely easy to setup a `recon-pipeline` development environment using `pipenv`.

To create a virtual environment and install everything needed for `recon-pipeline` development using `pipenv`, do the following
from a GitHub checkout:
```sh
pipenv install --dev
```

To create a new virtualenv, using a specific version of Python you have installed (and on your PATH), use the
--python VERSION flag, like so:
```sh
pipenv install --dev --python 3.7
```

### Making changes

It's your time to shine!

#### How to find code in the recon-pipeline codebase to fix/edit

The recon-pipeline project directory structure is pretty simple and straightforward.  All
actual code for recon-pipeline is located underneath the `pipeline` directory.  The code to
generate the documentation is in the `docs` directory.  Unit tests are in the
`tests` directory.  There are various other files in the root directory, but these are
primarily related to continuous integration and release deployment.

#### Changes to the documentation files

If you made changes to any file in the `/docs` directory, you need to build the
Sphinx documentation and make sure your changes look good:

```sh
$ sphinx-build docs/ docs/_build/
```

In order to see the changes, use your web browser of choice to open `docs/_build/index.html`.

### Static code analysis

recon-pipeline uses two code checking tools:

1. [black](https://github.com/psf/black)
2. [flake8](https://github.com/PyCQA/flake8)

#### pre-commit setup

recon-pipeline uses [pre-commit](https://github.com/pre-commit/pre-commit) to automatically run both of its static code analysis tools.  From within your
virtual environment's shell, run the following command:

```sh
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

With that complete, you should be able to run all the pre-commit hooks.

```text
❯ pre-commit run --all-files
black....................................................................Passed
flake8...................................................................Passed
Trim Trailing Whitespace.................................................Passed
Debug Statements (Python)................................................Passed
run tests................................................................Passed
```

> Please do not ignore any linting errors in code you write or modify, as they are meant to **help** you and to ensure a clean and simple code base.

### Running the test suite
When you're ready to share your code, run the test suite:
```sh
$ cd ~/projects/recon-pipeline
$ python -m pytest tests
```
and ensure all tests pass.

Test coverage can be checked using `coverage`:

```sh
coverage run --source=pipeline -m pytest  tests/test_recon/ tests/test_shell/ tests/test_web/ tests/test_models && coverage report -m
=====================================================================================================================================
platform linux -- Python 3.7.5, pytest-5.4.1, py-1.8.1, pluggy-0.13.1
rootdir: /home/epi/PycharmProjects/recon-pipeline, inifile: pytest.ini
collected 225 items

tests/test_recon/test_amass.py .........                                                                                                                                                               [  4%]
tests/test_recon/test_config.py ...........                                                                                                                                                            [  8%]
tests/test_recon/test_helpers.py .............                                                                                                                                                         [ 14%]
tests/test_recon/test_masscan.py .......                                                                                                                                                              [ 18%]
tests/test_recon/test_nmap.py ...........                                                                                                                                                              [ 23%]
tests/test_recon/test_parsers.py .............................................................                                                                                                         [ 50%]
tests/test_recon/test_targets.py ..                                                                                                                                                                    [ 51%]
tests/test_shell/test_recon_pipeline_shell.py ................................................................                                                                                         [ 79%]
tests/test_web/test_aquatone.py ......                                                                                                                                                                 [ 82%]
tests/test_web/test_gobuster.py .......                                                                                                                                                                [ 85%]
tests/test_web/test_subdomain_takeover.py ................                                                                                                                                             [ 92%]
tests/test_web/test_targets.py ...                                                                                                                                                                     [ 93%]
tests/test_web/test_webanalyze.py .......                                                                                                                                                              [ 96%]
tests/test_models/test_db_manager.py ....                                                                                                                                                              [ 98%]
tests/test_models/test_pretty_prints.py ...                                                                                                                                                            [100%]

============================================================================================ 225 passed in 20.35s ============================================================================================
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
pipeline/__init__.py                           0      0   100%
pipeline/models/__init__.py                    0      0   100%
pipeline/models/base_model.py                  2      0   100%
pipeline/models/db_manager.py                123      0   100%
pipeline/models/endpoint_model.py             12      0   100%
pipeline/models/header_model.py               12      0   100%
pipeline/models/ip_address_model.py           10      0   100%
pipeline/models/nmap_model.py                 47      0   100%
pipeline/models/nse_model.py                  12      0   100%
pipeline/models/port_model.py                 12      0   100%
pipeline/models/screenshot_model.py           16      0   100%
pipeline/models/searchsploit_model.py         34      0   100%
pipeline/models/target_model.py               18      0   100%
pipeline/models/technology_model.py           28      0   100%
pipeline/recon-pipeline.py                   388      5    99%   94, 104-105, 356-358
pipeline/recon/__init__.py                     9      0   100%
pipeline/recon/amass.py                       66      2    97%   186-187
pipeline/recon/config.py                       7      0   100%
pipeline/recon/helpers.py                     36      0   100%
pipeline/recon/masscan.py                     82     24    71%   83-143
pipeline/recon/nmap.py                       120      0   100%
pipeline/recon/parsers.py                     68      0   100%
pipeline/recon/targets.py                     27      0   100%
pipeline/recon/tool_definitions.py             3      0   100%
pipeline/recon/web/__init__.py                 5      0   100%
pipeline/recon/web/aquatone.py                93      0   100%
pipeline/recon/web/gobuster.py                72      0   100%
pipeline/recon/web/subdomain_takeover.py      87      0   100%
pipeline/recon/web/targets.py                 27      0   100%
pipeline/recon/web/webanalyze.py              70      0   100%
pipeline/recon/wrappers.py                    34     21    38%   35-70, 97-127
------------------------------------------------------------------------
TOTAL                                       1520     52    97%
```

### Squashing your commits

When you make a pull request, it is preferable for all of your changes to be in one commit.  Github has made it very
simple to squash commits now as it's [available through the web interface](https://stackoverflow.com/a/43858707) at
pull request submission time.

### Creating a pull request

#### What is a pull request?

A pull request (PR) is a method of submitting proposed changes to the recon-pipeline
repo (or any repo, for that matter). You will make changes to copies of the
files which make up recon-pipeline in a personal fork, then apply to have them
accepted by the recon-pipeline team.

#### Need help?

GitHub has a good guide on how to contribute to open source [here](https://opensource.guide/how-to-contribute/).

##### Editing via your local fork

1.  Perform the maintenance step of rebasing `master`
2.  Ensure you're on the `master` branch using `git status`:

```sh
$ git status
On branch master
Your branch is up-to-date with 'origin/master'.

nothing to commit, working directory clean
```

1.  If you're not on master or your working directory is not clean, resolve
    any outstanding files/commits and checkout master `git checkout master`
2.  Create a branch off of `master` with git: `git checkout -B
    branch/name-here`
3.  Edit your file(s) locally with the editor of your choice
4.  Check your `git status` to see unstaged files
5.  Add your edited files: `git add path/to/filename.ext` You can also do: `git
    add .` to add all unstaged files. Take care, though, because you can
    accidentally add files you don't want added. Review your `git status` first.
6.  Commit your edits: `git commit -m "Brief description of commit"`.
7.  Squash your commits, if there are more than one
8.  Push your commits to your GitHub Fork: `git push -u origin branch/name-here`
9.  Once the edits have been committed, you will be prompted to create a pull
    request on your fork's GitHub page
10.  By default, all pull requests should be against the `master` branch
11.  Submit a pull request from your branch to recon-pipeline's `master` branch
12.  The title (also called the subject) of your PR should be descriptive of your
    changes and succinctly indicate what is being fixed
    -   Examples: `Add test cases for Unicode support`; `Correct typo in overview documentation`
13.  In the body of your PR include a more detailed summary of the changes you
    made and why
    -   If the PR is meant to fix an existing bug/issue, then, at the end of
        your PR's description, append the keyword `closes` and #xxxx (where xxxx
        is the issue number). Example: `closes #1337`. This tells GitHub to
        close the existing issue if the PR is merged.
14.  Indicate what local testing you have done (e.g. what OS and version(s) of Python did you run the
    unit test suite with)
15.  Creating the PR causes our continuous integration (CI) systems to automatically run all of the
    unit tests on all supported OSes and all supported versions of Python. You should watch your PR
    to make sure that all unit tests pass.
16.  If any unit tests fail, you should look at the details and fix the failures. You can then push
    the fix to the same branch in your fork. The PR will automatically get updated and the CI system
    will automatically run all of the unit tests again.

### How we review and merge pull requests

1. If your changes can merge without conflicts and all unit tests pass, then your pull request (PR) will have a big
green checkbox which says something like "All Checks Passed" next to it. If this is not the case, there will be a
link you can click on to get details regarding what the problem is.  It is your responsibility to make sure all unit
tests are passing.  Generally a Maintainer will not QA a pull request unless it can merge without conflicts and all
unit tests pass.

2. If a Maintainer reviews a pull request and confirms that the new code does what it is supposed to do without
seeming to introduce any new bugs, and doesn't present any backward compatibility issues, they will merge the pull request.

### Next steps

#### If your PR is accepted

Once your PR is accepted, you may delete the branch you created to submit it.
This keeps your working fork clean.

You can do this with a press of a button on the GitHub PR interface. You can
delete the local copy of the branch with: `git branch -D branch/to-delete-name`

#### If your PR is rejected

Don't worry! You will receive solid feedback from the Maintainers as to
why it was rejected and what changes are needed.

Many pull requests, especially first pull requests, require correction or
updating.

If you have a local copy of the repo, you can make the requested changes and
amend your commit with: `git commit --amend` This will update your existing
commit. When you push it to your fork you will need to do a force push to
overwrite your old commit: `git push --force`

Be sure to post in the PR conversation that you have made the requested changes.

### Other resources

-   [PEP 8 Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
-   [Searching for your issue on GitHub](https://help.github.com/articles/searching-issues/)
-   [Creating a new GitHub issue](https://help.github.com/articles/creating-an-issue/)

### Advice

Here is some advice regarding what makes a good pull request (PR) from our perspective:
- Multiple smaller PRs divided by topic are better than a single large PR containing a bunch of unrelated changes
- Good unit/functional tests are very important
- Accurate documentation is also important
- It's best to create a dedicated branch for a PR, use it only for that PR, and delete it once the PR has been merged
- It's good if the branch name is related to the PR contents, even if it's just "fix123" or "add_more_tests"
- Code coverage of the unit tests matters, so try not to decrease it
- Think twice before adding dependencies to third-party libraries (outside of the Python standard library) because it could affect a lot of users

## Acknowledgement
Thanks to the awesome guys at [cmd2](https://github.com/python-cmd2/cmd2) for their fantastic `CONTRIBUTING` file from
which we have borrowed heavily.
