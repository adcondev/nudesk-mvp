package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"

	"github.com/findociq/gateway/internal/handler"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})

	port := os.Getenv("GATEWAY_PORT")
	if port == "" {
		port = "8080"
	}

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://findociq:findociq@db:5432/findociq"
	}

	ingestionURL := os.Getenv("INGESTION_URL")
	if ingestionURL == "" {
		ingestionURL = "http://ingestion:8001"
	}
	parsedIngestionURL, err := url.Parse(ingestionURL)
	if err != nil {
		log.Fatal().Err(err).Msg("Invalid INGESTION_URL")
	}
	ingestionProxy := httputil.NewSingleHostReverseProxy(parsedIngestionURL)

	pool, err := pgxpool.New(context.Background(), dbURL)
	if err != nil {
		log.Fatal().Err(err).Msg("Unable to connect to database")
	}
	defer pool.Close()

	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/healthz", handler.HealthCheck)
	r.Get("/documents/{id}", handler.GetDocument(pool))
	r.Post("/ingest", func(w http.ResponseWriter, r *http.Request) {
		ingestionProxy.ServeHTTP(w, r)
	})

	log.Info().Msgf("Gateway starting on port %s", port)
	if err := http.ListenAndServe(fmt.Sprintf(":%s", port), r); err != nil {
		log.Fatal().Err(err).Msg("Failed to start server")
	}
}
