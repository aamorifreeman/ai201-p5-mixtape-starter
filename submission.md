# Project 5 — Mixtape Bug Hunt

## AI usage and authorship

Aamori requested that Codex complete the implementation. Codex inspected the authenticated assignment and rubric, read the starter README, models, routes, and services, and prepared this architecture map before modifying application code. Subsequent investigation, code, tests, and documentation are AI-assisted work. This document reports actions performed by Codex; it does not claim Aamori personally performed them. Student review is still required before submission.

### Specific AI work and verification

1. **Architecture and execution tracing:** The request directed Codex to inspect the real assignment and starter. Codex traced the rating endpoint through `rate_song()`, compared it with the playlist notification path, and identified the absent notification call. The saved-rating/empty-notification API reproduction verified that explanation instead of accepting it from code inspection alone.
2. **Boundary and query debugging:** Codex inspected the streak weekday condition, feed cutoff, and search join, then authored deterministic tests to check Sunday, midnight, and tag cardinality. Tests failed against the unchanged starter before the targeted fixes and passed afterward.
3. **Correction during validation:** The expected playlist-add workflow could not run because the starter relationship append omitted required association metadata. The actual IntegrityError disproved the assumption that only retrieval needed repair. Codex added a separate insertion fix and verified ordering and notifications through the API.

These are agent-performed checks. Aamori's personal review is not represented as completed; see the student review section at the end.

## Codebase map

This architectural orientation was recorded before bug reproduction and implementation.

| File or group | Responsibility and connections |
|---|---|
| `app.py` | Defines the shared SQLAlchemy extension and `create_app(config)` factory; configures SQLite, registers four route blueprints, and creates tables. Test configuration can select an in-memory database. |
| `models.py` | Defines User, Tag, Song, ListeningEvent, Rating, Playlist, and Notification. UUIDs identify rows. `friendships` links users, `song_tags` links songs and tags, and `playlist_entries` stores song membership with position, adding user, and timestamp. Rating has a unique user/song constraint. Model `to_dict()` methods shape JSON. |
| `routes/songs.py` | Parses search queries and rating/listening JSON, delegates to search, notification, and streak services, and serializes service results. |
| `routes/playlists.py` | Exposes playlist creation, metadata, ordered songs, and adding a song. Delegates reads to playlist service and additions to notification service. |
| `routes/users.py` | Provides profiles, streaks, notification lists, unread filtering, and marking notifications read. |
| `routes/feed.py` | Provides listening-now and activity endpoints, returning a feed and its count. |
| `services/streak_service.py` | Records listening events, updates stored streak state using calendar dates, and retrieves the stored streak. |
| `services/feed_service.py` | Queries friends' listening events, sorts newest first, and produces either one latest entry per friend or a general limited activity list. |
| `services/search_service.py` | Searches title/artist case-insensitively and returns serialized songs including tags; also retrieves individual songs. |
| `services/notification_service.py` | Persists ratings and playlist additions, creates notifications, retrieves notification lists, and changes read state. |
| `services/playlist_service.py` | Creates playlists, retrieves metadata, queries song membership ordered by its explicit position, and lists a user's playlists. |
| `seed_data.py` | Recreates the configured database with sample users, friendships, tags, songs, playlists, events, and a notification. It is a destructive reset of that database and is only used for this new project's local sample database. |
| `tests/` | Pytest fixtures create isolated in-memory databases; existing tests exercise streak rules, tag-count variations in search, and playlist membership/order. |

### Data flow: rating a song

`POST /songs/<song_id>/rate` enters `routes/songs.rate()`. The route extracts `user_id` and `score`, checks required fields, converts the score to an integer, and calls `notification_service.rate_song()`. The service validates the score range, loads Song and User by UUID, looks for the user's existing Rating for that song, and updates it or adds a new Rating. SQLAlchemy persists the transaction. The returned Rating's `to_dict()` becomes a JSON response with status 201; validation errors become status 400.

### Organization patterns

Routes handle HTTP parsing and response formatting; services contain business logic and database queries. Models centralize relationships and serialization. The application factory supports isolated test databases. Time-producing code uses UTC, while SQLite DateTime retrieval may yield naive datetimes representing UTC. Playlist order is explicit data in the association table, not the order of song IDs.

## Root cause analyses

**Issue #1 — My listening streak keeps resetting**

