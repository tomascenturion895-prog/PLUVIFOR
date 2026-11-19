// Command api arranca la API de PLUVIFOR en Go.
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/httpapi"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/proxy"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stderr, nil))
	cfg, err := config.FromEnv()
	if err != nil {
		logger.Error("configuración inválida", "error", err)
		os.Exit(1)
	}

	srv := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           httpapi.New(cfg, logger, httpapi.WithBackend(proxy.New(cfg.BackendURL, logger))),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      30 * time.Second,
		MaxHeaderBytes:    1 << 16,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		logger.Info("API en Go escuchando", "puerto", cfg.Port, "env", cfg.Env, "base", cfg.Database.Engine, "datos_en", cfg.BackendURL.Host)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("el servidor se detuvo", "error", err)
			stop()
		}
	}()

	<-ctx.Done()
	shutdown, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdown)
}
