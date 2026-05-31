from datetime import datetime
from services.extraction.app.utils import _envelope

def test_envelope_defaults():
    """Test _envelope with default arguments."""
    result = _envelope()

    assert "data" in result
    assert result["data"] is None
    assert "error" in result
    assert result["error"] is None
    assert "meta" in result
    assert "request_id" in result["meta"]
    assert result["meta"]["request_id"] == ""
    assert "timestamp" in result["meta"]

    # Verify timestamp format and timezone
    dt = datetime.fromisoformat(result["meta"]["timestamp"])
    assert dt.tzinfo is not None

def test_envelope_with_data():
    """Test _envelope with only data argument provided."""
    test_data = {"key": "value", "number": 42}
    result = _envelope(data=test_data)

    assert result["data"] == test_data
    assert result["error"] is None

def test_envelope_with_error():
    """Test _envelope with only error argument provided."""
    test_error = "Something went wrong"
    result = _envelope(error=test_error)

    assert result["data"] is None
    assert result["error"] == test_error

def test_envelope_with_request_id():
    """Test _envelope with a specific request_id provided."""
    req_id = "req-12345"
    result = _envelope(request_id=req_id)

    assert result["meta"]["request_id"] == req_id

def test_envelope_with_all_args():
    """Test _envelope with all arguments provided."""
    test_data = {"status": "ok"}
    test_error = "Minor warning"
    req_id = "req-999"

    result = _envelope(data=test_data, error=test_error, request_id=req_id)

    assert result["data"] == test_data
    assert result["error"] == test_error
    assert result["meta"]["request_id"] == req_id
