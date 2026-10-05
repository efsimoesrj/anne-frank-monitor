# Anne Frank House ticket monitor

Every 5 minutes, this checks the public ticket calendar API
(`tickets.annefrank.org/api/v1/calendardates/...`) and sends a push notification to your phone
through [ntfy.sh](https://ntfy.sh) when a watched date becomes available (any time slot).
It sends one notification per date. If a date sells out and frees up again, you get another one.

## Setup

1. **Phone:** install the **ntfy** app (Android/iOS) and subscribe to a hard-to-guess topic,
   e.g. `annefrank-k39xq7m2p`.
2. **Local test** (PowerShell):
   ```powershell
   $env:NTFY_TOPIC = "annefrank-k39xq7m2p"
   python monitor.py --test      # a push should arrive on your phone
   python monitor.py --dry-run   # prints the current status of the watched dates
   ```
3. **GitHub:** create a **public** repo (free unlimited Actions minutes) and push this folder.
4. Go to **Settings → Secrets and variables → Actions**:
   - Secret `NTFY_TOPIC` = your topic
   - Variable `WATCH_DATES` = `2026-10-10..2026-10-12` (optional; this is the default.
     Use commas and `..` ranges for other dates.)
5. In the **Actions** tab, open "Anne Frank ticket monitor" and click **Run workflow** once to check that it works.
   After that it runs about every 5 minutes. GitHub can delay scheduled runs by a few minutes.

To stop it: Actions → the workflow → **Disable workflow**.
