// Package main demonstrates a simple HTTP server with middleware
// Shows Go structs, interfaces, methods, and concurrency patterns
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

// Config holds server configuration
type Config struct {
	Port         int           `json:"port"`
	ReadTimeout  time.Duration `json:"read_timeout"`
	WriteTimeout time.Duration `json:"write_timeout"`
	MaxConns     int           `json:"max_connections"`
}

// DefaultConfig returns default server configuration
func DefaultConfig() *Config {
	return &Config{
		Port:         8080,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		MaxConns:     100,
	}
}

// Handler defines the interface for HTTP handlers
type Handler interface {
	ServeHTTP(w http.ResponseWriter, r *http.Request)
	Name() string
}

// Server represents the HTTP server
type Server struct {
	config   *Config
	router   *Router
	mu       sync.RWMutex
	handlers map[string]Handler
	running  bool
}

// NewServer creates a new server instance
func NewServer(config *Config) *Server {
	if config == nil {
		config = DefaultConfig()
	}

	return &Server{
		config:   config,
		router:   NewRouter(),
		handlers: make(map[string]Handler),
		running:  false,
	}
}

// Start starts the HTTP server
func (s *Server) Start(ctx context.Context) error {
	s.mu.Lock()
	if s.running {
		s.mu.Unlock()
		return fmt.Errorf("server already running")
	}
	s.running = true
	s.mu.Unlock()

	addr := fmt.Sprintf(":%d", s.config.Port)
	server := &http.Server{
		Addr:         addr,
		Handler:      s.router,
		ReadTimeout:  s.config.ReadTimeout,
		WriteTimeout: s.config.WriteTimeout,
	}

	log.Printf("Starting server on %s", addr)

	// Start server in goroutine
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("Server error: %v", err)
		}
	}()

	// Wait for context cancellation
	<-ctx.Done()
	log.Println("Shutting down server...")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	return server.Shutdown(shutdownCtx)
}

// RegisterHandler registers a named handler
func (s *Server) RegisterHandler(path string, handler Handler) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.handlers[path] = handler
	s.router.Handle(path, handler)
	log.Printf("Registered handler '%s' at path: %s", handler.Name(), path)
}

// IsRunning returns whether the server is running
func (s *Server) IsRunning() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.running
}

// Router handles HTTP routing
type Router struct {
	routes map[string]Handler
	mu     sync.RWMutex
}

// NewRouter creates a new router
func NewRouter() *Router {
	return &Router{
		routes: make(map[string]Handler),
	}
}

// Handle registers a handler for a path
func (r *Router) Handle(path string, handler Handler) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.routes[path] = handler
}

// ServeHTTP implements http.Handler interface
func (r *Router) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	r.mu.RLock()
	handler, exists := r.routes[req.URL.Path]
	r.mu.RUnlock()

	if !exists {
		http.NotFound(w, req)
		return
	}

	// Apply middleware
	LoggingMiddleware(handler).ServeHTTP(w, req)
}

// APIHandler handles API requests
type APIHandler struct {
	name string
	data interface{}
}

// NewAPIHandler creates a new API handler
func NewAPIHandler(name string, data interface{}) *APIHandler {
	return &APIHandler{
		name: name,
		data: data,
	}
}

// ServeHTTP implements Handler interface
func (h *APIHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	response := map[string]interface{}{
		"handler": h.name,
		"path":    r.URL.Path,
		"method":  r.Method,
		"data":    h.data,
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

// Name returns the handler name
func (h *APIHandler) Name() string {
	return h.name
}

// LoggingMiddleware wraps a handler with logging
func LoggingMiddleware(next Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		log.Printf("Started %s %s", r.Method, r.URL.Path)

		next.ServeHTTP(w, r)

		duration := time.Since(start)
		log.Printf("Completed %s %s in %v", r.Method, r.URL.Path, duration)
	})
}

// HealthChecker provides health check functionality
type HealthChecker struct {
	checks map[string]func() error
	mu     sync.RWMutex
}

// NewHealthChecker creates a new health checker
func NewHealthChecker() *HealthChecker {
	return &HealthChecker{
		checks: make(map[string]func() error),
	}
}

// AddCheck adds a health check
func (hc *HealthChecker) AddCheck(name string, check func() error) {
	hc.mu.Lock()
	defer hc.mu.Unlock()
	hc.checks[name] = check
}

// RunChecks runs all health checks
func (hc *HealthChecker) RunChecks() map[string]error {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	results := make(map[string]error)
	var wg sync.WaitGroup

	for name, check := range hc.checks {
		wg.Add(1)
		go func(n string, c func() error) {
			defer wg.Done()
			results[n] = c()
		}(name, check)
	}

	wg.Wait()
	return results
}

func main() {
	config := DefaultConfig()
	server := NewServer(config)

	// Register handlers
	server.RegisterHandler("/api/status", NewAPIHandler("status", map[string]string{
		"status": "ok",
		"version": "1.0.0",
	}))

	server.RegisterHandler("/api/health", NewAPIHandler("health", map[string]bool{
		"healthy": true,
	}))

	// Start server
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := server.Start(ctx); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
