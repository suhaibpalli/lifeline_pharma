#!/usr/bin/env python3
"""Update the Lifeline SMTP template while Uptime Kuma is stopped."""
import argparse
import json
from pathlib import Path
import sqlite3
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", default="pharma_uptime")
    parser.add_argument("--database", type=Path, default=Path("/opt/pharma/uptime-kuma-data/kuma.db"))
    args = parser.parse_args()
    running = subprocess.check_output(
        ["docker", "inspect", "-f", "{{.State.Running}}", args.container], text=True
    ).strip()
    if running != "false":
        raise RuntimeError("Stop Uptime Kuma before updating its notification configuration")
    if not args.database.is_file():
        raise FileNotFoundError(args.database)

    updated = 0
    with sqlite3.connect(args.database) as database:
        rows = database.execute("SELECT id,config FROM notification WHERE name=?", ("Lifeline email alerts",))
        for notification_id, raw_config in rows.fetchall():
            config = json.loads(raw_config)
            if config.get("type") != "smtp":
                continue
            before = dict(config)
            if config.get("customSubject") == "[Lifeline] {{STATUS}} - {{NAME}}":
                config["customSubject"] = "[Lifeline] {{status}} - {{name}}"
            # Preserve encrypted transport and server certificate verification.
            config["smtpIgnoreSTARTTLS"] = False
            config["smtpIgnoreTLSError"] = False
            if config != before:
                database.execute("UPDATE notification SET config=? WHERE id=?", (json.dumps(config), notification_id))
                updated += 1
    print(f"Updated {updated} SMTP notification configuration(s); credentials and recipients preserved.")


if __name__ == "__main__":
    main()
