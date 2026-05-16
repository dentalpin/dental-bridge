# Renaming this repository: `gesden_explorer` → `dental-bridge`

Per the project plan, the working directory `gesden_explorer/` is the
former exploration project that has evolved into the `dental-bridge`
product repository. The directory rename has to be performed manually
because it changes Claude Code's working path. Two steps:

## 1. Rename the local directory

From the **parent** directory (`~/Documents`):

```bash
cd ~/Documents
mv gesden_explorer dental-bridge
cd dental-bridge
```

After this, reopen Claude Code in the new path. Any open shell sessions or
editors pointed at the old path will need to be redirected.

## 2. Update the git remote (when you push)

This repository currently has no `origin` remote configured (it has only a
local initial commit). When you create the GitHub repo for the product,
suggest:

```bash
gh repo create dentalpin/dental-bridge --public --source=. --remote=origin --push
```

Or, if the GitHub repo is created in the web UI first:

```bash
git remote add origin git@github.com:dentalpin/dental-bridge.git
git branch -M main
git push -u origin main
```

## 3. Verify

After the rename:

```bash
# you should be inside dental-bridge/ now
basename "$PWD"     # → dental-bridge
git log --oneline   # the initial commit is still here
ls -la              # the same files, plus the Sprint 0 additions
```

## Why the rename was deferred

The Sprint 0 scaffolding was performed inside the existing
`gesden_explorer/` directory because directory moves change the path
Claude Code operates against. The contents are already structured as
`dental-bridge`: package name, project name, README, license, scripts and
specs all use the new identifiers. The only thing left is the physical
directory name and the eventual git remote — both safer to do
interactively from the user's shell.