- **How you reproduced it:** Before fixes, the original Sunday test failed with 1 instead of 2. The added API test sets a stored streak of 12 and a Saturday timestamp, freezes the clock at Sunday June 16, 2024 09:00 UTC, posts a listen, then fetches the streak. It returned 1 instead of 13 (`evidence/baseline-regressions.txt`).
- **How you found the root cause:** Codex traced `routes/songs.listen()` → `record_listening_event()` → `update_listening_streak()`, then checked the stored result through `routes/users.streak()` → `get_streak()`. The consecutive-day branch explicitly excluded weekday 6; the controlled Sunday failure confirmed this condition, rather than persistence or the GET endpoint, caused the reset.
- **The root cause:** `days_since_last == 1 and today.weekday() != 6` rejects Sunday even when the calendar date difference is exactly one. Sunday therefore falls into the reset branch. Consecutive-day counting must depend on elapsed calendar dates, not the weekday number.
- **Your fix:** Removed the Sunday exclusion; all one-day differences increment the streak.
- **Your side-effect check:** All five original streak tests and the new API test pass (6 total). These cover first listen, ordinary consecutive days, skipped days, Saturday→Sunday→Monday, same-day repeats, and event persistence (three listens still create three events while counting only two new days).

**Issue #2 — Friends Listening Now shows people from yesterday**

- **How you reproduced it:** At a frozen Sunday 09:00 UTC, inserted a friend's listen from Saturday 23:59 and requested `/feed/owner/listening-now`. Before the fix its count was 1; expected 0. Fixtures use an isolated in-memory database rather than relying on the wall clock or seed timing.
- **How you found the root cause:** Codex followed `routes/feed.listening_now()` into `get_friends_listening_now()`, then inspected the event timestamp filter, ordering, and per-friend deduplication. The failing fixture was newer than the computed 24-hour cutoff but older than midnight, isolating the cutoff as the cause.
- **The root cause:** Subtracting `RECENT_THRESHOLD` (24 hours) creates a rolling interval. Yesterday at 23:59 is still inside that interval at 09:00 today, although it is not on today's calendar date. The app uses UTC timestamps and has no user timezone field, so the calendar boundary is UTC midnight.
- **Your fix:** Compute today's midnight UTC with `replace(hour=0, minute=0, second=0, microsecond=0)` and retain the inclusive `>=` timestamp filter. Removed the unused rolling-threshold constant/import and clarified the docstring.
- **Your side-effect check:** Four feed test cases pass: yesterday 23:59 excluded, midnight included, today 08:59 included, and multiple events reduced to the latest per friend. The tests also verify strangers are excluded, friendless users get an empty list, missing users get 404, and the general activity feed still includes yesterday's event.

**Issue #3 — The same song keeps showing up twice in search**

- **How you reproduced it:** The original three-tag Crown Heights test returned three copies instead of one. The added `/songs/search?q=aNtHeM` test seeds three different songs with three, one, and zero tags; the response contained five entries instead of three before the fix.
- **How you found the root cause:** Codex followed `routes/songs.search()` → `search_service.search_songs()` → `Song.to_dict()` and the `Song.tags` relationship in `models.py`. The SQL outer join produces one row per tag, and `execute(...).scalars().all()` preserves these repeated Song results. The reproduction's 3+1+1 count matches the join cardinality exactly.
- **The root cause:** Joining `song_tags` multiplies matching rows for multi-tag songs even though neither filtering nor serialization requires that join. Zero-tag songs get one outer-join row, one-tag songs get one row, and three-tag songs get three. It is not a second HTTP request or repeated seed insertion.
- **Your fix:** Removed the unnecessary outer join and unused imports. The query selects songs directly; SQLAlchemy's existing `Song.tags` relationship still supplies every tag for serialization. Different songs remain separate even if their titles match.
- **Your side-effect check:** All five original search tests and the new API test pass (6 total). Verified zero/one/multiple tags, full tag preservation, case-insensitive title and artist matches, no matches, and a missing query returning 400.

**Issue #4 — I got notified when a friend added my song to a playlist but not when they rated it**

