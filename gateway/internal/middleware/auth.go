package middleware

import (
	"net/http"
	"os"
	"strings"

	"github.com/findociq/gateway/internal/types"
	"github.com/rs/zerolog/log"
)

// APIKeyAuth rejects requests that do not carry the correct bearer token.
// Exempt: GET /healthz (no auth needed for health checks).
func APIKeyAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/healthz" {
			next.ServeHTTP(w, r)
			return
		}

		apiKey := os.Getenv("API_KEY")
		if apiKey == "" {
			log.Warn().Msg("API_KEY not set — auth disabled")
			next.ServeHTTP(w, r)
			return
		}

		header := r.Header.Get("Authorization")
		token := strings.TrimPrefix(header, "Bearer ")
		if token == "" || token != apiKey {
			types.WriteError(w, http.StatusUnauthorized, "unauthorized", "missing or invalid API key")
			return
		}

		next.ServeHTTP(w, r)
	})
}
