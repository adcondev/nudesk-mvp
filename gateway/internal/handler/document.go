package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/findociq/gateway/internal/types"
	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog/log"
)

type DocumentResponse struct {
	ID            string          `json:"id"`
	Filename      string          `json:"filename"`
	Status        string          `json:"status"`
	DocumentType  string          `json:"document_type,omitempty"`
	PageCount     int             `json:"page_count,omitempty"`
	UploadedAt    time.Time       `json:"uploaded_at"`
	ExtractedData json.RawMessage `json:"extracted_data,omitempty"`
}

func GetDocument(pool *pgxpool.Pool) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		if id == "" {
			types.WriteError(w, http.StatusBadRequest, "bad_request", "missing document id")
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
			types.WriteError(w, http.StatusNotFound, "not_found", "document not found")
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

		types.WriteJSON(w, r, http.StatusOK, resp)
	}
}

func ListDocuments(pool *pgxpool.Pool) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()

		query := `
			SELECT
				d.id, d.filename, d.status, d.document_type, d.page_count, d.uploaded_at
			FROM documents d
			ORDER BY d.uploaded_at DESC
			LIMIT 50
		`

		rows, err := pool.Query(ctx, query)
		if err != nil {
			log.Error().Err(err).Msg("failed to query documents")
			types.WriteError(w, http.StatusInternalServerError, "internal_error", "failed to list documents")
			return
		}
		defer rows.Close()

		var documents []DocumentResponse
		for rows.Next() {
			var resp DocumentResponse
			var docType *string
			var pageCount *int

			err := rows.Scan(
				&resp.ID, &resp.Filename, &resp.Status, &docType, &pageCount, &resp.UploadedAt,
			)
			if err != nil {
				log.Error().Err(err).Msg("failed to scan document row")
				continue
			}

			if docType != nil {
				resp.DocumentType = *docType
			}
			if pageCount != nil {
				resp.PageCount = *pageCount
			}
			documents = append(documents, resp)
		}

		if err := rows.Err(); err != nil {
			log.Error().Err(err).Msg("rows error when listing documents")
			types.WriteError(w, http.StatusInternalServerError, "internal_error", "failed to list documents")
			return
		}

		if documents == nil {
			documents = []DocumentResponse{}
		}

		types.WriteJSON(w, r, http.StatusOK, documents)
	}
}
