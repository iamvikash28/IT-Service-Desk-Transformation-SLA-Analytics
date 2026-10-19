
import argparse
import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import get_connection

CATEGORIES = [
    "Access Request",
    "Application Error",
    "Hardware",
    "Network",
    "Password Reset",
    "Software Installation",
    "Other",
]

DESCRIPTIONS = {
    "Access Request": [
        "Need access to the shared folder",
        "New starter needs internal tool access",
    ],
    "Application Error": [
        "Application crashes after sign-in",
        "Error appears exporting a report",
    ],
    "Hardware": [
        "Laptop will not power on",
        "Keyboard keys are not responding",
    ],
    "Network": [
        "VPN disconnects from home",
        "Wi-Fi drops every few minutes",
    ],
    "Password Reset": [
        "Forgot password and cannot sign in",
        "Account locked after multiple attempts",
    ],
    "Software Installation": [
        "Need approved software installed",
        "Installer fails with an error",
    ],
    "Other": [
        "General IT assistance requested",
        "Unexpected workstation issue",
    ],
}

PRIORITIES = ["Critical", "High", "Medium", "Low"]
SLA_HOURS = {"Critical": 4, "High": 8, "Medium": 24, "Low": 72}

DEPARTMENTS = [
    "Finance", "Human Resources", "Sales", "Operations",
    "Engineering", "Customer Support", "General",
]

TEAMS = [
    "Service Desk", "Infrastructure", "Applications",
    "Endpoint Support", "Identity & Access",
]

STATUSES = ["Open", "In Progress", "Pending", "Resolved", "Closed"]


def main():
    parser = argparse.ArgumentParser(
        description="Generate and load synthetic service desk tickets."
    )
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be greater than zero")

    random.seed(args.seed)
    now = datetime.now().replace(microsecond=0)
    rows = []

    for i in range(1, args.count + 1):
        category = random.choice(CATEGORIES)
        priority = random.choices(
            PRIORITIES, weights=[5, 20, 50, 25]
        )[0]
        status = random.choices(
            STATUSES, weights=[18, 20, 8, 38, 16]
        )[0]

        created = now - timedelta(
            days=random.randint(0, 365),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        first_response = None
        if random.random() > 0.12:
            first_response = created + timedelta(
                minutes=random.randint(2, 120)
            )

        resolved = None
        if status in ("Resolved", "Closed"):
            duration_minutes = random.randint(
                10, SLA_HOURS[priority] * 120
            )
            resolved = created + timedelta(
                minutes=duration_minutes
            )

            if resolved > now:
                resolved = now - timedelta(minutes=1)

            if resolved < created:
                resolved = created + timedelta(minutes=1)

        sla_due = created + timedelta(
            hours=SLA_HOURS[priority]
        )

        rows.append({
            "external_ticket_key": f"SD-{i:06d}",
            "title": f"{category} - {random.choice(DESCRIPTIONS[category])}",
            "description": random.choice(DESCRIPTIONS[category]),
            "category": category,
            "priority": priority,
            "department": random.choice(DEPARTMENTS),
            "assigned_team": random.choice(TEAMS),
            "status": status,
            "created_at": created,
            "first_response_at": first_response,
            "resolved_at": resolved,
            "sla_due_at": sla_due,
            "reopened_count": random.choices(
                [0, 1, 2, 3], weights=[84, 12, 3, 1]
            )[0],
            "resolution_code": (
                random.choice([
                    "Resolved", "Workaround",
                    "User guidance", "Referred"
                ])
                if resolved else None
            ),
        })

    # Write a CSV copy of the synthetic dataset.
    csv_path = ROOT / "data" / "synthetic_tickets.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()

        for row in rows:
            writer.writerow({
                key: value.isoformat(sep=" ")
                if isinstance(value, datetime)
                else value
                for key, value in row.items()
            })

    # Load synthetic tickets into MySQL.
    # Existing demo tickets will be deleted first.
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM ticket_history")
        cur.execute("DELETE FROM support_tickets")

        insert_sql = """
            INSERT INTO support_tickets (
                external_ticket_key,
                title,
                description,
                category,
                priority,
                department,
                assigned_team,
                status,
                created_at,
                first_response_at,
                resolved_at,
                sla_due_at,
                reopened_count,
                resolution_code
            )
            VALUES (
                %(external_ticket_key)s,
                %(title)s,
                %(description)s,
                %(category)s,
                %(priority)s,
                %(department)s,
                %(assigned_team)s,
                %(status)s,
                %(created_at)s,
                %(first_response_at)s,
                %(resolved_at)s,
                %(sla_due_at)s,
                %(reopened_count)s,
                %(resolution_code)s
            )
        """

        cur.executemany(insert_sql, rows)
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    print(f"Successfully loaded {len(rows):,} synthetic tickets.")
    print(f"CSV file saved to: {csv_path}")


if __name__ == "__main__":
    main()
