package handler

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestCheckServiceHealth(t *testing.T) {
	tests := []struct {
		name       string
		serverResp int
		delay      time.Duration
		badURL     bool
		want       bool
	}{
		{
			name:       "Healthy Service (200 OK)",
			serverResp: http.StatusOK,
			want:       true,
		},
		{
			name:       "Unhealthy Service (500 Internal Server Error)",
			serverResp: http.StatusInternalServerError,
			want:       false,
		},
		{
			name:       "Unhealthy Service (404 Not Found)",
			serverResp: http.StatusNotFound,
			want:       false,
		},
		{
			name:       "Timeout",
			serverResp: http.StatusOK,
			delay:      100 * time.Millisecond,
			want:       false,
		},
		{
			name:   "Invalid URL",
			badURL: true,
			want:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if tt.delay > 0 {
					time.Sleep(tt.delay)
				}
				w.WriteHeader(tt.serverResp)
			}))
			defer server.Close()

			url := server.URL
			if tt.badURL {
				url = "http://not-a-real-url-that-will-fail-dns.local"
			}

			// For the timeout test, we override the healthClient timeout or use a tight context.
			// The original healthClient has a 2 second timeout.
			// Let's use a context with a shorter timeout for the timeout test case.
			ctx := context.Background()
			var cancel context.CancelFunc
			if tt.delay > 0 {
				ctx, cancel = context.WithTimeout(context.Background(), 50*time.Millisecond)
				defer cancel()
			}

			got := checkServiceHealth(ctx, url)
			if got != tt.want {
				t.Errorf("checkServiceHealth() = %v, want %v", got, tt.want)
			}
		})
	}
}
