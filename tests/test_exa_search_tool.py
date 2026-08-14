import json
import os
import sys
from unittest.mock import MagicMock
sys.modules['swarms'] = MagicMock()
sys.modules['swarms.utils'] = MagicMock()
sys.modules['swarms.utils.any_to_str'] = MagicMock()

from unittest.mock import patch, MagicMock

import pytest

from autohedge.tools.exa_search_tool import exa_search

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"EXA_API_KEY": "test_key"}):
        yield

def test_exa_search_success(mock_env):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "title": "Test Title",
                "url": "https://example.com",
                "summary": "This is a summary."
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.post", return_value=mock_response) as mock_post:
        result_str = exa_search("test query")
        
        # Verify JSON serialization
        result_data = json.loads(result_str)
        assert "results" in result_data
        assert result_data["results"][0]["title"] == "Test Title"
        assert result_data["results"][0]["url"] == "https://example.com"
        assert result_data["results"][0]["summary"] == "This is a summary."

        # Verify payload sent to Exa
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["contents"]["text"] is False
        assert "summary" in payload["contents"]

def test_exa_search_error(mock_env):
    with patch("httpx.post", side_effect=Exception("API Error")):
        result_str = exa_search("test query")
        
        # Verify error handling
        result_data = json.loads(result_str)
        assert result_data["status"] == "error"
        assert result_data["provider"] == "exa"
        assert "API Error" in result_data["error"]

def test_exa_search_no_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="EXA_API_KEY environment variable is not set"):
            exa_search("test query")
