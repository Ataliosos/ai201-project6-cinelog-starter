"""
tests/test_watchlist.py — CineLog

Tests for the watchlist service.
"""

import pytest

from app import create_app, db
from models import User, Film, WatchlistEntry
from services.collection_service import FilmNotFoundError
from services.watchlist_service import (
    add_to_watchlist,
    remove_from_watchlist,
    update_watchlist_visibility,
    NotInWatchlistError,
)


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(
        config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """Create a user to use in watchlist tests."""
    with app.app_context():
        user = User(
            username="watchlistuser",
            email="watchlist@example.com",
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that does not exist should raise FilmNotFoundError.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(
                user_id=sample_user,
                film_id=fake_film_id,
            )


def test_remove_from_watchlist_removes_entry(app, sample_user):
    """
    Removing an existing watchlist entry should delete it from the database.
    """
    with app.app_context():
        film = Film(title="Arrival", year=2016)
        db.session.add(film)
        db.session.commit()

        add_to_watchlist(
            user_id=sample_user,
            film_id=film.id,
        )

        result = remove_from_watchlist(
            user_id=sample_user,
            film_id=film.id,
        )

        assert result is True

        entry = WatchlistEntry.query.filter_by(
            user_id=sample_user,
            film_id=film.id,
        ).first()

        assert entry is None


def test_remove_from_watchlist_missing_film_raises(app, sample_user):
    """
    Removing a film that is not on the watchlist should raise NotInWatchlistError.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NotInWatchlistError):
            remove_from_watchlist(
                user_id=sample_user,
                film_id=fake_film_id,
            )


def test_update_watchlist_visibility_changes_public_value(app, sample_user):
    """
    Updating visibility should change an existing entry from public to private.
    """
    with app.app_context():
        film = Film(title="HOUSE OF DAVID", year=2025)
        db.session.add(film)
        db.session.commit()

        add_to_watchlist(
            user_id=sample_user,
            film_id=film.id,
        )

        updated_entry = update_watchlist_visibility(
            user_id=sample_user,
            film_id=film.id,
            public=False,
        )

        assert updated_entry.public is False

        in_db = WatchlistEntry.query.filter_by(
            user_id=sample_user,
            film_id=film.id,
        ).first()

        assert in_db is not None
        assert in_db.public is False