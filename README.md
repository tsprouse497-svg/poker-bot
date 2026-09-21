# Poker Bot

An offline-first deterministic bot that plays strong no-limit hold'em.
Training and coaching tools are backlogged until the bot plays well.
The boundaries on what it may do, and what lifts each one, are in `AGENTS.md`.

Agent behavior rules live in `AGENTS.md` (loaded by Claude Code via `CLAUDE.md`).
Phase progress lives in `phase_status.yml` and the generated `STATUS.md`.

## Verify

PowerShell:

```powershell
scripts/verify.ps1
```

POSIX shell:

```sh
scripts/verify.sh
```
