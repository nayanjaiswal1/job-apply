# Job Hunting Agent

LangGraph multi-agent system that searches, scores, tailors, applies, tracks, and follows up across job platforms.

## Files

- `CLAUDE.md` — conventions and quality bars, auto-loaded by Claude Code each session
- `STATE.md` — current phase + task pointer
- `plans/phase-{1..5}.md` — per-phase tasks + exit criteria
- `REQUIREMENTS.md` — full spec (architecture, agents, schemas)
- `.claude/settings.json` — pre-approved safe commands

## Using with Claude Code

Open this folder in Claude Code. `CLAUDE.md` + `STATE.md` load automatically. Tell it "continue" — it reads the active phase file and works the first unchecked task.

End of session: ask it to update `STATE.md` and commit.

## Status

Phase 1 not started. See `plans/phase-1.md`.
