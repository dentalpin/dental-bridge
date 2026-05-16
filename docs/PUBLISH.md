# Publishing `dental-bridge` to GitHub

> This is a one-shot operator runbook. Follow it once to take the
> repository public and produce the first signed release. The actions
> below modify shared state (GitHub.com) and are not reversible without
> manual cleanup.

## Pre-checks (do these once, locally)

```bash
cd /Users/ramonmartinez/Documents/gesden_explorer
git status                    # working tree should be clean (or close)
uv run pytest tests/unit -q   # 156 passing
uv run ruff check             # clean
uv run ruff format --check    # clean
```

If anything is dirty, fix it first.

## 1. Create the GitHub repo (private at first, on purpose)

Create the repo **private** so you can iterate before exposing it:

```bash
gh repo create dentalpin/dental-bridge \
    --private \
    --description "Open source migration toolkit for dental practice management systems. First connector: Gesdén." \
    --homepage "https://dentalpin.com" \
    --disable-issues=false \
    --disable-wiki=true
```

If the `dentalpin` organisation does not exist, replace it with your
GitHub username (and update the URLs in `pyproject.toml`,
`README.md`, `docs/windows-deployment.md` accordingly first).

## 2. Push the local repo

The local `gesden_explorer` directory contains the dental-bridge code.
We push it as `main`:

```bash
git remote add origin git@github.com:dentalpin/dental-bridge.git
git branch -M main
git add .
git commit -s -m "feat: dental-bridge 0.1.0 — first public release

The toolkit migrates dental practice data from a Gesdén SQL Server
database to a portable DPMF file via four CLI modes (analyze, plan,
extract, verify). Frozen DPMF spec v0.1.0; PyInstaller Windows
build via CI; CHANGELOG describes the full feature set.
"
git push -u origin main
```

The first push triggers `.github/workflows/ci.yml`. Watch it on the
Actions tab; the Windows build job should produce
`dental-bridge.exe` as an artifact within ~5 minutes.

## 3. Tag and trigger the first release

Once CI is green:

```bash
git tag -s v0.1.0 -m "v0.1.0 — first public release"
git push origin v0.1.0
```

The tag push triggers `.github/workflows/release.yml`. It:

1. Builds the Windows binary on a fresh `windows-latest` runner.
2. Renames it to `dental-bridge-0.1.0-windows-x64.exe`.
3. Computes SHA-256 and writes the sidecar.
4. Extracts the CHANGELOG section for `0.1.0`.
5. Creates a GitHub Release with the binary, the sidecar and the
   release notes.

If anything fails, fix the workflow, push, delete the tag (`git tag -d
v0.1.0 && git push :refs/tags/v0.1.0`), re-tag and re-push.

## 4. Make the repo public

Once the v0.1.0 release looks correct (binary downloads, SHA-256
verifies, README renders cleanly):

```bash
gh repo edit dentalpin/dental-bridge --visibility public --accept-visibility-change-consequences
```

Or from the GitHub web UI: Settings → Danger Zone → Change visibility.

## 5. Post-publish housekeeping

- Add a repository description and topics
  (`dental`, `migration`, `pms`, `gesden`, `etl`, `healthcare`).
- Pin the README on the org profile if `dentalpin` org.
- Enable Dependabot security updates.
- Add a security advisory address: Settings → Security → "Private
  vulnerability reporting".
- Optional but recommended: add a `CODEOWNERS` file listing the people
  who must approve PRs.

## 6. Announcing

Wait until at least one external person has reproduced a successful
`extract → verify` round-trip against their own Gesdén instance
before promoting widely. The README/docs presume working software, and
a first-issue avalanche from a botched release is hard to walk back.

Suggested first-touch channels once it's solid:

- LinkedIn post from Dentalpin company page.
- DM to two or three dental IT integrators in Spain.
- Show-HN once you have a screenshot of a real migration HTML report.

## Troubleshooting the release flow

| Symptom | Likely cause | Fix |
|---|---|---|
| CI fails on lint | Stray whitespace / new ruff rule | `uv run ruff format` locally, push again |
| Windows build fails on `pyinstaller` | Missing hiddenimport for a new module | Add it to `build/dental-bridge.spec` |
| Release workflow does not run | Tag does not match `v*.*.*` pattern | Tag must be SemVer-prefixed: `v0.1.0`, not `0.1.0` |
| `softprops/action-gh-release` errors | Token lacks `contents: write` | Workflow already declares `permissions: contents: write` — verify the org has not restricted token scopes |
| Release notes empty | `awk` did not find the `## [0.1.0]` heading | Confirm the CHANGELOG section uses `## [0.1.0]` (with brackets) |
