package handler

import (
	"context"
	"net/http"
	"time"

	"github.com/findociq/gateway/internal/types"
	"github.com/jackc/pgx/v5/pgxpool"
)

// HealthCheck returns a handler that checks the database and downstream services.
func HealthCheck(pool *pgxpool.Pool, ingestionURL, ragURL, extractionURL string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		status := map[string]string{
			"status":     "ok",
			"db":         "down",
			"ingestion":  "down",
			"extraction": "down",
			"rag":        "down",
		}

		overallStatus := http.StatusOK

		// Check DB
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()
		if err := pool.Ping(ctx); err == nil {
			status["db"] = "up"
		} else {
			overallStatus = http.StatusServiceUnavailable
		}

		// Check Ingestion
		if checkServiceHealth(r.Context(), ingestionURL+"/healthz") {
			status["ingestion"] = "up"
		} else {
			overallStatus = http.StatusServiceUnavailable
		}

		// Check Extraction
		if checkServiceHealth(r.Context(), extractionURL+"/healthz") {
			status["extraction"] = "up"
		} else {
			overallStatus = http.StatusServiceUnavailable
		}

		// Check RAG
		if checkServiceHealth(r.Context(), ragURL+"/healthz") {
			status["rag"] = "up"
		} else {
			overallStatus = http.StatusServiceUnavailable
		}

		if overallStatus != http.StatusOK {
			status["status"] = "error"
		}

		types.WriteJSON(w, r, overallStatus, status)
	}
}

var healthClient = &http.Client{
	Timeout: 2 * time.Second,
}

func checkServiceHealth(ctx context.Context, url string) bool {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return false
	}
	resp, err := healthClient.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}
