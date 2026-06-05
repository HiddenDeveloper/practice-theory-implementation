# Ops front-door for the practice-theory long-lived services.
# Cognabot-style: make is the interface, pm2 is the supervisor (auto-restart on
# crash; `pm2 save` + the existing pm2 boot agent resurrect on reboot).
# Process definitions live in ecosystem.config.js; env wiring lives in scripts/.
#
# Every service has: up / down / restart / logs / status.
# Across all services: all-up / all-down / all-restart / all-status / all-logs.
# `restart` starts the service if it is not running, so you never have to know
# whether it is up first.

.PHONY: help save \
	keeper-up keeper-down keeper-restart keeper-logs keeper-status \
	somatic-http-up somatic-http-down somatic-http-restart somatic-http-logs somatic-http-status \
	autonomic-http-up autonomic-http-down autonomic-http-restart autonomic-http-logs autonomic-http-status \
	autonomic-stop \
	janitor-up janitor-down janitor-restart janitor-logs janitor-status \
	dashboard-up dashboard-down dashboard-restart dashboard-logs dashboard-status \
	all-up all-down all-restart all-status all-logs

help:  ## Show this help
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── RemSleep keeper (Memory Recall + Consolidation; applies for real) ──
keeper-up:  ## Start the RemSleep keeper
	@pm2 start ecosystem.config.js --only remsleep-keeper
	@pm2 save
keeper-down:  ## Stop + remove the RemSleep keeper
	@pm2 delete remsleep-keeper 2>/dev/null || true
	@pm2 save
keeper-restart:  ## Restart (or start) the RemSleep keeper
	@pm2 startOrRestart ecosystem.config.js --only remsleep-keeper --update-env
	@pm2 save
keeper-logs:  ## Follow the RemSleep keeper log
	@pm2 logs remsleep-keeper
keeper-status:  ## Show the RemSleep keeper status
	@pm2 describe remsleep-keeper

# ── Somatic HTTP MCP server (:7180) ──
somatic-http-up:  ## Start the somatic HTTP server (:7180)
	@pm2 start ecosystem.config.js --only apprenticeship-somatic-http
	@pm2 save
somatic-http-down:  ## Stop + remove the somatic HTTP server
	@pm2 delete apprenticeship-somatic-http 2>/dev/null || true
	@pm2 save
somatic-http-restart:  ## Restart (or start) the somatic HTTP server
	@pm2 startOrRestart ecosystem.config.js --only apprenticeship-somatic-http --update-env
	@pm2 save
somatic-http-logs:  ## Follow the somatic HTTP server log
	@pm2 logs apprenticeship-somatic-http
somatic-http-status:  ## Show the somatic HTTP server status
	@pm2 describe apprenticeship-somatic-http

# ── Autonomic HTTP MCP server (:7181) ──
autonomic-http-up:  ## Start the autonomic HTTP server (:7181)
	@pm2 start ecosystem.config.js --only apprenticeship-autonomic-http
	@pm2 save
autonomic-http-down:  ## Stop + remove the autonomic HTTP server
	@pm2 delete apprenticeship-autonomic-http 2>/dev/null || true
	@pm2 save
autonomic-http-restart:  ## Restart (or start) the autonomic HTTP server
	@pm2 startOrRestart ecosystem.config.js --only apprenticeship-autonomic-http --update-env
	@pm2 save
autonomic-http-logs:  ## Follow the autonomic HTTP server log
	@pm2 logs apprenticeship-autonomic-http
autonomic-http-status:  ## Show the autonomic HTTP server status
	@pm2 describe apprenticeship-autonomic-http
autonomic-stop:  ## Deterministic halt: stop the autonomic HTTP server AND the keeper
	@$(MAKE) autonomic-http-down
	@$(MAKE) keeper-down

# ── Autonomic substrate janitor (quarantine snapshots) ──
janitor-up:  ## Start the autonomic substrate janitor
	@pm2 start ecosystem.config.js --only autonomic-substrate-janitor
	@pm2 save
janitor-down:  ## Stop + remove the autonomic substrate janitor
	@pm2 delete autonomic-substrate-janitor 2>/dev/null || true
	@pm2 save
janitor-restart:  ## Restart (or start) the autonomic substrate janitor
	@pm2 startOrRestart ecosystem.config.js --only autonomic-substrate-janitor --update-env
	@pm2 save
janitor-logs:  ## Follow the autonomic substrate janitor log
	@pm2 logs autonomic-substrate-janitor
janitor-status:  ## Show the autonomic substrate janitor status
	@pm2 describe autonomic-substrate-janitor

# ── Status dashboard (:7182 self-refreshing HTML view) ──
dashboard-up:  ## Start the status dashboard HTTP server (:7182)
	@pm2 start ecosystem.config.js --only status-dashboard
	@pm2 save
dashboard-down:  ## Stop + remove the status dashboard
	@pm2 delete status-dashboard 2>/dev/null || true
	@pm2 save
dashboard-restart:  ## Restart (or start) the status dashboard
	@pm2 startOrRestart ecosystem.config.js --only status-dashboard --update-env
	@pm2 save
dashboard-logs:  ## Follow the status dashboard log
	@pm2 logs status-dashboard
dashboard-status:  ## Show the status dashboard status
	@pm2 describe status-dashboard

# ── All services ──
all-up:  ## Start every service
	@pm2 start ecosystem.config.js
	@pm2 save
all-down:  ## Stop + remove every service
	@pm2 delete ecosystem.config.js 2>/dev/null || true
	@pm2 save
all-restart:  ## Restart (or start) every service
	@pm2 startOrRestart ecosystem.config.js --update-env
	@pm2 save
all-status:  ## Show pm2 status + HTTP port health
	@pm2 status
	@printf "  somatic   :7180  "; lsof -iTCP:7180 -sTCP:LISTEN >/dev/null 2>&1 && echo "listening" || echo "down"
	@printf "  autonomic :7181  "; lsof -iTCP:7181 -sTCP:LISTEN >/dev/null 2>&1 && echo "listening" || echo "down"
	@printf "  dashboard :7182  "; lsof -iTCP:7182 -sTCP:LISTEN >/dev/null 2>&1 && echo "listening" || echo "down"
all-logs:  ## Follow every service log
	@pm2 logs

save:  ## Persist the pm2 process list (boot resurrection)
	@pm2 save
