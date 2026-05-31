import json
import pytest
from datetime import datetime

# Conftest mocks external deps before this import
from services.extraction.app.main import _parse_claude_json, _envelope


def test_parse_claude_json_plain():
    input_text = '{"name": "John Doe", "age": 30}'
    result = _parse_claude_json(input_text)
    assert result == {"name": "John Doe", "age": 30}


def test_parse_claude_json_with_fences():
    input_text = """```
{"name": "John Doe", "age": 30}
```"""
    result = _parse_claude_json(input_text)
    assert result == {"name": "John Doe", "age": 30}


def test_parse_claude_json_with_json_fences():
    input_text = """```json
{"name": "John Doe", "age": 30}
```"""
    result = _parse_claude_json(input_text)
    assert result == {"name": "John Doe", "age": 30}


def test_parse_claude_json_with_whitespace():
    input_text = """

```json
  {"name": "John Doe", "age": 30}
```

    """
    result = _parse_claude_json(input_text)
    assert result == {"name": "John Doe", "age": 30}


def test_parse_claude_json_invalid():
    input_text = '{"name": "John Doe", "age": 30'  # Missing closing brace
    with pytest.raises(json.JSONDecodeError):
        _parse_claude_json(input_text)


def test_parse_claude_json_empty_string():
    with pytest.raises(json.JSONDecodeError):
        _parse_claude_json("")


def test_parse_claude_json_multiline_fences():
    input_text = """```json
{
    "name": "John Doe",
    "age": 30
}
```"""
    result = _parse_claude_json(input_text)
    assert result == {"name": "John Doe", "age": 30}


def test_envelope_default():
    result = _envelope()
    assert result["data"] is None
    assert result["error"] is None
    assert result["meta"]["request_id"] == ""
    assert "timestamp" in result["meta"]
    # Check timestamp is ISO format
    datetime.fromisoformat(result["meta"]["timestamp"])


def test_envelope_with_data():
    result = _envelope(data={"key": "value"})
    assert result["data"] == {"key": "value"}
    assert result["error"] is None


def test_envelope_with_error():
    result = _envelope(error="something went wrong")
    assert result["data"] is None
    assert result["error"] == "something went wrong"


def test_envelope_with_request_id():
    result = _envelope(request_id="req-123")
    assert result["meta"]["request_id"] == "req-123"


def test_envelope_with_all():
    result = _envelope(data={"status": "ok"}, error="none", request_id="req-456")
    assert result["data"] == {"status": "ok"}
    assert result["error"] == "none"
    assert result["meta"]["request_id"] == "req-456"
