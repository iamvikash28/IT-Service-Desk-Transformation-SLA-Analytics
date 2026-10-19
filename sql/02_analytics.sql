USE service_desk;
-- Overall volume and backlog
SELECT COUNT(*) total_tickets,SUM(status NOT IN('Resolved','Closed')) open_backlog FROM support_tickets;
-- Monthly volume
SELECT DATE_FORMAT(created_at,'%Y-%m') ticket_month,COUNT(*) total_tickets FROM support_tickets GROUP BY ticket_month ORDER BY ticket_month;
-- Average and median resolution hours by category (MySQL 8 window functions)
WITH resolved AS(SELECT category,TIMESTAMPDIFF(SECOND,created_at,resolved_at)/3600.0 resolution_hours FROM support_tickets WHERE resolved_at IS NOT NULL),
ranked AS(SELECT category,resolution_hours,ROW_NUMBER() OVER(PARTITION BY category ORDER BY resolution_hours) rn,COUNT(*) OVER(PARTITION BY category) cnt FROM resolved)
SELECT category,ROUND(AVG(resolution_hours),2) avg_resolution_hours,
 ROUND(AVG(CASE WHEN rn IN(FLOOR((cnt+1)/2),FLOOR((cnt+2)/2)) THEN resolution_hours END),2) median_resolution_hours
FROM ranked GROUP BY category ORDER BY avg_resolution_hours DESC;
-- Resolved SLA compliance denominator: resolved tickets with a due timestamp
SELECT COUNT(*) resolved_with_sla,SUM(resolved_at<=sla_due_at) resolved_within_sla,SUM(resolved_at>sla_due_at) resolved_breached_sla,
 ROUND(100*SUM(resolved_at<=sla_due_at)/NULLIF(COUNT(*),0),2) resolved_sla_compliance_pct
FROM support_tickets WHERE resolved_at IS NOT NULL AND sla_due_at IS NOT NULL;
-- Open overdue tickets
SELECT priority,assigned_team,COUNT(*) open_overdue FROM support_tickets WHERE resolved_at IS NULL AND status NOT IN('Resolved','Closed') AND sla_due_at<NOW() GROUP BY priority,assigned_team ORDER BY open_overdue DESC;
-- Backlog aging
SELECT CASE WHEN TIMESTAMPDIFF(HOUR,created_at,NOW())<24 THEN '0-24 hours' WHEN TIMESTAMPDIFF(HOUR,created_at,NOW())<72 THEN '1-3 days' WHEN TIMESTAMPDIFF(HOUR,created_at,NOW())<168 THEN '3-7 days' ELSE '7+ days' END age_bucket,
 priority,COUNT(*) ticket_count FROM support_tickets WHERE status NOT IN('Resolved','Closed') GROUP BY age_bucket,priority;
-- Reopen rate
SELECT category,COUNT(*) ticket_count,SUM(reopened_count>0) reopened_tickets,ROUND(100*SUM(reopened_count>0)/NULLIF(COUNT(*),0),2) reopened_pct FROM support_tickets GROUP BY category ORDER BY reopened_pct DESC;
-- Workload
SELECT assigned_team,department,status,COUNT(*) ticket_count FROM support_tickets GROUP BY assigned_team,department,status;
-- Data-quality checks
SELECT 'resolution before creation' check_name,COUNT(*) issue_count FROM support_tickets WHERE resolved_at<created_at
UNION ALL SELECT 'first response before creation',COUNT(*) FROM support_tickets WHERE first_response_at<created_at
UNION ALL SELECT 'missing SLA due date',COUNT(*) FROM support_tickets WHERE sla_due_at IS NULL;
-- Power BI source
SELECT * FROM vw_ticket_kpis;
