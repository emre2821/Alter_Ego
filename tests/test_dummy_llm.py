"""Unit tests for dummy_llm module."""

from pathlib import Path

import pytest

from dummy_llm import DummyLLM, DummyRule, DummyScriptLibrary, DEFAULT_DATA


class TestDummyRule:
    """Tests for the DummyRule dataclass."""

    def test_matches_any_keyword(self):
        """Rule should match when any keyword is present."""
        rule = DummyRule(
            name="test",
            response="test response",
            persona_overrides={},
            any_keywords=["hello", "hi", "greet"],
            all_keywords=[],
            exclude_keywords=[],
        )
        assert rule.matches("hello world")
        assert rule.matches("hi there")
        assert not rule.matches("goodbye")

    def test_matches_all_keywords(self):
        """Rule should match only when all keywords are present."""
        rule = DummyRule(
            name="test",
            response="test response",
            persona_overrides={},
            any_keywords=[],
            all_keywords=["hello", "world"],
            exclude_keywords=[],
        )
        assert rule.matches("hello world")
        assert not rule.matches("hello there")
        assert not rule.matches("goodbye world")

    def test_excludes_keywords(self):
        """Rule should not match when exclude keywords are present."""
        rule = DummyRule(
            name="test",
            response="test response",
            persona_overrides={},
            any_keywords=["hello"],
            all_keywords=[],
            exclude_keywords=["goodbye"],
        )
        assert rule.matches("hello there")
        assert not rule.matches("hello and goodbye")

    def test_template_for_persona_override(self):
        """template_for should return persona-specific override."""
        rule = DummyRule(
            name="test",
            response="default response",
            persona_overrides={"rhea": "rhea response", "default": "default response"},
            any_keywords=[],
            all_keywords=[],
            exclude_keywords=[],
        )
        assert rule.template_for("rhea") == "rhea response"
        assert rule.template_for("unknown") == "default response"


class TestDummyScriptLibrary:
    """Tests for the DummyScriptLibrary class."""

    def test_from_dict_creates_library(self):
        """from_dict should create a valid library from dictionary data."""
        library = DummyScriptLibrary.from_dict(DEFAULT_DATA)
        assert library.rules
        assert library.fallback is not None
        assert library.persona_openings

    def test_persona_opening_for_known_persona(self):
        """persona_opening_for should return persona-specific opening."""
        library = DummyScriptLibrary.from_dict(DEFAULT_DATA)
        opening = library.persona_opening_for("rhea")
        assert "Rhea" in opening

    def test_persona_opening_for_unknown_persona(self):
        """persona_opening_for should return default for unknown persona."""
        library = DummyScriptLibrary.from_dict(DEFAULT_DATA)
        opening = library.persona_opening_for("unknown_persona")
        assert "Alter/Ego" in opening

    def test_pick_rule_matches_grounding(self):
        """pick_rule should return grounding rule for anxiety keywords."""
        library = DummyScriptLibrary.from_dict(DEFAULT_DATA)
        rule = library.pick_rule("I'm feeling anxious today")
        assert rule.name == "grounding"

    def test_pick_rule_returns_fallback(self):
        """pick_rule should return fallback for unmatched prompts."""
        library = DummyScriptLibrary.from_dict(DEFAULT_DATA)
        rule = library.pick_rule("random text with no keywords")
        assert rule.name == "fallback"


class TestDummyLLM:
    """Tests for the DummyLLM class."""

    def test_init_creates_library(self):
        """DummyLLM should initialize with a script library."""
        dummy = DummyLLM()
        assert dummy.library is not None

    def test_generate_returns_string(self):
        """generate should return a non-empty string."""
        dummy = DummyLLM()
        result = dummy.generate("Hello, who are you?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_with_persona(self):
        """generate should use the specified persona."""
        dummy = DummyLLM()
        result = dummy.generate("Hello", persona="Rhea")
        assert isinstance(result, str)
        # The response should contain something related to Rhea or Alter/Ego
        assert len(result) > 0

    def test_generate_with_memory(self):
        """generate should incorporate memory into response."""
        dummy = DummyLLM()
        result = dummy.generate(
            "Hello",
            memory_used=["user: I'm feeling scattered"]
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_introduction(self):
        """generate should match introduction rule."""
        dummy = DummyLLM()
        result = dummy.generate("Who are you?")
        # Should return introduction response
        assert "mirror" in result.lower() or "alter" in result.lower() or "listen" in result.lower()

    def test_generate_grounding(self):
        """generate should match grounding rule for anxiety."""
        dummy = DummyLLM()
        result = dummy.generate("I feel overwhelmed and anxious")
        # Should return grounding response with grounding techniques
        assert len(result) > 0

    def test_generate_never_returns_empty(self):
        """generate should never return an empty string."""
        dummy = DummyLLM()
        # Test with various inputs
        for prompt in ["", "   ", "xyz123", "hello", "anxious"]:
            result = dummy.generate(prompt)
            assert result.strip(), f"Empty response for prompt: {repr(prompt)}"


class TestSummarizeMemory:
    """Tests for the _summarize_memory static method."""

    def test_empty_memory_returns_empty_dict(self):
        """Empty memory should return empty strings."""
        result = DummyLLM._summarize_memory([])
        assert result["summary"] == ""
        assert result["sentence"] == ""
        assert result["block"] == ""
        assert result["bullets"] == ""

    def test_memory_with_prefix(self):
        """Memory with prefix should strip the prefix."""
        result = DummyLLM._summarize_memory(["user: feeling happy"])
        assert result["summary"] == "feeling happy"

    def test_memory_without_prefix(self):
        """Memory without prefix should be used as-is."""
        result = DummyLLM._summarize_memory(["just some text"])
        assert result["summary"] == "just some text"

    def test_memory_sentence_format(self):
        """Memory sentence should be formatted correctly."""
        result = DummyLLM._summarize_memory(["user: test memory"])
        assert "holding our earlier note" in result["sentence"]
        assert "test memory" in result["sentence"]
