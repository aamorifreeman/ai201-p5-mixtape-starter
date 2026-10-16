# Project 5 — Mixtape Bug Hunt

## AI usage and authorship

Aamori requested that Codex complete the implementation. Codex inspected the authenticated assignment and rubric, read the starter README, models, routes, and services, and prepared this architecture map before modifying application code. Subsequent investigation, code, tests, and documentation are AI-assisted work. This document reports actions performed by Codex; it does not claim Aamori personally performed them. Student review is still required before submission.

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
