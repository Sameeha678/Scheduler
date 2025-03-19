from flask import Flask, render_template, request, redirect, url_for, flash, session
from controllers.models import db, User, Task, Recommendation
from werkzeug.security import generate_password_hash, check_password_hash

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
    return "User Profile Page"

@app.route('/activity')
def activity():
    return "Activity Page"

@app.route('/recommendations')
def recommendations():
    return "Recommendations Page"

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for('index'))

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
