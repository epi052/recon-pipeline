# Landing a Pull Request (PR)

Long form explanations of most of the items below can be found in the [CONTRIBUTING](https://github.com/epi052/recon-pipeline/blob/master/CONTRIBUTING.md) guide.

## Branching checklist
- [ ] There is an issue associated with your PR (bug, feature, etc.. if not, create one)
- [ ] Your PR description references the associated issue (i.e. fixes #123)
- [ ] Code is in its own branch
- [ ] Branch name is related to the PR contents
- [ ] PR targets master
- [ ] Option to squash commits is checked

## Static analysis checks
- [ ] All python files are formatted using black
- [ ] All flake8 checks pass
- [ ] All existing tests pass

## Documentation
- [ ] Documentation about your PR is included in docs/ and the README, as appropriate

## Additional Tests
- [ ] New code is unit tested
- [ ] New tests pass
