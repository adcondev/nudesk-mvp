package handler

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestCheckServiceHealth(t *testing.T) {
	// Save the original timeout and restore it after tests
	originalTimeout := healthClient.Timeout
	healthClient.Timeout = 50 * time.Millisecond
	defer func() {
		healthClient.Timeout = originalTimeout
	}()

	tests := []struct {
		name           string
		handler        http.HandlerFunc
		url            string
		expectedResult bool
	}{
		{
			name: "Status OK returns true",
			handler: func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusOK)
			},
			expectedResult: true,
		},
		{
			name: "Internal Server Error returns false",
			handler: func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(http.StatusInternalServerError)
			},
			expectedResult: false,
		},
		{
			name: "Timeout returns false",
			handler: func(w http.ResponseWriter, r *http.Request) {
				time.Sleep(100 * time.Millisecond) // longer than the 50ms client timeout
				w.WriteHeader(http.StatusOK)
			},
			expectedResult: false,
		},
		{
			name: "Unreachable URL returns false",
			url:  "http://127.0.0.1:0", // Invalid/unreachable port
			expectedResult: false,
		},
		{
			name: "Invalid URL format returns false",
			url:  "http://[::1]:namedport", // Bad URL
			expectedResult: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			var testURL string
			if tc.url != "" {
				testURL = tc.url
			} else {
				server := httptest.NewServer(tc.handler)
				defer server.Close()
				testURL = server.URL
			}

			result := checkServiceHealth(context.Background(), testURL)
			if result != tc.expectedResult {
				t.Errorf("expected %v, got %v", tc.expectedResult, result)
			}
		})
	}

	t.Run("Context Cancelled returns false", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		ctx, cancel := context.WithCancel(context.Background())
		cancel() // Cancel context immediately

		result := checkServiceHealth(ctx, server.URL)
		if result != false {
			t.Errorf("expected false, got %v", result)
		}
	})

	t.Run("Request Creation Failure", func(t *testing.T) {
		// A control character in the URL causes NewRequestWithContext to fail
		result := checkServiceHealth(context.Background(), "http://127.0.0.1/\x7f")
		if result != false {
			t.Errorf("expected false, got %v", result)
		}
	})
}
