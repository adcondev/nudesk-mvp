package middleware_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/findociq/gateway/internal/middleware"
	"github.com/findociq/gateway/internal/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestAPIKeyAuth(t *testing.T) {
	// Setup a dummy handler
	dummyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("success"))
	})

	// Setup middleware
	handler := middleware.APIKeyAuth(dummyHandler)

	tests := []struct {
		name           string
		path           string
		apiKeyEnv      string
		authHeader     string
		expectedStatus int
		expectedBody   string
		validateErr    bool
	}{
		{
			name:           "healthz endpoint is exempt",
			path:           "/healthz",
			apiKeyEnv:      "secret123",
			authHeader:     "", // No header provided
			expectedStatus: http.StatusOK,
			expectedBody:   "success",
			validateErr:    false,
		},
		{
			name:           "empty API_KEY environment variable allows request",
			path:           "/api/v1/test",
			apiKeyEnv:      "",
			authHeader:     "Bearer whatever",
			expectedStatus: http.StatusOK,
			expectedBody:   "success",
			validateErr:    false,
		},
		{
			name:           "missing Authorization header",
			path:           "/api/v1/test",
			apiKeyEnv:      "secret123",
			authHeader:     "",
			expectedStatus: http.StatusUnauthorized,
			validateErr:    true,
		},
		{
			name:           "invalid Authorization header format (not Bearer)",
			path:           "/api/v1/test",
			apiKeyEnv:      "secret123",
			authHeader:     "Basic dXNlcjpwYXNz",
			expectedStatus: http.StatusUnauthorized,
			validateErr:    true,
		},
		{
			name:           "incorrect API key",
			path:           "/api/v1/test",
			apiKeyEnv:      "secret123",
			authHeader:     "Bearer wrong_secret",
			expectedStatus: http.StatusUnauthorized,
			validateErr:    true,
		},
		{
			name:           "correct API key",
			path:           "/api/v1/test",
			apiKeyEnv:      "secret123",
			authHeader:     "Bearer secret123",
			expectedStatus: http.StatusOK,
			expectedBody:   "success",
			validateErr:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Manage environment variable
			originalKey := os.Getenv("API_KEY")
			defer os.Setenv("API_KEY", originalKey)

			if tt.apiKeyEnv != "" {
				os.Setenv("API_KEY", tt.apiKeyEnv)
			} else {
				os.Unsetenv("API_KEY")
			}

			// Prepare request
			req := httptest.NewRequest(http.MethodGet, tt.path, nil)
			if tt.authHeader != "" {
				req.Header.Set("Authorization", tt.authHeader)
			}

			// Record response
			rr := httptest.NewRecorder()
			handler.ServeHTTP(rr, req)

			// Assertions
			assert.Equal(t, tt.expectedStatus, rr.Code)

			if tt.expectedStatus == http.StatusOK {
				assert.Equal(t, tt.expectedBody, rr.Body.String())
			}

			if tt.validateErr {
				var env types.Envelope
				err := json.Unmarshal(rr.Body.Bytes(), &env)
				require.NoError(t, err, "Response should be a valid JSON envelope")
				require.NotNil(t, env.Error, "Error should not be nil in the envelope")
				assert.Equal(t, "unauthorized", env.Error.Code)
				assert.Equal(t, "missing or invalid API key", env.Error.Message)
			}
		})
	}
}
