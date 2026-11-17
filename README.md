# AI Freelance Job Hunter

Open-source job discovery for remote/freelance work, designed for Android and near-zero budget.

## First version
- Collects public RSS feeds from We Work Remotely and Remote OK.
- Normalizes and deduplicates listings into JSON and CSV.
- Provides a static dashboard with search and a device-local application tracker.
- Does not auto-apply. Always verify eligibility for applicants in Indonesia on the original listing.

## Enable dashboard
Repository Settings → Pages → Deploy from a branch → branch `main` → folder `/dashboard` → Save.

## Run collector
Open Actions → Collect remote jobs → Run workflow. It also runs every 6 hours (best effort).

Dashboard: https://satriamada-web.github.io/ai-freelance-job-hunter/

Sources: [We Work Remotely RSS](https://weworkremotely.com/remote-jobs.rss), [Remote OK RSS](https://remoteok.com/remote-jobs.rss). Missing salary/location/eligibility fields are left unknown, never guessed.

Requires Python 3.11+ for local testing. Collector uses only the Python standard library. GitHub Actions usage limits apply.