package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog/log"
)

type DocumentResponse struct {
	ID             string          `json:"id"`
	Filename       string          `json:"filename"`
	Status         string          `json:"status"`
	DocumentType   string          `json:"document_type,omitempty"`
	PageCount      int             `json:"page_count,omitempty"`
	UploadedAt     time.Time       `json:"uploaded_at"`
	ExtractedData  json.RawMessage `json:"extracted_data,omitempty"`
}

func GetDocument(pool *pgxpool.Pool) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		if id == "" {
			http.Error(w, "missing document id", http.StatusBadRequest)
			return
		}

		ctx := context.Background()
		var resp DocumentResponse
		var docType *string
		var pageCount *int
		var extractedData []byte

		query := `
			SELECT
				d.id, d.filename, d.status, d.document_type, d.page_count, d.uploaded_at,
				e.extracted_data
			FROM documents d
			LEFT JOIN extractions e ON d.id = e.document_id
			WHERE d.id = $1
		`

		err := pool.QueryRow(ctx, query, id).Scan(
			&resp.ID, &resp.Filename, &resp.Status, &docType, &pageCount, &resp.UploadedAt, &extractedData,
		)
		if err != nil {
			log.Error().Err(err).Str("id", id).Msg("failed to query document")
			http.Error(w, "document not found", http.StatusNotFound)
			return
		}

		if docType != nil {
			resp.DocumentType = *docType
		}
		if pageCount != nil {
			resp.PageCount = *pageCount
		}
		if extractedData != nil {
			resp.ExtractedData = extractedData
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}
}
