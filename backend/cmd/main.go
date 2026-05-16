package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/the-onewho-knocks/finance-Simulation/backend/internal/cache"
	"github.com/the-onewho-knocks/finance-Simulation/backend/internal/config"
	handler "github.com/the-onewho-knocks/finance-Simulation/backend/internal/handlers"
	"github.com/the-onewho-knocks/finance-Simulation/backend/internal/repositories/pgx"
	"github.com/the-onewho-knocks/finance-Simulation/backend/internal/routes"
	"github.com/the-onewho-knocks/finance-Simulation/backend/internal/services"
	"github.com/the-onewho-knocks/finance-Simulation/backend/internal/stockapi"
)

func main() {

	cfg := config.LoadConfig()

	dbPool, err := pgxpool.New(context.Background(), cfg.DatabaseURL)
	if err != nil {
		log.Fatal("failed to connect to database:", err)
	}
	defer dbPool.Close()

	log.Println("connected to postgreSQL successfully")

	cache.InitializeRedis(cfg)

	stockCache := cache.NewStockCache()
	marketCache := cache.NewMarketCache(cache.RedisClient)
	heatmapCache := cache.NewHeatMapCache(cache.RedisClient)

	rapidApiClient := stockapi.NewRapidApiClient(
		cfg.RapidAPIKey,
		cfg.RapidAPIHost,
	)

	userRepo := pgx.NewUserRepository(dbPool)
	adminRepo := pgx.NewAdminRepository(dbPool)
	portfolioRepo := pgx.NewPortfolioRepository(dbPool)
	transactionRepo := pgx.NewTransactionRepository(dbPool)
	expenseRepo := pgx.NewExpenseRepository(dbPool)
	plannedExpenseRepo := pgx.NewPlannedExpenseRepository(dbPool)
	networthRepo := pgx.NewNetworthRepository(dbPool)

	userService := services.NewUserService(userRepo)
	adminService := services.NewAdminService(adminRepo)
	authService := services.NewAuthService(userService)

	expenseService := services.NewExpenseService(expenseRepo)
	plannedExpenseService := services.NewPlannedExpenseService(plannedExpenseRepo)

	portfolioService := services.NewPortfolioService(
		portfolioRepo,
		stockCache,
	)

	networthService := services.NewNetworthService(
		networthRepo,
		userRepo,
		portfolioService,
		expenseService,
	)

	transactionService := services.NewTransactionService(
		userRepo,
		portfolioRepo,
		transactionRepo,
		stockCache,
		networthService,
	)

	marketService := services.NewMarketService(
		cfg.RapidAPIKey,
		marketCache,
		stockCache,
	)

	heatmapService := services.NewHeatmapService(
		rapidApiClient,
		heatmapCache,
	)

	dashboardCache := cache.NewDashboardCache()

	dashboardService := services.NewDashboardService(
		networthService,
		portfolioService,
		expenseService,
		dashboardCache,
	)
	h := &routes.Handlers{
		Auth:           handler.NewAuthHandler(authService),
		User:           handler.NewUserHandler(userService),
		Admin:          handler.NewAdminHandler(adminService),
		Portfolio:      handler.NewPortfolioHandler(portfolioService),
		Transaction:    handler.NewTransactionHandler(transactionService),
		Expense:        handler.NewExpenseHandler(expenseService),
		PlannedExpense: handler.NewPlannedExpenseHandler(plannedExpenseService),
		Networth:       handler.NewNetworthHandler(networthService),
		Market:         handler.NewMarketHandler(marketService),
		Heatmap:        handler.NewHeatmapHandler(heatmapService),
		Dashboard:      handler.NewDashboardHandler(dashboardService),
	}

	r := chi.NewRouter()

	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Timeout(60 * time.Second))

	r.Get("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	r.Mount("/", routes.RegisterRoutes(h))

	srv := &http.Server{
		Addr:    ":" + cfg.AppPort,
		Handler: r,
	}

	go func() {
		log.Println("Server running on port", cfg.AppPort)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal(err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	srv.Shutdown(ctx)
}
