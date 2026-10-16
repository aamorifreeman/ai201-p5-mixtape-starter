# Unit 5 rubric and delivery status

Source: authenticated CodePath AI201 Unit 5 project and grading page, inspected October 16, 2026.
Project: Mixtape Bug Hunt. Maximum: 25 required points + 3 stretch points.
This is an evidence mapping, not a guaranteed grade or a claim of 28/28.

| Required category | Points | Evidence and status |
|---|---:|---|
| Codebase Map | 3 | `submission.md` names main files and responsibilities (1), traces rating data flow (1), and has an architecture-only map committed before bug work (1), commit `6edd05c`. Prepared. |
| Bug Fix Completeness | 4 | Five issue-numbered RCA entries each include reproduction, navigation, cause, fix, side-effect check (2); substantive explanations (1); clear issue organization (1). Prepared. |
| Root Cause Quality | 5 | At least three specific conditions/functions (2); at least two named mechanisms tied to trigger conditions (2); causal reasoning about date differences, join cardinality and final-element slicing (1). Prepared. |
| Navigation Strategy | 4 | All five entries trace route → service → relevant model/query (2), with deliberate investigation and baseline test evidence (2). These actions were performed by Codex and disclosed, not falsely attributed to the student. |
| Side-Effect Check | 3 | At least three specific related checks (2); API persistence, read/unread behavior, preserved tags and ordering go beyond startup (1). Prepared; 25 tests pass. |
| Commit History | 3 | Actual local history identifies `bugfix/mixtape` (1), separate fixes (1), specific conventional `fix:` messages (1). Text evidence and full Git bundle included. Public fork created for aamorifreeman; branch publication is part of this delivery. Required screenshot remains pending. |
| AI Usage | 3 | At least two specific navigation/debugging uses (1), specific collaboration detail (1), documented student verification/correction (1). Specific uses and agent verification are documented. Aamori reports that her professor waived the personal-verification requirement; no student verification is fabricated. |

## Stretch mapping

| Stretch | Points | Status |
|---|---:|---|
| Fix a fourth bug | +1 | Code, complete RCA and separate commit prepared. The rubric also asks that its commit be visible in the git-log screenshot; screenshot pending. |
| Fix all five bugs | +1 | All five fixes, complete RCAs and separate commits prepared. Depends on fourth-bug stretch; screenshot pending. |
| Regression test | +1 | Satisfied in the local project: 12 new deterministic cases in `tests/test_regressions.py`, referenced and explained in `submission.md`; actual pre-fix failure output and post-fix pass output included. |

No video demo is required. The course-required public fork is https://github.com/aamorifreeman/ai201-p5-mixtape-starter and the assignment branch URL is https://github.com/aamorifreeman/ai201-p5-mixtape-starter/tree/bugfix/mixtape . No course submission has been made. Final grading remains the instructor's decision; the screenshot evidence is still pending.

## Exact final steps for Aamori

1. In Terminal, run the following and take a screenshot showing the branch and separate fix commits:

   ```sh
   cd /Users/aamorifreeman/Documents/Codex/2026-10-16/task/ai201-p5-mixtape-starter
   git log --oneline --decorate -12
   ```

   Screenshot is intentionally absent: tool policy blocked Terminal capture and local-file browser display. No alternative capture route was used after those denials.
2. Submit https://github.com/aamorifreeman/ai201-p5-mixtape-starter/tree/bugfix/mixtape , `submission.md`, and the screenshot yourself. Per the instructor clarification, no personal AI-verification statement is required.

## Archive layout and portable setup

`ai201-p5-mixtape-starter/` contains the tracked source, tests, documentation and evidence. `.venv`, caches, databases, `.env`, `.git` metadata, and credentials are excluded. `mixtape-unit5.bundle` preserves the complete Git history and branch; it passed `git bundle verify` before packaging.

To recover the repository with its graded commit history on another computer:

```sh
git clone -b bugfix/mixtape mixtape-unit5.bundle mixtape-restored
cd mixtape-restored
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
python seed_data.py
python -m pytest tests/ -q
FLASK_APP=app:create_app flask run --port 5055
```

The bundle restores the published `bugfix/mixtape` delivery history. The ZIP also includes this packaging checklist outside the repo; a copy is tracked in the repository. Do not merely upload the source folder as one new commit: that would lose the required separate fix history.
