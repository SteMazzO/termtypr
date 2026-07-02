"""Tests for WordStorage bundled + user word handling."""

import json

import pytest

from termtypr.data.word_storage import WordStorage


@pytest.fixture
def bundled_file(tmp_path):
    """A words file standing in for the read-only bundled list."""
    path = tmp_path / "words.json"
    path.write_text(json.dumps({"words": ["alpha", "bravo"]}), encoding="utf-8")
    return path


@pytest.fixture
def user_file(tmp_path):
    """Path for the writable user words file (not created yet)."""
    return tmp_path / "data" / "custom_words.json"


@pytest.fixture
def storage(bundled_file, user_file):
    """WordStorage wired to the temp bundled and user files."""
    return WordStorage(words_file=bundled_file, user_words_file=user_file)


class TestGetWords:
    """Tests for reading and merging word lists."""

    def test_bundled_words_only(self, storage):
        """Without a user file, only bundled words are returned."""
        assert storage.get_words() == ["alpha", "bravo"]

    def test_merges_user_words(self, storage, user_file):
        """User words are appended after bundled words."""
        user_file.parent.mkdir(parents=True)
        user_file.write_text(json.dumps({"words": ["charlie"]}), encoding="utf-8")

        assert storage.get_words() == ["alpha", "bravo", "charlie"]

    def test_deduplicates_across_sources(self, storage, user_file):
        """Words present in both sources appear once."""
        user_file.parent.mkdir(parents=True)
        user_file.write_text(
            json.dumps({"words": ["bravo", "charlie"]}), encoding="utf-8"
        )

        assert storage.get_words() == ["alpha", "bravo", "charlie"]

    def test_missing_files_return_empty(self, tmp_path):
        """Nonexistent files yield an empty word list."""
        storage = WordStorage(
            words_file=tmp_path / "missing.json",
            user_words_file=tmp_path / "also_missing.json",
        )
        assert storage.get_words() == []

    def test_corrupt_file_returns_empty(self, tmp_path, user_file):
        """A corrupt words file is treated as empty instead of crashing."""
        corrupt = tmp_path / "corrupt.json"
        corrupt.write_text("{not valid json", encoding="utf-8")
        storage = WordStorage(words_file=corrupt, user_words_file=user_file)

        assert storage.get_words() == []


class TestAddWords:
    """Tests for adding words to the user file."""

    def test_writes_to_user_file_not_bundled(self, storage, bundled_file, user_file):
        """New words go to the user file; the bundled file is untouched."""
        assert storage.add_words(["charlie"]) is True

        bundled = json.loads(bundled_file.read_text(encoding="utf-8"))
        custom = json.loads(user_file.read_text(encoding="utf-8"))
        assert bundled == {"words": ["alpha", "bravo"]}
        assert custom == {"words": ["charlie"]}
        assert storage.get_words() == ["alpha", "bravo", "charlie"]

    def test_creates_parent_directory(self, storage, user_file):
        """The user data directory is created when missing."""
        assert not user_file.parent.exists()
        assert storage.add_words(["charlie"]) is True
        assert user_file.exists()

    def test_skips_words_already_bundled(self, storage, user_file):
        """Words already in the bundled list aren't duplicated."""
        assert storage.add_words(["alpha", "charlie"]) is True

        custom = json.loads(user_file.read_text(encoding="utf-8"))
        assert custom == {"words": ["charlie"]}

    def test_appends_to_existing_user_words(self, storage):
        """Adding twice accumulates without duplicates."""
        storage.add_words(["charlie"])
        storage.add_words(["charlie", "delta"])

        assert storage.get_words() == ["alpha", "bravo", "charlie", "delta"]

    def test_returns_false_on_write_error(self, bundled_file, tmp_path):
        """An unwritable user file path reports failure instead of raising."""
        # A directory in place of the file makes open(..., 'w') fail
        storage = WordStorage(words_file=bundled_file, user_words_file=tmp_path)

        assert storage.add_words(["charlie"]) is False
