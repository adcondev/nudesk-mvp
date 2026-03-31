package handler

import (
	"net/http"

	"github.com/findociq/gateway/internal/types"
)

func HealthCheck(w http.ResponseWriter, r *http.Request) {
	types.WriteJSON(w, r, http.StatusOK, map[string]string{"status": "ok"})
}
