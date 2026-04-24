"""
tests/test_incremental.py – tests for the hash-based incremental generation pipeline.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_incremental import file_hash, should_regenerate, load_cache, save_cache  # noqa: E402

PROTO_FILE = Path(__file__).parent.parent / "contracts" / "user" / "v1" / "user.proto"


class TestFileHash:
    def test_returns_hex_string(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        h = file_hash(str(f))
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("same content", encoding="utf-8")
        f2.write_text("same content", encoding="utf-8")
        assert file_hash(str(f1)) == file_hash(str(f2))

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("content A", encoding="utf-8")
        f2.write_text("content B", encoding="utf-8")
        assert file_hash(str(f1)) != file_hash(str(f2))


class TestShouldRegenerate:
    def test_new_file_should_regenerate(self, tmp_path):
        f = tmp_path / "test.proto"
        f.write_text("syntax = 'proto3';", encoding="utf-8")
        assert should_regenerate(str(f), {}) is True

    def test_unchanged_file_should_not_regenerate(self, tmp_path):
        f = tmp_path / "test.proto"
        f.write_text("syntax = 'proto3';", encoding="utf-8")
        cache = {str(f): file_hash(str(f))}
        assert should_regenerate(str(f), cache) is False

    def test_changed_file_should_regenerate(self, tmp_path):
        f = tmp_path / "test.proto"
        f.write_text("syntax = 'proto3';", encoding="utf-8")
        cache = {str(f): file_hash(str(f))}
        f.write_text("syntax = 'proto3'; // changed", encoding="utf-8")
        assert should_regenerate(str(f), cache) is True


class TestCachePersistence:
    def test_save_and_load_cache(self, tmp_path, monkeypatch):
        import generate_incremental as gi
        monkeypatch.setattr(gi, "CACHE_PATH", str(tmp_path / "cache.json"))

        original_cache = {"some/file.proto": "abc123"}
        save_cache(original_cache)
        loaded = load_cache()
        assert loaded == original_cache

    def test_load_cache_returns_empty_when_missing(self, tmp_path, monkeypatch):
        import generate_incremental as gi
        monkeypatch.setattr(gi, "CACHE_PATH", str(tmp_path / "nonexistent.json"))
        assert load_cache() == {}
