# Contributing to RelayDesk

Thanks for taking the time to contribute! RelayDesk thrives when community members share ideas, fixes, and features. This guide outlines how to set up your environment, follow our conventions, and submit high-quality pull requests.

## Prerequisites

- Python 3.12
- Node.js 20
- pnpm (preferred package manager)
- Docker + Docker Compose

## Local Setup

```bash
git clone https://github.com/<org>/RelayDesk.git
cd RelayDesk
make be-install    # creates virtualenv and installs backend deps
make fe-install    # installs frontend deps with pnpm
make be-migrate    # apply migrations
make be-run        # optional: run Django dev server
make fe-dev        # optional: run Next.js dev server
```

## Branching Strategy

- `feature/<short-description>` for new features.
- `fix/<short-description>` for bug fixes.
- `docs/<short-description>` for documentation updates.

Please base branches off `main` (or the active release branch) and keep them short-lived.

## Code Style & Tooling

- **Backend (Django):** `black`, `ruff`, and `mypy` enforce formatting, linting, and type safety.
- **Frontend (Next.js):** `eslint` and `prettier` ensure consistent TypeScript/React formatting.

Run these before committing:

```bash
make be-lint   # runs black, ruff, mypy
make fe-lint   # runs ESLint + Prettier
```

## Testing & Coverage

Backend:

```bash
make be-test                # pytest with coverage
pytest --cov=chat --cov=relaydesk --cov-report=term-missing
```

Frontend:

```bash
make fe-test                # pnpm test -- --coverage --runInBand
pnpm test -- --coverage --runInBand
```

We aim to keep backend coverage ≥85% and frontend coverage ≥80%. Please update or add tests alongside your changes.

## Commit Messages

RelayDesk follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(scope?): <short summary>

fix(auth): handle refresh token rotation
feat(chat): add presence endpoint
docs: update README quick start
```

Types commonly used: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`.

## Pull Request Guidelines

- Keep PRs focused and reasonably small.
- Ensure all linting and tests pass locally.
- Add or update documentation and changelog entries when the user-facing behavior changes.
- Request review from at least one maintainer.
- Reference related issues in the PR body (e.g., “Closes #42”).

## Running CI/CD Locally

Our GitHub Actions workflows mirror the commands above:

- **backend.yml** runs migrations, pytest (with coverage), and uploads artifacts.
- **frontend.yml** runs pnpm install, lint, tests (with coverage), and build.

If these commands succeed locally (`make be-test`, `make fe-test`, `make be-lint`, `make fe-lint`), CI should pass as well.

## Need Help?

Open a GitHub discussion or issue, or email the maintainers at [support@relaydesk.dev](mailto:support@relaydesk.dev). We’re happy to help clarify scope, provide feedback, or pair on larger features.
