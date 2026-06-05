---
id: render_status_dashboard
name: Render status dashboard
materials:
- render_status_dashboard
---
Render the autonomic-loop status as a self-contained HTML dashboard: the Judge inbox count, the Smoother inbox count, the open-enactment count with each enactment's age, and the count of unaddressed Frictions. Writes the HTML to a file and returns its path, the live-server URL, and the headline counts. Read-only over the trail; it writes only the HTML artifact and does not restart services, clear queues, mark work handled, or change substrate. For an always-current view, leave the dashboard HTTP server running and open its URL; this affordance is the one-shot snapshot of the same view.
