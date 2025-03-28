from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time

db = SQLAlchemy()

# User authentication and basic account details
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Relationships to other tables
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    tasks = db.relationship('Task', backref='user', lazy=True)
    activity_logs = db.relationship('ActivityLog', backref='user', lazy=True)
    schedules = db.relationship('Schedule', backref='user', lazy=True)
    recommendations = db.relationship('Recommendation', backref='user', lazy=True)

# Additional user details such as work hours, break preferences, and streak count
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    work_start_time = db.Column(db.Time, nullable=True)   # User's usual start time
    work_end_time = db.Column(db.Time, nullable=True)     # User's usual end time
    break_preference = db.Column(db.String(20), nullable=True)  # e.g., 'short' or 'long'
    streak_count = db.Column(db.Integer, default=0)  # Consecutive days the user has worked
    last_active_date = db.Column(db.Date, nullable=True)  # The last day the user was active

# Task management model including support for drag-and-drop ordering and rescheduling
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Integer, default=0)  # Lower/higher values can represent different priorities
    estimated_time = db.Column(db.Integer, nullable=True)  # Estimated time in minutes (e.g., 15, 45, 60+)
    sort_order = db.Column(db.Integer, nullable=True)  # Used for drag-and-drop ordering in the dashboard
    status = db.Column(db.String(20), nullable=False, default='pending')  # e.g., 'pending', 'in-progress', 'completed'
    reschedule_count = db.Column(db.Integer, default=0)  # Tracks how many times the task has been rescheduled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships to activity logs and schedules
    activity_logs = db.relationship('ActivityLog', backref='task', lazy=True)
    schedules = db.relationship('Schedule', backref='task', lazy=True)

# Logs for tracking user activity and task progress
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=True)  # e.g., 'in-progress', 'paused', 'completed'
    # Optionally, add fields such as pause_count or notes if needed

# Table to store AI-generated schedules for tasks
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    scheduled_date = db.Column(db.Date, nullable=False)  # The date on which the task is scheduled
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    # Additional fields (e.g., algorithm confidence scores) can be added as needed

# Table for storing recommendations generated by the system
class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recommendation_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
