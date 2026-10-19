from datetime import datetime,timedelta
from app.kpis import resolution_hours,sla_status,compliance_rate
def test_resolution_hours():
 s=datetime(2025,1,1,10);assert resolution_hours(s,s+timedelta(hours=3,minutes=30))==3.5
 assert resolution_hours(s,None) is None
def test_sla_status():
 now=datetime(2025,1,1,15);due=datetime(2025,1,1,14)
 assert sla_status(now,due,datetime(2025,1,1,13))=="Met"
 assert sla_status(now,due,datetime(2025,1,1,15))=="Breached"
 assert sla_status(now,due,None)=="Open overdue"
def test_compliance_rate():
 assert compliance_rate(["Met","Breached","Open overdue"])==50.0
 assert compliance_rate(["Open overdue"]) is None
