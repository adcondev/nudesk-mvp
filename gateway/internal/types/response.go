package types

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
)

// Envelope is the standard API response shape for all endpoints.
type Envelope struct {
	Data  any        `json:"data"`
	Error *APIError  `json:"error"`
	Meta  Meta       `json:"meta"`
}

type APIError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

type Meta struct {
	RequestID string `json:"request_id"`
	Timestamp string `json:"timestamp"`
}

// WriteJSON writes a successful envelope response.
func WriteJSON(w http.ResponseWriter, r *http.Request, status int, data any) {
	env := Envelope{
		Data:  data,
		Error: nil,
		Meta: Meta{
			RequestID: middleware.GetReqID(r.Context()),
			Timestamp: time.Now().UTC().Format(time.RFC3339),
		},
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(env)
}

// WriteError writes an error envelope response.
func WriteError(w http.ResponseWriter, status int, code, message string) {
	env := Envelope{
		Data: nil,
		Error: &APIError{Code: code, Message: message},
		Meta: Meta{
			Timestamp: time.Now().UTC().Format(time.RFC3339),
		},
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(env)
}
