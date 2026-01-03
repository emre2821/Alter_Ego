"""Unit tests for configuration module."""

import os
from pathlib import Path
from unittest.mock import patch


import configuration


class TestConfiguration:
    """Tests for the configuration module."""

    def test_load_configuration_returns_dict(self):
        """load_configuration should return a dictionary."""
        result = configuration.load_configuration()
        assert isinstance(result, dict)

    def test_get_persona_root_returns_path(self):
        """get_persona_root should return a Path object."""
        result = configuration.get_persona_root(create=False)
        assert isinstance(result, Path)

    def test_get_models_dir_returns_path(self):
        """get_models_dir should return a Path object."""
        result = configuration.get_models_dir(create=False)
        assert isinstance(result, Path)

    def test_get_memory_db_path_returns_path(self):
        """get_memory_db_path should return a Path object."""
        result = configuration.get_memory_db_path()
        assert isinstance(result, Path)

    def test_get_log_path_returns_path(self):
        """get_log_path should return a Path object."""
        result = configuration.get_log_path()
        assert isinstance(result, Path)

    def test_get_default_log_path_returns_path(self):
        """get_default_log_path should return a Path object."""
        result = configuration.get_default_log_path()
        assert isinstance(result, Path)

    def test_get_switch_log_path_returns_path(self):
        """get_switch_log_path should return a Path object."""
        result = configuration.get_switch_log_path(create=False)
        assert isinstance(result, Path)

    def test_describe_data_locations_returns_dict(self):
        """describe_data_locations should return a dictionary of paths."""
        result = configuration.describe_data_locations()
        assert isinstance(result, dict)
        assert "personas" in result
        assert "models" in result
        assert "memory_db" in result
        assert "autosave_log" in result

    @patch.dict(os.environ, {"PERSONA_ROOT": "/custom/personas"}, clear=False)
    def test_get_persona_root_uses_env_override(self):
        """get_persona_root should use PERSONA_ROOT environment variable."""
        # Clear the cache to force re-evaluation
        configuration.load_configuration.cache_clear()
        result = configuration.get_persona_root(create=False)
        assert str(result) == "/custom/personas"

    @patch.dict(os.environ, {"ALTER_EGO_LOG_PATH": "/custom/logs/echo.chaos"}, clear=False)
    def test_get_log_path_uses_env_override(self):
        """get_log_path should use ALTER_EGO_LOG_PATH environment variable."""
        configuration.load_configuration.cache_clear()
        result = configuration.get_log_path()
        assert str(result) == "/custom/logs/echo.chaos"


class TestExpand:
    """Tests for the _expand helper function."""

    def test_expand_absolute_path(self):
        """_expand should return absolute paths unchanged."""
        result = configuration._expand("/absolute/path")
        assert result == Path("/absolute/path")

    def test_expand_relative_path(self):
        """_expand should resolve relative paths against APP_ROOT."""
        result = configuration._expand("relative/path")
        expected = (configuration.APP_ROOT / "relative/path").resolve()
        assert result == expected

    def test_expand_home_tilde(self):
        """_expand should expand ~ to home directory."""
        result = configuration._expand("~/some/path")
        assert str(result).startswith(str(Path.home()))
