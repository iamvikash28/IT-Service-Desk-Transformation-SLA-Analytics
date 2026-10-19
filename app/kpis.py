def resolution_hours(created_at, resolved_at):
    if not created_at or not resolved_at:
        return None
    return round((resolved_at - created_at).total_seconds() / 3600, 2)

def sla_status(now, due_at, resolved_at=None):
    if due_at is None:
        return "Not applicable"
    if resolved_at is not None:
        return "Met" if resolved_at <= due_at else "Breached"
    return "Open overdue" if now > due_at else "Open on track"

def compliance_rate(statuses):
    eligible = [s for s in statuses if s in ("Met", "Breached")]
    if not eligible:
        return None
    return round(100 * sum(s == "Met" for s in eligible) / len(eligible), 2)
