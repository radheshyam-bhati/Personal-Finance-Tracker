# Contributing

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code |
| `develop` | Integration branch — all feature branches merge here first |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `chore/<name>` | Tooling, deps, docs |

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(auth): add login and registration endpoints
fix(analytics): handle empty DataFrame in get_monthly_trends
test(categorization): add unit tests for keyword rule matching
```

## Pull Request Process

1. Branch off `develop`, not `main`
2. Keep PRs focused — one feature or fix per PR
3. All tests must pass: `pytest --cov=app tests/`
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Request review before merging

## Local Setup

See [README.md](README.md#getting-started).
