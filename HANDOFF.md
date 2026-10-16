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
- [x] User-supplied git-log screenshot inspected and saved unchanged as `evidence/git-log.png`; branch and all separate fixes are visible.
- [x] Personal check: completed (confirmed by the author).
- [x] Added an evidence-based Sunday-streak example summarizing recorded project tests.
- [x] Course-required public fork created at https://github.com/aamorifreeman/ai201-p5-mixtape-starter .
- [ ] Submit the published branch URL yourself, with the included commit-history screenshot. Nothing has been submitted to the course.

## GitHub delivery

Repository: https://github.com/aamorifreeman/ai201-p5-mixtape-starter

Assignment branch: https://github.com/aamorifreeman/ai201-p5-mixtape-starter/tree/bugfix/mixtape

The fork's `main` retains the official starter. All completed work is on `bugfix/mixtape`, with separate fixes preserved. The local `my-fork` remote points to your fork; `origin` remains CodePath's upstream. Do not squash the fix commits. Use the branch URL above in the portal, not the bare repository URL.

The commit-history screenshot is complete. Personal check: completed (confirmed by the author). The AI-usage documentation also includes an evidence-based Sunday-streak example. Submit the branch URL/documentation and included screenshot yourself. No video demo is required by the Unit 5 brief.

```sh
git log --oneline --decorate -12
```

## Verification and limitations

Original suite: 4 failed / 9 passed. Added suite before fixes: 7 failed / 5 passed. Final suite: 25 passed. HTTP smoke check on the actual Flask development server returned one Crown Heights Anthem result with all three tags. Browser automation blocked the loopback URL, so the live HTTP check used curl; all API mutation checks used Flask's isolated test client.

The implementation follows the starter's UTC calendar convention and local single-process assumptions. It does not add authentication, production concurrency guarantees, or a frontend. The authenticated assignment showed a due date of October 14 at 11:59 PM EDT; any late-submission arrangements are for the student/instructor.
