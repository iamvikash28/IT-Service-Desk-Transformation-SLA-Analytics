import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.db import query_all
checks=query_all("""SELECT 'ticket count' check_name,COUNT(*) issue_count FROM support_tickets
UNION ALL SELECT 'resolution before creation',COUNT(*) FROM support_tickets WHERE resolved_at<created_at
UNION ALL SELECT 'first response before creation',COUNT(*) FROM support_tickets WHERE first_response_at<created_at
UNION ALL SELECT 'missing title',COUNT(*) FROM support_tickets WHERE title IS NULL OR TRIM(title)=''
UNION ALL SELECT 'missing description',COUNT(*) FROM support_tickets WHERE description IS NULL OR TRIM(description)=''
UNION ALL SELECT 'missing SLA due date',COUNT(*) FROM support_tickets WHERE sla_due_at IS NULL""")
print("Data quality report")
for row in checks:print(f"- {row['check_name']}: {row['issue_count']}")
