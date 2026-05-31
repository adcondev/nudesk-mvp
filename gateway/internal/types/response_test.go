package types

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestWriteError(t *testing.T) {
	tests := []struct {
		name    string
		status  int
		code    string
		message string
	}{
		{
			name:    "bad_request",
			status:  http.StatusBadRequest,
			code:    "bad_request",
			message: "Invalid input",
		},
		{
			name:    "internal_server_error",
			status:  http.StatusInternalServerError,
			code:    "internal_error",
			message: "Something went wrong",
		},
		{
			name:    "not_found",
			status:  http.StatusNotFound,
			code:    "not_found",
			message: "Resource not found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			w := httptest.NewRecorder()
			WriteError(w, tt.status, tt.code, tt.message)

			res := w.Result()
			defer res.Body.Close()

			if res.StatusCode != tt.status {
				t.Errorf("expected status %d, got %d", tt.status, res.StatusCode)
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

			if env.Error.Code != tt.code {
				t.Errorf("expected error code %s, got %s", tt.code, env.Error.Code)
			}

			if env.Error.Message != tt.message {
				t.Errorf("expected error message %s, got %s", tt.message, env.Error.Message)
			}

			if env.Meta.Timestamp == "" {
				t.Error("expected meta timestamp to not be empty")
			} else {
				_, err := time.Parse(time.RFC3339, env.Meta.Timestamp)
				if err != nil {
					t.Errorf("expected valid RFC3339 timestamp, got %s", env.Meta.Timestamp)
				}
			}
		})
	}
}

func TestWriteJSON(t *testing.T) {
	tests := []struct {
		name   string
		status int
		data   any
	}{
		{
			name:   "ok_with_map",
			status: http.StatusOK,
			data:   map[string]string{"key": "value"},
		},
		{
			name:   "created_with_struct",
			status: http.StatusCreated,
			data: struct {
				ID string `json:"id"`
			}{ID: "123"},
		},
		{
			name:   "no_content_nil_data",
			status: http.StatusNoContent,
			data:   nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			w := httptest.NewRecorder()
			req := httptest.NewRequest("GET", "/test", nil)

			WriteJSON(w, req, tt.status, tt.data)

			res := w.Result()
			defer res.Body.Close()

			if res.StatusCode != tt.status {
				t.Errorf("expected status %d, got %d", tt.status, res.StatusCode)
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

			if env.Meta.Timestamp == "" {
				t.Error("expected meta timestamp to not be empty")
			} else {
				_, err := time.Parse(time.RFC3339, env.Meta.Timestamp)
				if err != nil {
					t.Errorf("expected valid RFC3339 timestamp, got %s", env.Meta.Timestamp)
				}
			}
		})
	}
}
