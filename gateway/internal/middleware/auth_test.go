package middleware

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/findociq/gateway/internal/types"
)

func TestAPIKeyAuth(t *testing.T) {
	// Create a dummy handler to act as the "next" handler in the chain.
	dummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// Wrap it with our middleware.
	handler := APIKeyAuth(dummyHandler)

	tests := []struct {
		name           string
		path           string
		apiKeyEnv      string
		authHeader     string
		expectedStatus int
		expectedBody   string // or expected substring
	}{
		{
			name:           "Healthz endpoint is exempt",
			path:           "/healthz",
			apiKeyEnv:      "secret123",
			authHeader:     "", // no header
			expectedStatus: http.StatusOK,
			expectedBody:   "OK",
		},
		{
			name:           "Empty API_KEY env var denies request with internal error",
			path:           "/some/path",
			apiKeyEnv:      "",
			authHeader:     "Bearer whatever",
			expectedStatus: http.StatusInternalServerError,
		},
		{
			name:           "Missing Authorization header returns 401",
			path:           "/some/path",
			apiKeyEnv:      "secret123",
			authHeader:     "",
			expectedStatus: http.StatusUnauthorized,
		},
		{
			name:           "Invalid Authorization header format returns 401",
			path:           "/some/path",
			apiKeyEnv:      "secret123",
			authHeader:     "Basic whatever",
			expectedStatus: http.StatusUnauthorized,
		},
		{
			name:           "Incorrect API key returns 401",
			path:           "/some/path",
			apiKeyEnv:      "secret123",
			authHeader:     "Bearer wrongsecret",
			expectedStatus: http.StatusUnauthorized,
		},
		{
			name:           "Correct API key allows request",
			path:           "/some/path",
			apiKeyEnv:      "secret123",
			authHeader:     "Bearer secret123",
			expectedStatus: http.StatusOK,
			expectedBody:   "OK",
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			// Save the original API_KEY so we can restore it.
			origAPIKey := os.Getenv("API_KEY")
			defer os.Setenv("API_KEY", origAPIKey)

			// Set the API_KEY environment variable.
			if tc.apiKeyEnv != "" {
				os.Setenv("API_KEY", tc.apiKeyEnv)
			} else {
				os.Unsetenv("API_KEY")
			}

			// Create a request.
			req := httptest.NewRequest(http.MethodGet, tc.path, nil)
			if tc.authHeader != "" {
				req.Header.Set("Authorization", tc.authHeader)
			}

			// Record the response.
			rr := httptest.NewRecorder()
			handler.ServeHTTP(rr, req)

			// Check the status code.
			if rr.Code != tc.expectedStatus {
				t.Errorf("expected status %d, got %d", tc.expectedStatus, rr.Code)
			}

			// For OK responses, check that the dummy handler was called.
			if tc.expectedStatus == http.StatusOK {
				if rr.Body.String() != tc.expectedBody {
					t.Errorf("expected body %q, got %q", tc.expectedBody, rr.Body.String())
				}
			} else {
				// For unauthorized responses, verify it's the expected JSON format.
				var env types.Envelope
				if err := json.Unmarshal(rr.Body.Bytes(), &env); err != nil {
					t.Fatalf("failed to unmarshal response body: %v", err)
				}
				if env.Error == nil {
					t.Error("expected error object in response envelope, got nil")
				} else {
					if tc.expectedStatus == http.StatusUnauthorized {
						if env.Error.Code != "unauthorized" {
							t.Errorf("expected error code 'unauthorized', got %q", env.Error.Code)
						}
						if env.Error.Message != "missing or invalid API key" {
							t.Errorf("expected error message 'missing or invalid API key', got %q", env.Error.Message)
						}
					} else if tc.expectedStatus == http.StatusInternalServerError {
						if env.Error.Code != "internal_error" {
							t.Errorf("expected error code 'internal_error', got %q", env.Error.Code)
						}
						if env.Error.Message != "server misconfiguration: API_KEY not set" {
							t.Errorf("expected error message 'server misconfiguration: API_KEY not set', got %q", env.Error.Message)
						}
					}
				}
			}
		})
	}
}
