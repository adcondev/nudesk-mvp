import json
import pytest

# Conftest mocks external deps before this import
from services.extraction.app.main import _parse_claude_json

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
