package types

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestWriteError(t *testing.T) {
	w := httptest.NewRecorder()
	status := http.StatusBadRequest
	code := "bad_request"
	message := "Invalid input"

	WriteError(w, status, code, message)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != status {
		t.Errorf("expected status %d, got %d", status, res.StatusCode)
	}

	contentType := res.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got %s", contentType)
	}

	var env Envelope
	if err := json.NewDecoder(res.Body).Decode(&env); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if env.Data != nil {
		t.Errorf("expected data to be nil, got %v", env.Data)
	}

	if env.Error == nil {
		t.Fatal("expected error to be not nil")
	}

	if env.Error.Code != code {
		t.Errorf("expected error code %s, got %s", code, env.Error.Code)
	}

	if env.Error.Message != message {
		t.Errorf("expected error message %s, got %s", message, env.Error.Message)
	}

	if env.Meta.Timestamp == "" {
		t.Error("expected meta timestamp to not be empty")
	} else {
		_, err := time.Parse(time.RFC3339, env.Meta.Timestamp)
		if err != nil {
			t.Errorf("expected valid RFC3339 timestamp, got %s", env.Meta.Timestamp)
		}
	}
}

func TestWriteJSON(t *testing.T) {
	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/test", nil)

	status := http.StatusOK
	data := map[string]string{"key": "value"}

	WriteJSON(w, req, status, data)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != status {
		t.Errorf("expected status %d, got %d", status, res.StatusCode)
	}

	contentType := res.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got %s", contentType)
	}

	var env Envelope
	if err := json.NewDecoder(res.Body).Decode(&env); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if env.Error != nil {
		t.Errorf("expected error to be nil, got %v", env.Error)
	}

	dataMap, ok := env.Data.(map[string]interface{})
	if !ok {
		t.Fatalf("expected data to be map[string]interface{}, got %T", env.Data)
	}
	if dataMap["key"] != "value" {
		t.Errorf("expected data key to be value, got %v", dataMap["key"])
	}

	if env.Meta.Timestamp == "" {
		t.Error("expected meta timestamp to not be empty")
	} else {
		_, err := time.Parse(time.RFC3339, env.Meta.Timestamp)
		if err != nil {
			t.Errorf("expected valid RFC3339 timestamp, got %s", env.Meta.Timestamp)
		}
	}
}
