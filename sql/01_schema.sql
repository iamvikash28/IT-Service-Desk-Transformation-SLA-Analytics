CREATE DATABASE IF NOT EXISTS service_desk CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE service_desk;
CREATE TABLE IF NOT EXISTS categories(category_id INT AUTO_INCREMENT PRIMARY KEY,category_name VARCHAR(80) NOT NULL UNIQUE) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS priorities(priority_id INT AUTO_INCREMENT PRIMARY KEY,priority_name VARCHAR(20) NOT NULL UNIQUE,sort_order TINYINT NOT NULL UNIQUE) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS departments(department_id INT AUTO_INCREMENT PRIMARY KEY,department_name VARCHAR(100) NOT NULL UNIQUE) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS support_teams(team_id INT AUTO_INCREMENT PRIMARY KEY,team_name VARCHAR(100) NOT NULL UNIQUE) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS sla_policies(sla_policy_id INT AUTO_INCREMENT PRIMARY KEY,priority_name VARCHAR(20) NOT NULL,target_hours INT NOT NULL,is_active BOOLEAN NOT NULL DEFAULT TRUE,CHECK(target_hours>0),UNIQUE KEY uq_sla_priority_active(priority_name,is_active)) ENGINE=InnoDB;
INSERT IGNORE INTO categories(category_name) VALUES('Access Request'),('Application Error'),('Hardware'),('Network'),('Password Reset'),('Software Installation'),('Other');
INSERT IGNORE INTO priorities(priority_name,sort_order) VALUES('Critical',1),('High',2),('Medium',3),('Low',4);
INSERT IGNORE INTO departments(department_name) VALUES('Finance'),('Human Resources'),('Sales'),('Operations'),('Engineering'),('Customer Support'),('General');
INSERT IGNORE INTO support_teams(team_name) VALUES('Service Desk'),('Infrastructure'),('Applications'),('Endpoint Support'),('Identity & Access');
INSERT IGNORE INTO sla_policies(priority_name,target_hours,is_active) VALUES('Critical',4,TRUE),('High',8,TRUE),('Medium',24,TRUE),('Low',72,TRUE);
CREATE TABLE IF NOT EXISTS support_tickets(
 ticket_id BIGINT AUTO_INCREMENT PRIMARY KEY,external_ticket_key VARCHAR(24) UNIQUE,title VARCHAR(200) NOT NULL,description TEXT NOT NULL,
 category VARCHAR(80) NOT NULL,priority VARCHAR(20) NOT NULL,department VARCHAR(100) NOT NULL,assigned_team VARCHAR(100) NOT NULL,
 status ENUM('Open','In Progress','Pending','Resolved','Closed') NOT NULL DEFAULT 'Open',
 created_at DATETIME NOT NULL,first_response_at DATETIME NULL,resolved_at DATETIME NULL,sla_due_at DATETIME NULL,
 reopened_count INT NOT NULL DEFAULT 0,resolution_code VARCHAR(80) NULL,CHECK(reopened_count>=0),
 INDEX idx_ticket_created(created_at),INDEX idx_ticket_status_priority(status,priority),INDEX idx_ticket_category(category),
 INDEX idx_ticket_sla_due(sla_due_at),INDEX idx_ticket_team(assigned_team)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS ticket_history(
 history_id BIGINT AUTO_INCREMENT PRIMARY KEY,ticket_id BIGINT NOT NULL,changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 changed_by VARCHAR(100) NOT NULL DEFAULT 'demo-agent',field_name VARCHAR(80) NOT NULL,old_value VARCHAR(255),new_value VARCHAR(255),note VARCHAR(500),
 CONSTRAINT fk_history_ticket FOREIGN KEY(ticket_id) REFERENCES support_tickets(ticket_id) ON DELETE CASCADE,
 INDEX idx_history_ticket_changed(ticket_id,changed_at)
) ENGINE=InnoDB;
CREATE OR REPLACE VIEW vw_ticket_kpis AS
SELECT t.ticket_id,t.external_ticket_key,t.title,t.category,t.priority,t.department,t.assigned_team,t.status,t.created_at,
 t.first_response_at,t.resolved_at,t.sla_due_at,t.reopened_count,t.resolution_code,
 CASE WHEN t.first_response_at IS NOT NULL THEN TIMESTAMPDIFF(SECOND,t.created_at,t.first_response_at)/3600.0 END AS first_response_hours,
 CASE WHEN t.resolved_at IS NOT NULL THEN TIMESTAMPDIFF(SECOND,t.created_at,t.resolved_at)/3600.0 END AS resolution_hours,
 CASE WHEN t.sla_due_at IS NULL THEN 'Not applicable'
 WHEN t.resolved_at IS NOT NULL AND t.resolved_at<=t.sla_due_at THEN 'Met'
 WHEN t.resolved_at IS NOT NULL AND t.resolved_at>t.sla_due_at THEN 'Breached'
 WHEN t.resolved_at IS NULL AND NOW()>t.sla_due_at THEN 'Open overdue' ELSE 'Open on track' END AS sla_status
FROM support_tickets t;
-- Local demo account only. Change this password before any non-demo use.
CREATE USER IF NOT EXISTS 'service_desk_app'@'localhost' IDENTIFIED BY 'ChangeThis_LocalDemo_Only!';
GRANT SELECT,INSERT,UPDATE,DELETE ON service_desk.* TO 'service_desk_app'@'localhost';
FLUSH PRIVILEGES;