- **How you reproduced it:** Posted a 5-star rating by `friend` for `owner`'s song through `/songs/s0/rate`. The endpoint returned 201 and stored the rating, but `/users/owner/notifications` returned count 0 instead of 1. The baseline log records this failure.
- **How you found the root cause:** Codex traced the rating route into `notification_service.rate_song()`, compared that function with `add_to_playlist()` and `create_notification()` in the same module, and followed notification retrieval through `routes/users.py`. The rating was persisted, but its service never called the helper that creates Notification rows; the empty list was therefore not a retrieval-filter problem.
- **The root cause:** Rating persistence and notification generation are separate operations in the service layer. The playlist path explicitly invokes `create_notification()` for the song sharer, while the rating path committed and immediately returned. Saving a Rating has no model hook that automatically creates a notification.
- **Your fix:** After saving the rating, call the existing helper with type `song_rated`, recipient `song.shared_by`, and a body identifying the rater, song, and score. Follow the existing self-interaction exclusion. Both new ratings and score updates notify the sharer; updates still reuse the original Rating row.
- **Your side-effect check:** Both rating tests pass. They verify recipient/type/body, rating updates without duplicate Rating rows, no self-notifications, rejection of scores 0/6 and nonexistent users/songs, and read/unread filtering. Playlist notification coverage is also included in the related insertion test below.

**Issue #5 — The last song in a playlist never shows up**

- **How you reproduced it:** Before fixes, the original five-song fixture returned only four songs. The added API tests directly populate ordered association rows: a one-song playlist returned an empty list and a three-song playlist returned two songs. Direct insertion isolated retrieval from the separate insertion failure.
- **How you found the root cause:** Codex followed `routes/playlists.get_songs()` into `playlist_service.get_playlist_songs()`, checked the membership join and ascending position sort, then inspected the final list comprehension. The query returns every row, but serialization slices off the last element. A single-song fixture becoming empty confirms the loss occurs after querying.
- **The root cause:** `songs[:-1]` excludes the final element of the already ordered result. The highest-position song is always missing; when another entry is added, the previously final song moves inside the slice and the new one becomes excluded.
- **Your fix:** Serialize the whole `songs` list, preserving the existing ordering query and response shape.
- **Your side-effect check:** Six playlist retrieval tests pass (three original plus empty/single/multiple API cases). New fixtures insert rows in reverse order to verify sorting is by position rather than insertion order. They also check metadata and 404 behavior. The add-and-re-fetch path required the related repair below before its end-to-end test could pass.

### Related repair — playlist insertion required by the reproduction workflow

The baseline API add test raised `IntegrityError: NOT NULL constraint failed: playlist_entries.position`. Tracing `routes/playlists.add_song()` → `notification_service.add_to_playlist()` → `models.playlist_entries` showed that `playlist.songs.append(song)` supplies membership IDs but not mandatory `position` or `added_by`. Replaced that append with an explicit association-table insert, using the playlist's maximum position plus one and the supplied adding user. Re-adding a song returns without inserting or notifying again. This repair is a separate sixth fix commit rather than being hidden in one of the five required fixes.

The end-to-end regression adds three songs through HTTP routes, re-fetches after every add, checks all songs are visible, confirms positions 1/2/3 and adding-user metadata, checks playlist-add notifications, and verifies repeated addition does not duplicate membership or notifications. All 25 tests pass after this repair. This retains the starter's single-process local-app assumptions; concurrent writers would need stronger ordering/transaction design for a production deployment.

## Regression tests and evidence

Run `.venv/bin/python -m pytest tests/ -q` from the repository root. `tests/test_regressions.py` adds 12 deterministic cases to the original 13 tests, using independent in-memory databases and frozen service clocks. Before implementation, 7 new cases failed and 5 passed; after implementation all 25 pass. In particular, `test_feed_calendar_boundary[23-59-False]` would catch the rolling-24-hour bug: it failed before the midnight fix and passes afterward. The suite also demonstrates all five reported failures and checks nearby behavior.

- `evidence/baseline-tests.txt`: actual original-suite output, 4 failed / 9 passed.
- `evidence/baseline-regressions.txt`: actual pre-fix new-suite output, 7 failed / 5 passed.
- `evidence/final-tests.txt`: actual final full-suite output.
- `evidence/git-log.txt`: actual `git log --oneline --decorate -10` output, including all six separate fix commits.
- `evidence/http-search.json`: actual live-server search response.
- Required screenshot remains user-only: computer-use policy blocked Terminal access and browser policy blocked displaying the local log file. No screenshot was fabricated. Run `git log --oneline --decorate -10` locally and capture it before submitting.

## Student review before submission

No first-person learning experience or personal verification is asserted here. The rubric asks for an instance where the student verified an AI explanation. Aamori must personally review and then describe one real check, for example running the Sunday test and inspecting the removed weekday condition, or inspecting the before/after feed boundary output. Add what was checked and what was concluded only after doing it. This personal verification point cannot honestly be completed by an autonomous agent on the student's behalf.
