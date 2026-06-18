// PM2 process definitions for the practice-theory-implementation long-lived
// services. Mirrors the Cognabot ops model (make as the front-door, pm2 as the
// supervisor): `make keeper-up` / `make up` start these; auto-restart on crash,
// and `pm2 save` + the existing pm2 boot agent resurrect them on reboot.
//
// All three reuse the launcher scripts under scripts/ so the env wiring lives in
// one place. The RemSleep keeper applies for real (preview OFF). The two HTTP
// servers are the Phase 2b long-lived MCP surfaces — defined here so they are
// ready to start, but only the keeper is started by default.

const cwd = __dirname;
const common = {
  interpreter: "bash",
  cwd,
  autorestart: true,
  max_restarts: 10,
  min_uptime: 15000,
  exp_backoff_restart_delay: 5000,
  kill_timeout: 15000,
  merge_logs: true,
};

module.exports = {
  apps: [
    {
      ...common,
      name: "remsleep-keeper",
      script: "./scripts/remsleep_service.sh",
      out_file: "./data/remsleep_service.log",
      error_file: "./data/remsleep_service.log",
    },
    {
      ...common,
      name: "apprenticeship-somatic-http",
      script: "./scripts/somatic_http_server.sh",
      out_file: "./data/somatic_http.log",
      error_file: "./data/somatic_http.log",
    },
    {
      ...common,
      name: "apprenticeship-autonomic-http",
      script: "./scripts/autonomic_http_server.sh",
      out_file: "./data/autonomic_http.log",
      error_file: "./data/autonomic_http.log",
    },
    {
      // Generic autonomic scheduler: periodically creates an LLM practitioner
      // for the configured somatic practice. See config/somatic_scheduler.yaml.
      ...common,
      name: "somatic-scheduler",
      script: "./scripts/somatic_scheduler_service.sh",
      out_file: "./data/somatic_scheduler.pm2.log",
      error_file: "./data/somatic_scheduler.pm2.log",
    },
    {
      // Long-lived periodic service: snapshot the loop's substrate
      // self-amendments onto the autonomic/substrate quarantine branch for
      // review. It stays online between passes so PM2 status and boot
      // resurrection reflect actual health.
      ...common,
      name: "autonomic-substrate-janitor",
      script: "./scripts/autonomic_substrate_janitor.sh",
      out_file: "./data/substrate_janitor.log",
      error_file: "./data/substrate_janitor.log",
    },
    {
      // Self-refreshing HTTP status dashboard (:7182): Judge/Smoother inbox
      // counts, open enactments with age, unaddressed Frictions. Reads the
      // trail read-only on each request. Same view as the
      // render_status_dashboard affordance, served live.
      ...common,
      name: "status-dashboard",
      script: "./scripts/status_dashboard_server.sh",
      out_file: "./data/status_dashboard.log",
      error_file: "./data/status_dashboard.log",
    },
  ],
};
