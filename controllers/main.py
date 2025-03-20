from flask import Flask, render_template, request, redirect, url_for, flash, session
from controllers.models import db, User, Task, Recommendation, UserProfile, Schedule,ActivityLog
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date,datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this for production

# Initialize SQLAlchemy with the app
db.init_app(app)

def create_tables():
    with app.app_context():
        db.create_all()
        # Creating a dummy user if one doesn't exist (for testing)
        if not User.query.filter_by(username="testuser").first():
            dummy_password = generate_password_hash("hashedpassword", method='pbkdf2:sha256')
            user = User(username="testuser", email="test@example.com", password_hash=dummy_password)
            db.session.add(user)
            db.session.commit()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    # For testing purposes, using session or default to user_id=1.
    user_id = session.get("user_id", 1)
    tasks = Task.query.filter_by(user_id=user_id).all()
    recommendations = Recommendation.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', tasks=tasks, recommendations=recommendations)

@app.route('/profile')
def profile():
    # Ensure the user is logged in
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your profile.", "error")
        return redirect(url_for('login'))
    
    # Retrieve the user record
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('login'))
    
    # Retrieve the user's profile record (if it exists)
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    # Construct the userData dictionary
    userData = {
        "username": user.username,
        "email": user.email,
        "workStartTime": profile.work_start_time.strftime("%H:%M") if profile and profile.work_start_time else "09:00",
        "workEndTime": profile.work_end_time.strftime("%H:%M") if profile and profile.work_end_time else "17:00",
        "breakPreference": profile.break_preference if profile and profile.break_preference else "medium",
        "streakCount": profile.streak_count if profile and profile.streak_count is not None else 0,
        # For demonstration purposes; replace with real data if available.
        "lastTask": "Project Update",
        "lastDate": profile.last_active_date.strftime("%d %B %Y") if profile and profile.last_active_date else "N/A"
    }
    
    # Render the profile template with the userData dictionary
    return render_template("profile.html", userData=userData)


@app.route('/activity')
def activity():
    return "Activity Page"


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('index'))

@app.route('/recommendations', methods=['GET'])
def recommendations():
    # Ensure the user is logged in (otherwise default to user_id=1 for testing)
    user_id = session.get("user_id", 1)

    # Fetch user record
    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('login'))

    # Mock or fetch user interests from the DB. 
    # If you don't store interests, you can define them manually or skip entirely.
    user_interests = ["Mathematics", "Problem-Solving", "Time Management"]

    # Fetch user recommendations from the DB
    # (Assuming your Recommendation model has fields: id, user_id, recommendation_text, created_at, etc.)
    recs = Recommendation.query.filter_by(user_id=user_id).all()

    return render_template(
        'recommendations.html',
        user=user,
        user_interests=user_interests,
        recommendations=recs
    )

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    user_id = session.get("user_id", None)
    if not user_id:
        flash("Please log in to set preferences.", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        work_start_time = request.form.get('workStartTime')
        work_end_time = request.form.get('workEndTime')
        break_preference = request.form.get('breakPreference')
        
        # Optionally, convert the string times to Python time objects
        # Here we assume the input is in HH:MM format.
        from datetime import datetime
        start_time_obj = datetime.strptime(work_start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(work_end_time, "%H:%M").time()
        
        # Fetch or create the UserProfile record
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        profile.work_start_time = start_time_obj
        profile.work_end_time = end_time_obj
        profile.break_preference = break_preference
        db.session.commit()
        
        flash("Preferences saved successfully!", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('preferences.html')

@app.route('/timer_schedule', methods=['GET', 'POST'])
def timer_schedule():
    user_id = session.get("user_id", 1)
    # Query pending (or in-progress) tasks from the Task table.
    # You may also filter by today's date if you have a date column.
    tasks = Task.query.filter_by(user_id=user_id).filter(Task.status != 'completed').all()
    current_date = date.today().strftime("%Y-%m-%d")
    return render_template('timer_schedule.html', tasks=tasks, current_date=current_date)

@app.route('/log_activity', methods=['POST'])
def log_activity():
    user_id = session.get("user_id", 1)
    task_id = request.form.get("active_task_id")
    try:
        elapsed_time = int(request.form.get("elapsed_time", 0))
    except ValueError:
        elapsed_time = 0

    if task_id:
        task = Task.query.get(task_id)
        if task:
            # Convert estimated_time (in minutes) to seconds (if it exists)
            estimated_seconds = task.estimated_time * 60 if task.estimated_time else 0

            # Compare elapsed time with the estimated time.
            if elapsed_time >= estimated_seconds and estimated_seconds > 0:
                task.status = 'completed'
            else:
                task.status = 'in-progress'

            # Create an ActivityLog entry
            log = ActivityLog(
                user_id=user_id,
                task_id=task.id,
                status=task.status,
                end_time=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()

            flash(f"Activity logged: {elapsed_time} seconds. Task marked as {task.status}.", "success")
        else:
            flash("Task not found.", "error")
    else:
        flash("No active task selected.", "error")
    return redirect(url_for('timer_schedule'))


@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    # This route may be used if you want to mark a task complete outside the timer flow.
    task = Task.query.get(task_id)
    if task:
        task.status = 'completed'
        log = ActivityLog(user_id=task.user_id, task_id=task.id, status='completed', end_time=datetime.utcnow())
        db.session.add(log)
        db.session.commit()
        flash("Task marked as completed.", "success")
    else:
        flash("Task not found.", "error")
    return redirect(url_for('dashboard'))

# ------------------ Signup Route ------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template('signup.html')
        
        # Check if user already exists (by username or email)
        existing_user = User.query.filter((User.username == name) | (User.email == email)).first()
        if existing_user:
            flash("User already exists with that name or email", "error")
            return render_template('signup.html')

        # Create new user with hashed password using pbkdf2:sha256
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=name, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

# ------------------ Login Route ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password", "error")
            return render_template('login.html')
        
        session["user_id"] = user.id

        # Check if the user's preferences have been set.
        # If no profile exists, then it's considered the first login.
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            flash("Please set your preferences.", "info")
            return redirect(url_for('preferences'))
        
        flash("Logged in successfully", "success")
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        # Extract form data from the modal form
        task_name = request.form.get('name')
        estimated_time = request.form.get('estimated_time')
        deadline = request.form.get('deadline')
        priority = request.form.get('priority')
        
        # Get the current user's id; here we default to 1 for testing.
        user_id = session.get("user_id", 1)
        
        priority_mapping = {'low': 1, 'medium': 2, 'high': 3}
        priority = priority_mapping.get(priority, 0)
        # Create a new Task object (adjust the fields as necessary)
        new_task = Task(
            user_id=user_id,
            name=task_name,
            estimated_time=int(estimated_time),
            priority=int(priority)
            # You can add additional processing for the deadline if needed.
        )
        db.session.add(new_task)
        db.session.commit()

        flash("Task added successfully!", "success")
        return redirect(url_for('dashboard'))
    
    # For a GET request, you might render a dedicated template for adding a task.
    # Since you're using a modal on the dashboard, you could simply redirect back.
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    create_tables()  # Ensure tables are created before the app runs
    app.run(debug=True)
