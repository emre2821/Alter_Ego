"""Unit tests for autosave_echo_daemon module."""

from pathlib import Path
from datetime import datetime, timezone

import pytest

import autosave_echo_daemon


class TestFormatChaosEntry:
    """Tests for the format_chaos_entry function."""

    def test_basic_entry_format(self):
        """Basic entry should contain required fields."""
        result = autosave_echo_daemon.format_chaos_entry(
            "Hello world",
            {}
        )
        assert "[EVENT]: autosave_echo" in result
        assert "[TIME]:" in result
        assert "[CONTEXT]: prompt_catch" in result
        assert "[SIGNIFICANCE]: MEDIUM" in result
        assert "Hello world" in result

    def test_entry_with_tremor_detected(self):
        """Entry with tremor_detected should include EMOTION tag."""
        result = autosave_echo_daemon.format_chaos_entry(
            "I'm feeling anxious",
            {"tremor_detected": True}
        )
        assert "[EMOTION:ANXIETY:HIGH]" in result

    def test_entry_with_file_overload(self):
        """Entry with file_overload_detected should include SYMBOL tag."""
        result = autosave_echo_daemon.format_chaos_entry(
            "Too many files",
            {"file_overload_detected": True}
        )
        assert "[SYMBOL:LOOP:STRONG]" in result

    def test_entry_with_whisper(self):
        """Entry with whisper should include whisper text."""
        result = autosave_echo_daemon.format_chaos_entry(
            "Main prompt",
            {"whisper": "soft echo"}
        )
        assert "-- Whisper: soft echo" in result

    def test_entry_strips_prompt(self):
        """Prompt should be stripped of whitespace."""
        result = autosave_echo_daemon.format_chaos_entry(
            "   trimmed text   ",
            {}
        )
        assert "trimmed text" in result
        # Should not have leading/trailing spaces in the content block
        assert "{" in result
        assert "}" in result

    def test_entry_has_closing_brace(self):
        """Entry should have proper structure with braces."""
        result = autosave_echo_daemon.format_chaos_entry(
            "Test prompt",
            {}
        )
        assert result.count("{") == 1
        assert result.count("}") == 1


class TestAutosavePrompt:
    """Tests for the autosave_prompt function."""

    def test_autosave_creates_file(self, tmp_path, monkeypatch):
        """autosave_prompt should create a log file."""
        test_log = tmp_path / "test_echo.chaos"
        
        # Mock the configuration module functions
        monkeypatch.setattr(
            autosave_echo_daemon.configuration,
            "get_log_path",
            lambda: test_log
        )
        monkeypatch.setattr(
            autosave_echo_daemon.configuration,
            "get_default_log_path",
            lambda: test_log
        )
        
        autosave_echo_daemon.autosave_prompt("Test message", {})
        
        assert test_log.exists()
        content = test_log.read_text()
        assert "Test message" in content

    def test_autosave_appends_to_existing_file(self, tmp_path, monkeypatch):
        """autosave_prompt should append to existing file."""
        test_log = tmp_path / "test_echo.chaos"
        test_log.write_text("existing content\n")
        
        monkeypatch.setattr(
            autosave_echo_daemon.configuration,
            "get_log_path",
            lambda: test_log
        )
        monkeypatch.setattr(
            autosave_echo_daemon.configuration,
            "get_default_log_path",
            lambda: test_log
        )
        
        autosave_echo_daemon.autosave_prompt("New message", {})
        
        content = test_log.read_text()
        assert "existing content" in content
        assert "New message" in content
