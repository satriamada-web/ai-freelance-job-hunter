# AI Freelance Job Hunter

Open-source remote-job discovery for a near-zero budget and Android-first workflow.

## Current system
- Collects public listings from We Work Remotely RSS and the Himalayas public JSON API.
- Normalizes and deduplicates listings into JSON and CSV.
- Scores each listing (0–100) using transparent keyword rules for beginner-friendly roles, seniority signals, Indonesia location restrictions, and likely device needs.
- Stores source links separately from application links where the API provides both.
- Runs once daily through GitHub Actions. The Himalayas dataset refreshes daily, so frequent polling is unnecessary.
- Does not auto-apply. Always open the original listing, confirm the role is still open, verify Indonesia eligibility, and submit applications yourself.

## Data
- `data/jobs.json`: full records, fit score, difficulty, eligibility notes, Android feasibility, and reasons.
- `data/jobs.csv`: spreadsheet-friendly export.
- Scores are a first-pass heuristic, not a guarantee of hiring likelihood. The system does not infer missing salary, experience, country, or device requirements.

## Run manually
Open Actions → Collect remote jobs → Run workflow.

## Sources and attribution
- [We Work Remotely RSS](https://weworkremotely.com/remote-jobs.rss)
- [Himalayas Remote Jobs API](https://himalayas.app/api). Keep Himalayas attribution visible and use the API's `applicationLink` unchanged when applying. Do not republish these listings to third-party job aggregators, Google Jobs, or LinkedIn Jobs.

The optional static dashboard files remain in `dashboard/`, but GitHub Pages is not required for the current workflow. GitHub Actions usage limits apply.
