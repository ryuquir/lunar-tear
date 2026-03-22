package main

import (
	"fmt"
	"log"
	"net/http"

	"lunar-tear/server/internal/service"

	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"
)

func startHTTP(port int, resourcesBaseURL string) {
	octoServer := service.NewOctoHTTPServer(resourcesBaseURL)
	h2s := &http2.Server{}
	octoHandler := h2c.NewHandler(octoServer.Handler(), h2s)
	log.Printf("Octo HTTP server listening on :%d (HTTP/1.1 + h2c)", port)
	srv := &http.Server{Addr: fmt.Sprintf(":%d", port), Handler: octoHandler}
	http2.ConfigureServer(srv, h2s)
	if err := srv.ListenAndServe(); err != nil {
		log.Fatalf("HTTP server on %d failed: %v", port, err)
	}
}
