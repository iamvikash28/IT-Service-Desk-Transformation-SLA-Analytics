from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import query_all, execute
from app.classifier import suggest_category

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    stats = query_all("""
        SELECT COUNT(*) AS total_tickets,
          SUM(status NOT IN ('Resolved','Closed')) AS open_backlog,
          ROUND(AVG(CASE WHEN resolved_at IS NOT NULL
            THEN TIMESTAMPDIFF(SECOND,created_at,resolved_at)/3600 END),2) AS avg_resolution_hours,
          ROUND(100*SUM(CASE WHEN resolved_at IS NOT NULL AND resolved_at<=sla_due_at
            THEN 1 ELSE 0 END)/NULLIF(SUM(resolved_at IS NOT NULL AND sla_due_at IS NOT NULL),0),2)
            AS resolved_sla_compliance_pct
        FROM support_tickets
    """)[0]
    tickets = query_all("""SELECT ticket_id,title,category,priority,status,assigned_team,created_at,sla_due_at
        FROM support_tickets ORDER BY created_at DESC LIMIT 100""")
    return render_template("index.html", stats=stats, tickets=tickets)

@bp.get("/tickets/new")
def new_ticket():
    return render_template("new_ticket.html",
        categories=query_all("SELECT category_name FROM categories ORDER BY category_name"),
        priorities=query_all("SELECT priority_name FROM priorities ORDER BY sort_order"),
        departments=query_all("SELECT department_name FROM departments ORDER BY department_name"),
        teams=query_all("SELECT team_name FROM support_teams ORDER BY team_name"))

@bp.post("/tickets")
def create_ticket():
    title=request.form.get("title","").strip()
    description=request.form.get("description","").strip()
    category=request.form.get("category","Other")
    priority=request.form.get("priority","Medium")
    department=request.form.get("department","General")
    team=request.form.get("assigned_team","Service Desk")
    if not title or not description:
        flash("Title and description are required.","error")
        return redirect(url_for("main.new_ticket"))
    execute("""INSERT INTO support_tickets
        (title,description,category,priority,department,assigned_team,status,created_at,sla_due_at,reopened_count)
        SELECT %s,%s,%s,%s,%s,%s,'Open',NOW(),DATE_ADD(NOW(),INTERVAL target_hours HOUR),0
        FROM sla_policies WHERE priority_name=%s AND is_active=1 LIMIT 1""",
        (title,description,category,priority,department,team,priority))
    flash("Ticket created.","success")
    return redirect(url_for("main.index"))

@bp.post("/tickets/<int:ticket_id>/status")
def update_status(ticket_id):
    status=request.form.get("status","")
    if status not in {"Open","In Progress","Pending","Resolved","Closed"}:
        flash("Invalid status.","error")
        return redirect(url_for("main.index"))
    if status in {"Resolved","Closed"}:
        execute("UPDATE support_tickets SET status=%s,resolved_at=COALESCE(resolved_at,NOW()) WHERE ticket_id=%s",(status,ticket_id))
    else:
        execute("UPDATE support_tickets SET status=%s WHERE ticket_id=%s",(status,ticket_id))
    flash(f"Ticket #{ticket_id} updated.","success")
    return redirect(url_for("main.index"))

@bp.post("/classify")
def classify():
    description=request.form.get("description","")
    return render_template("classification.html",description=description,result=suggest_category(description))
