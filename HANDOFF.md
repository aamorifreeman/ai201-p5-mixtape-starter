# Mixtape Unit 5 — local handoff

## Open and run

```sh
cd /Users/aamorifreeman/Documents/Codex/2026-10-16/task/ai201-p5-mixtape-starter
source .venv/bin/activate
python -m pytest tests/ -q
FLASK_APP=app:create_app flask run --host 127.0.0.1 --port 5055
```

Open http://127.0.0.1:5055/songs/search?q=Anthem . This starter is a JSON API, not a web frontend; `/` has no route and returns 404. Port 5055 avoids the common macOS port-5000 conflict. Do not use `python app.py`.

The isolated `.venv` and sample SQLite database are already prepared. On another computer, create a Python 3.13 virtual environment and install `pip install -r requirements-lock.txt` (exact versions used here). `requirements.txt` remains the starter's supported minimum list. Run `python seed_data.py` only to recreate disposable sample data: it drops all tables in the configured database.

## Requirements checklist

- [x] Official starter cloned; original history retained; unrelated projects untouched.
- [x] Local `bugfix/mixtape` branch.
- [x] Architecture-only codebase map committed before bug work.
- [x] All five bugs reproduced before code changes.
- [x] All five bugs fixed, each in its own descriptive `fix:` commit.
- [x] Five complete root cause analyses in root `submission.md`.
- [x] Stretch: fourth and fifth fixes plus new regression tests.
- [x] Separate repair for playlist insertion discovered during reproduction.
- [x] 25 tests pass; actual before/after output saved in `evidence/`.
- [x] Honest AI disclosure at the top of `submission.md`.
- [ ] Capture `git log --oneline --decorate -10` in Terminal. The exact text is in `evidence/git-log.txt`; screenshot capture was blocked by tool policy.
- [ ] Aamori personally verifies one AI explanation and adds a truthful account to the AI usage section (rubric asks for student verification).
- [ ] Fork/push on GitHub and submit the branch URL yourself. No repository has been published and nothing has been submitted.

## Publishing later — only when you choose

Fork https://github.com/codepath/ai201-p5-mixtape-starter in your own GitHub account. Add that fork as a new remote in this local clone, then push the existing branch (do not squash the individual fixes):

```sh
git remote add my-fork https://github.com/YOUR-USERNAME/ai201-p5-mixtape-starter.git
git push -u my-fork bugfix/mixtape
```

Replace YOUR-USERNAME with your actual account. The original `origin` points to CodePath and has not been changed. Use your fork's URL ending `/tree/bugfix/mixtape` in the portal, not the bare repository URL. Include `submission.md` and the required commit-history screenshot. No video demo is required by Unit 5's project brief.

## Verification and limitations

Original suite: 4 failed / 9 passed. Added suite before fixes: 7 failed / 5 passed. Final suite: 25 passed. HTTP smoke check on the actual Flask development server returned one Crown Heights Anthem result with all three tags. Browser automation blocked the loopback URL, so the live HTTP check used curl; all API mutation checks used Flask's isolated test client.

The implementation follows the starter's UTC calendar convention and local single-process assumptions. It does not add authentication, production concurrency guarantees, or a frontend. The authenticated assignment showed a due date of October 14 at 11:59 PM EDT; any late-submission arrangements are for the student/instructor.
