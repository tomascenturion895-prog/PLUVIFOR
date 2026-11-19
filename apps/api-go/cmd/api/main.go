// Command api arranca la API de PLUVIFOR en Go.
package main

import (
	"context"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/civil"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/config"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/httpapi"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/proxy"
	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/sqlstore"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stderr, nil))
	cfg, err := config.FromEnv()
	if err != nil {
		logger.Error("configuración inválida", "error", err)
		os.Exit(1)
	}

	opts := []httpapi.Option{httpapi.WithBackend(proxy.New(cfg.BackendURL, logger))}
	if store := openStore(cfg, logger); store != nil {
		defer store.Close()
		cutoff, _ := civil.Parse(cfg.CutoffDate) // ya validada por config
		opts = append(opts, httpapi.WithStations(store, logger), httpapi.WithRainfall(store, cutoff, logger))
	}

	srv := &http.Server{
		Addr:              net.JoinHostPort(cfg.Host, cfg.Port),
		Handler:           httpapi.New(cfg, logger, opts...),
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      30 * time.Second,
		MaxHeaderBytes:    1 << 16,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		logger.Info("API en Go escuchando", "direccion", net.JoinHostPort(cfg.Host, cfg.Port), "env", cfg.Env, "base", cfg.Database.Engine, "datos_en", cfg.BackendURL.Host)
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

// openStore abre la base para que Go responda estaciones y lluvia. Si no se puede (sin driver, motor
// no soportado o base inaccesible), devuelve nil y esas rutas siguen yendo a Python por el reenvío:
// la API arranca igual, con el mismo contrato.
func openStore(cfg config.Config, logger *slog.Logger) *sqlstore.Store {
	if cfg.Database.Engine != "sqlite" {
		logger.Warn("Go todavía lee solo SQLite: estaciones y lluvia se reenvían a Python", "base", cfg.Database.Engine)
		return nil
	}
	store, err := sqlstore.OpenSQLite(cfg.Database.SQLitePath)
	if err != nil {
		logger.Warn("estaciones y lluvia se reenvían a Python", "motivo", err.Error())
		return nil
	}
	logger.Info("Go responde estaciones y lluvia desde la base (solo lectura)")
	return store
}
