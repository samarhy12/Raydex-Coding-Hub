import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

# Initialize the app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Use environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')  # Use environment variable

# Initialize the database, bcrypt, and login manager
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login if user is not authenticated

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    progress = db.relationship('Progress', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Enrollment Model (Many-to-Many relationship between User and Course)
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    def __repr__(self):
        return f"Enrollment(User ID: {self.user_id}, Course ID: {self.course_id})"

# Course Model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(20), nullable=False, default='default.jpg')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    lessons = db.relationship('Lesson', backref='course', lazy=True)

    def __repr__(self):
        return f"Course('{self.title}', '{self.price}')"

# Lesson Model (One-to-Many relationship between Course and Lesson)
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    quiz = db.Column(db.Text, nullable=True)
    assignment = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    progress = db.relationship('Progress', backref='lesson', lazy=True)

    def __repr__(self):
        return f"Lesson('{self.title}', 'Course ID: {self.course_id}')"

# Progress Model (Tracking user's progress in lessons)
class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Progress(User ID: {self.user_id}, Lesson ID: {self.lesson_id}, Completed: {self.completed})"

# Post Model (Forum Post Model)
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

# Comment Model (Forum Comment Model)
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"


# Load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Route
@app.route('/')
def home():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

# All Courses Route
@app.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

# Single Course Route
@app.route('/course/<int:course_id>', methods=['GET'])
def course(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    
    # Initialize enrollment and progress tracking variables
    enrolled = False
    completed_lessons_count = 0
    lessons_count = len(lessons)
    completed_lessons_ids = []
    next_lesson = None

    # Check if the user is logged in and enrolled
    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        if enrollment:
            enrolled = True
            
            # Get completed lessons
            completed_lessons = Progress.query.filter_by(user_id=current_user.id).filter(Progress.lesson_id.in_([lesson.id for lesson in lessons])).all()
            completed_lessons_count = len(completed_lessons)
            completed_lessons_ids = [progress.lesson_id for progress in completed_lessons]

            # Find the next incomplete lesson for the "Continue" button
            for lesson in lessons:
                if lesson.id not in completed_lessons_ids:
                    next_lesson = lesson
                    break

    return render_template(
        'course.html', 
        course=course, 
        lessons=lessons, 
        enrolled=enrolled, 
        completed_lessons_count=completed_lessons_count, 
        lessons_count=lessons_count, 
        completed_lessons_ids=completed_lessons_ids, 
        next_lesson=next_lesson
    )


@app.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    # Check if user is already enrolled
    if Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first():
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('course', course_id=course_id))

    # Enroll user in the course
    enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    flash('You have been enrolled in the course!', 'success')
    return redirect(url_for('course', course_id=course_id))

# Lesson Route
# Route to mark lesson as completed
@app.route('/course/<int:course_id>/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def mark_completed(course_id, lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    # Mark lesson as completed by adding progress entry
    progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = Progress(user_id=current_user.id, lesson_id=lesson.id, completed=True)
        db.session.add(progress)
        db.session.commit()

    flash('Lesson marked as completed!', 'success')

    return redirect(url_for('lesson', course_id=course_id, lesson_id=lesson_id))




@app.route('/dashboard')
@login_required
def student_dashboard():
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_course_ids = [enrollment.course_id for enrollment in enrollments]

    # Fetch the courses the user is enrolled in
    courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()

    completed_lessons_count = {}
    lessons_count = {}

    for course in courses:
        lessons = Lesson.query.filter_by(course_id=course.id).all()
        lessons_count[course.id] = len(lessons)
        
        # Count the number of completed lessons for this user in the course
        completed_lessons = Progress.query.filter_by(user_id=current_user.id).filter(Progress.lesson_id.in_([lesson.id for lesson in lessons])).all()
        completed_lessons_count[course.id] = len(completed_lessons)

    # Prepare completed lesson IDs for easier rendering
    completed_lessons_ids = {course.id: [progress.lesson_id for progress in completed_lessons] for course in courses}

    return render_template('student_dashboard.html', courses=courses, completed_lessons_count=completed_lessons_count, lessons_count=lessons_count, completed_lessons_ids=completed_lessons_ids)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Redirect if user is already logged in

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch user from database
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))  # Redirect to home or dashboard
        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Redirect if user is already logged in

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/course/<int:course_id>/lesson/<int:lesson_id>', methods=['GET'])
@login_required
def lesson(course_id, lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()

    # Fetch the user's progress to check if the lesson is completed
    progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    completed = progress is not None

    # Determine the next lesson for navigation
    current_lesson_index = lessons.index(lesson)
    next_lesson = lessons[current_lesson_index + 1] if current_lesson_index + 1 < len(lessons) else None

    return render_template('lesson.html', lesson=lesson, next_lesson=next_lesson, completed=completed)

@app.route('/code-playground', methods=['GET'])
@login_required
def code_playground():
    return render_template('code_playground.html')


# User Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route("/forum")
def forum():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('forum.html', posts=posts)

# Route to view a single post and its comments
@app.route("/forum/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post.id).all()
    return render_template('view_post.html', post=post, comments=comments)

# Route to create a new post
@app.route("/forum/new_post", methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post = Post(title=title, content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('forum'))
    return render_template('create_post.html')

# Route to edit a post
@app.route("/forum/post/<int:post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)  # Forbidden if not the author

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    
    return render_template('edit_post.html', post=post)

# Route to delete a post
@app.route("/forum/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)  # Forbidden if not the author

    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('forum'))

# Route to create a comment on a post
@app.route("/forum/post/<int:post_id>/comment", methods=['POST'])
@login_required
def comment_on_post(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form['content']
    comment = Comment(content=content, author=current_user, post_id=post.id)
    db.session.add(comment)
    db.session.commit()
    flash('Your comment has been added!', 'success')
    return redirect(url_for('view_post', post_id=post.id))

# Route to delete a comment
@app.route("/forum/comment/<int:comment_id>/delete", methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        abort(403)  # Forbidden if not the author

    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been deleted!', 'success')
    return redirect(url_for('view_post', post_id=comment.post_id))

# PWA Manifest
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# PWA Service Worker
@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
