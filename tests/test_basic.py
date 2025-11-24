"""
Basic Unit Tests
"""
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def test_imports():
    from src.utils import config
    from src.tools import web_search_tool
    from src.memory import memory_system
    assert True

def test_config_loading():
    from src.utils.config import settings
    assert settings is not None
    assert settings.openai is not None

def test_custom_exceptions():
    from src.utils.exceptions import ResearchAssistantError, CrewError
    error = ResearchAssistantError("test", "TEST")
    assert "TEST" in str(error)
    assert issubclass(CrewError, ResearchAssistantError)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
