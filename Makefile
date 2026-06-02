# Ops front-door for the practice-theory long-lived services.
# Cognabot-style: make is the interface, pm2 is the supervisor (auto-restart on
# crash; `pm2 save` + the existing pm2 boot agent resurrect on reboot).
# Process definitions live in ecosystem.config.js; env wiring lives in scripts/.

.PHONY: help up down status logs save \
	keeper-up keeper-down keeper-logs \
	somatic-http-up somatic-http-down \
	autonomic-http-up autonomic-http-down

help:  ## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── RemSleep keeper (Memory Recall + Consolidation; applies for real) ──
keeper-up:  ## Start the RemSleep keeper under pm2
	@pm2 start ecosystem.config.js --only remsleep-keeper
	@pm2 save

keeper-down:  ## Stop + remove the RemSleep keeper
	@pm2 stop remsleep-keeper 2>/dev/null || true
	@pm2 delete remsleep-keeper 2>/dev/null || true
	@pm2 save

keeper-logs:  ## Follow the keeper log
	@pm2 logs remsleep-keeper

# ── HTTP MCP servers (Phase 2b; per-session state makes them concurrent-safe) ──
somatic-http-up:  ## Start the somatic HTTP MCP server (:7180)
	@pm2 start ecosystem.config.js --only practice-somatic-http
	@pm2 save

somatic-http-down:  ## Stop the somatic HTTP MCP server
	@pm2 stop practice-somatic-http 2>/dev/null || true
	@pm2 delete practice-somatic-http 2>/dev/null || true
	@pm2 save

autonomic-http-up:  ## Start the autonomic HTTP MCP server (:7181)
	@pm2 start ecosystem.config.js --only practice-autonomic-http
	@pm2 save

autonomic-http-down:  ## Stop the autonomic HTTP MCP server
	@pm2 stop practice-autonomic-http 2>/dev/null || true
	@pm2 delete practice-autonomic-http 2>/dev/null || true
	@pm2 save

# ── Aggregate ──
up:  ## Start all services under pm2 (keeper + both HTTP servers)
	@pm2 start ecosystem.config.js
	@pm2 save

down:  ## Stop + remove all services
	@pm2 delete ecosystem.config.js 2>/dev/null || true
	@pm2 save

status:  ## Show pm2 status + HTTP port health
	@pm2 status
	@printf "  somatic   :7180  "; lsof -iTCP:7180 -sTCP:LISTEN >/dev/null 2>&1 && echo "listening" || echo "down"
	@printf "  autonomic :7181  "; lsof -iTCP:7181 -sTCP:LISTEN >/dev/null 2>&1 && echo "listening" || echo "down"

logs:  ## Follow all service logs
	@pm2 logs

save:  ## Persist the pm2 process list (boot resurrection)
	@pm2 save
