"""Deterministic API regression and boundary tests; no persistent data touched."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from app import create_app, db
from models import User, Song, Tag, Playlist, ListeningEvent, Rating, Notification, playlist_entries

NOW = datetime(2024, 6, 16, 9, tzinfo=timezone.utc)  # Sunday

@pytest.fixture
def sample():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        owner = User(id='owner', username='owner', email='owner@example.test')
        friend = User(id='friend', username='friend', email='friend@example.test')
        stranger = User(id='stranger', username='stranger', email='stranger@example.test')
        owner.friends.append(friend)
        db.session.add_all([owner, friend, stranger])
        db.session.flush()
        songs = [Song(id=f's{i}', title=f'Anthem {i}', artist='Band', shared_by='owner') for i in range(3)]
        songs[0].tags = [Tag(name=x) for x in ('rap', 'hip-hop', 'soul')]
        songs[1].tags = [Tag(name='indie')]
        db.session.add_all(songs)
        db.session.add(Playlist(id='p', name='Friday Energy', created_by='owner'))
        db.session.commit()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_sunday_streak_api(sample):
    user = db.session.get(User, 'friend')
    user.listening_streak = 12
    user.last_listened_at = NOW - timedelta(days=1)
    db.session.commit()
    with patch('services.streak_service.datetime') as clock:
        clock.now.return_value = NOW
        assert sample.post('/songs/s0/listen', json={'user_id': 'friend'}).status_code == 201
        assert sample.get('/users/friend/streak').json['streak'] == 13
        sample.post('/songs/s0/listen', json={'user_id': 'friend'})
        assert sample.get('/users/friend/streak').json['streak'] == 13
        clock.now.return_value = NOW + timedelta(days=1)
        sample.post('/songs/s0/listen', json={'user_id': 'friend'})
        assert sample.get('/users/friend/streak').json['streak'] == 14
    assert ListeningEvent.query.count() == 3


@pytest.mark.parametrize('hour,minute,included', [(23,59,False), (0,0,True), (8,59,True)])
def test_feed_calendar_boundary(sample, hour, minute, included):
    date = NOW - timedelta(days=1) if hour == 23 else NOW
    db.session.add(ListeningEvent(user_id='friend', song_id='s0', listened_at=date.replace(hour=hour, minute=minute)))
    db.session.commit()
    with patch('services.feed_service.datetime') as clock:
        clock.now.return_value = NOW
        response = sample.get('/feed/owner/listening-now')
        assert response.status_code == 200
        assert response.json['count'] == int(included)
    assert sample.get('/feed/owner/activity').json['count'] == 1


def test_feed_latest_friend_only_and_empty(sample):
    for user, song, minutes in [('friend','s0',30), ('friend','s1',10), ('stranger','s2',5)]:
        db.session.add(ListeningEvent(user_id=user, song_id=song, listened_at=NOW-timedelta(minutes=minutes)))
    db.session.commit()
    with patch('services.feed_service.datetime') as clock:
        clock.now.return_value = NOW
        feed = sample.get('/feed/owner/listening-now').json
        assert feed['count'] == 1
        assert feed['feed'][0]['song']['id'] == 's1'
        assert sample.get('/feed/stranger/listening-now').json['count'] == 0
        assert sample.get('/feed/missing/listening-now').status_code == 404


def test_search_preserves_tags_and_distinct_songs(sample):
    results = sample.get('/songs/search?q=aNtHeM').json
    assert results['count'] == 3
    assert {s['id'] for s in results['results']} == {'s0','s1','s2'}
    by_id = {s['id']:s for s in results['results']}
    assert set(by_id['s0']['tags']) == {'rap','hip-hop','soul'}
    assert by_id['s2']['tags'] == []
    assert sample.get('/songs/search?q=Band').json['count'] == 3
    assert sample.get('/songs/search?q=unmatched').json['count'] == 0
    assert sample.get('/songs/search').status_code == 400


def test_rating_notification_and_updates(sample):
    response = sample.post('/songs/s0/rate', json={'user_id':'friend','score':5})
    assert response.status_code == 201
    notices = sample.get('/users/owner/notifications').json
    assert notices['count'] == 1
    notice = notices['notifications'][0]
    assert notice['type'] == 'song_rated'
    assert 'friend' in notice['body'] and 'Anthem 0' in notice['body'] and '5' in notice['body']
    assert sample.get('/users/friend/notifications').json['count'] == 0
    sample.post('/songs/s0/rate', json={'user_id':'friend','score':4})
    assert Rating.query.count() == 1
    assert Rating.query.one().score == 4
    assert Notification.query.count() == 2
    assert sample.post(f"/users/notifications/{notice['id']}/read").status_code == 200
    assert sample.get('/users/owner/notifications?unread_only=true').json['count'] == 1


def test_rating_self_and_invalid_inputs(sample):
    assert sample.post('/songs/s0/rate', json={'user_id':'owner','score':3}).status_code == 201
    for user,song,score in [('friend','s0',0),('friend','s0',6),('missing','s0',5),('friend','missing',5)]:
        assert sample.post(f'/songs/{song}/rate', json={'user_id':user,'score':score}).status_code == 400
    assert Notification.query.count() == 0
    assert Rating.query.count() == 1


@pytest.mark.parametrize('count', [0, 1, 3])
def test_playlist_boundaries_and_order(sample, count):
    for i in reversed(range(count)):
        db.session.execute(playlist_entries.insert().values(playlist_id='p',song_id=f's{i}',position=i+1,added_by='friend'))
    db.session.commit()
    response = sample.get('/playlists/p/songs')
    assert response.status_code == 200
    assert [s['id'] for s in response.json['songs']] == [f's{i}' for i in range(count)]
    assert response.json['count'] == count
    assert sample.get('/playlists/p').json['name'] == 'Friday Energy'
    assert sample.get('/playlists/missing/songs').status_code == 404


def test_playlist_add_workflow_and_notification(sample):
    for i in range(3):
        assert sample.post('/playlists/p/songs',json={'song_id':f's{i}','added_by':'friend'}).status_code == 201
        assert sample.get('/playlists/p/songs').json['count'] == i+1
    rows = db.session.execute(playlist_entries.select().order_by(playlist_entries.c.position)).all()
    assert [r.position for r in rows] == [1,2,3]
    assert all(r.added_by == 'friend' for r in rows)
    assert Notification.query.filter_by(notification_type='song_added_to_playlist').count() == 3
    assert sample.post('/playlists/p/songs',json={'song_id':'s2','added_by':'friend'}).status_code == 201
    assert sample.get('/playlists/p/songs').json['count'] == 3
    assert Notification.query.count() == 3
