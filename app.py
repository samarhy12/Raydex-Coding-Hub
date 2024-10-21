import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_mail import Mail, Message
import secrets
from PIL import Image
from flask_migrate import Migrate
from cloudinary import uploader
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from dotenv import load_dotenv
import requests
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room, leave_room
from itsdangerous import URLSafeTimedSerializer

# Initialize the app
app = Flask(__name__)
load_dotenv()

# Flask configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Default if not found
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
app.config['MAIL_SERVER'] = 'mail.raydexhub.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('Raydex Hub', os.getenv('MAIL_USERNAME'))
app.config['MAIL_DEBUG'] = True

# Cloudinary configuration
app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv('CLOUDINARY_CLOUD_NAME')
app.config['CLOUDINARY_API_KEY'] = os.getenv('CLOUDINARY_API_KEY')
app.config['CLOUDINARY_API_SECRET'] = os.getenv('CLOUDINARY_API_SECRET')


PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'profile_pics')

mail = Mail(app)
socketio = SocketIO(app)

ADMIN_SUPPORT_ROOM = 'admin_support'
active_chats = {}
# Initialize Cloudinary
import cloudinary
cloudinary.config(
    cloud_name = app.config['CLOUDINARY_CLOUD_NAME'],
    api_key = app.config['CLOUDINARY_API_KEY'],
    api_secret = app.config['CLOUDINARY_API_SECRET']
)

# Initialize the database, bcrypt, and login manager
db = SQLAlchemy(app)
migrate = Migrate(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login if user is not authenticated

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Raydex Hub startup')

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
    is_admin = db.Column(db.Boolean, default=False)

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
    
    def save_image(self, file):
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(file.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(app.root_path, 'static/course_images', picture_fn)
        
        output_size = (300, 300)
        i = Image.open(file)
        i.thumbnail(output_size)
        i.save(picture_path)
        
        return picture_fn

# Lesson Model (One-to-Many relationship between Course and Lesson)
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    progress = db.relationship('Progress', backref='lesson', lazy=True)
    videos = db.relationship('Video', backref='lesson', lazy=True, cascade="all, delete-orphan")
    quiz = db.relationship('Quiz', backref='lesson', uselist=False, lazy=True, cascade="all, delete-orphan")
    assignment = db.relationship('Assignment', backref='lesson', uselist=False, lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Lesson('{self.title}', 'Course ID: {self.course_id}')"
    
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)

    def __repr__(self):
        return f"Quiz('Lesson ID: {self.lesson_id}')"

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)

    def __repr__(self):
        return f"Assignment('Lesson ID: {self.lesson_id}')"

# New Video Model
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    public_id = db.Column(db.String(255), nullable=False)  # Store Cloudinary public_id
    order = db.Column(db.Integer, nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)

    def __repr__(self):
        return f"Video('{self.title}', 'Lesson ID: {self.lesson_id}')"

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

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    course = db.relationship('Course', backref='chat_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

    def __repr__(self):
        return f"ChatMessage('{self.content}', '{self.timestamp}')"
    
application = app
from flask.cli import with_appcontext
import click

@click.command(name='create_admin')
@with_appcontext
def create_admin():
    username = click.prompt('Enter admin username', type=str)
    email = click.prompt('Enter admin email', type=str)
    password = click.prompt('Enter admin password', type=str, hide_input=True, confirmation_prompt=True)

    user = User(username=username, email=email, password=bcrypt.generate_password_hash(password), is_admin=True)
    db.session.add(user)
    db.session.commit()
    click.echo(f'Admin user {username} created successfully.')

app.cli.add_command(create_admin)

# Helper Functions
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def send_email(subject, recipient, template, **kwargs):
    msg = Message(
        subject,
        sender='Raydex Hub <info@raydexhub.com>',
        recipients=[recipient]
    )
    
    # Only render and send the HTML version of the email
    msg.html = render_template(template + '.html', **kwargs)
    
    try:
        mail.send(msg)  # Send the email
        print(f"HTML email sent to {recipient}")
    except Exception as e:
        print(f"Failed to send HTML email: {e}")

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def upload_video_to_cloudinary(file):
    try:
        result = upload(file, resource_type="video")
        return result['public_id']
    except Exception as e:
        app.logger.error(f"Failed to upload video to Cloudinary: {e}")
        return None

def get_cloudinary_video_url(public_id):
    try:
        url, options = cloudinary_url(public_id, resource_type="video", format="mp4")
        return url
    except Exception as e:
        app.logger.error(f"Failed to get Cloudinary video URL: {e}")
        return None
    
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def delete_video_from_cloudinary(public_id):
    if not public_id:
        current_app.logger.error("Attempted to delete video with empty public_id")
        return False

    try:
        result = uploader.destroy(public_id, resource_type="video", invalidate=True)
        
        if result.get('result') == 'ok':
            current_app.logger.info(f"Successfully deleted video with public_id: {public_id}")
            return True
        else:
            current_app.logger.warning(f"Failed to delete video with public_id: {public_id}. Cloudinary response: {result}")
            return False
    
    except cloudinary.exceptions.Error as e:
        current_app.logger.error(f"Cloudinary error when deleting video {public_id}: {str(e)}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error when deleting video {public_id}: {str(e)}")
        return False

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
@app.route('/course/<int:course_id>')
def course(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    
    enrolled = False
    completed_lessons_count = 0
    lessons_count = len(lessons)
    completed_lessons_ids = []
    next_lesson = None

    if current_user.is_authenticated:
        enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
        if enrollment:
            enrolled = True
            completed_lessons = Progress.query.filter_by(user_id=current_user.id).filter(Progress.lesson_id.in_([lesson.id for lesson in lessons])).all()
            completed_lessons_count = len(completed_lessons)
            completed_lessons_ids = [progress.lesson_id for progress in completed_lessons]

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

def verify_paystack_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        return response_data['status'], response_data['data']
    return False, None

@app.route('/course/<int:course_id>/enroll', methods=['GET', 'POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Check if user is already enrolled
    if Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first():
        return jsonify({"success": False, "message": "Already enrolled"}), 400

    if request.method == 'POST':
        # Handle the payment confirmation
        payment_reference = request.form.get('payment_reference')
        print(payment_reference)
        
        if not payment_reference:
            return jsonify({"success": False, "message": "No payment reference provided"}), 400

        # Verify the payment with Paystack
        is_verified, transaction_data = verify_paystack_transaction(payment_reference)
        
        if is_verified:
            # Check if the amount paid matches the course price
            amount_paid = transaction_data['amount'] / 100  # Paystack amount is in kobo
            if amount_paid != course.price:
                return jsonify({"success": False, "message": "Payment amount does not match course price"}), 400

            # Enroll user in the course
            enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()

            # Send enrollment email
            send_email(
                subject=f'Course Enrollment Confirmation: {course.title}',
                recipient=current_user.email,
                template='enrollment_email',
                user=current_user,
                course=course
            )

            return jsonify({
                "success": True, 
                "message": "Enrollment successful",
                "redirect_url": url_for('course', course_id=course_id)
            }), 200
        else:
            return jsonify({"success": False, "message": "Payment verification failed"}), 400

    # If it's a GET request, show the payment form
    return render_template('enroll.html', course=course, user=current_user)

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
    total_learning_hours = 0
    completed_courses_count = 0

    for course in courses:
        lessons = Lesson.query.filter_by(course_id=course.id).all()
        lessons_count[course.id] = len(lessons)
        
        # Count the number of completed lessons for this user in the course
        completed_lessons = Progress.query.filter_by(user_id=current_user.id).filter(Progress.lesson_id.in_([lesson.id for lesson in lessons])).all()
        completed_lessons_count[course.id] = len(completed_lessons)

        # Calculate total learning hours (assuming each lesson takes 1 hour)
        total_learning_hours += completed_lessons_count[course.id]

        # Check if the course is completed
        if completed_lessons_count[course.id] == lessons_count[course.id]:
            completed_courses_count += 1

    # Prepare completed lesson IDs for easier rendering
    completed_lessons_ids = {course.id: [progress.lesson_id for progress in completed_lessons] for course in courses}

    return render_template('student_dashboard.html', 
                           courses=courses, 
                           completed_lessons_count=completed_lessons_count, 
                           lessons_count=lessons_count, 
                           completed_lessons_ids=completed_lessons_ids,
                           total_learning_hours=total_learning_hours,
                           completed_courses_count=completed_courses_count)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            send_email(
                subject="Welcome to Raydex Hub!",
                recipient=email,
                template='welcome',
                username=username,
                current_year=datetime.now().year
            )
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration failed: {e}")
            flash('An error occurred. Please try again.', 'danger')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = generate_reset_token(user.email)
            
            # Send reset email
            reset_link = url_for('reset_password', token=token, _external=True)
            send_email(
                subject='Reset Your Raydex Hub Password',
                recipient=user.email,
                template='reset_password_email',
                username=user.username,
                reset_link=reset_link
            )
            
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'danger')
    
    return render_template('forgot_password.html')

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    email = verify_reset_token(token)
    if email is None:
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid reset token.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        
        # Send confirmation email
        send_email(
            subject='Your Raydex Hub Password Has Been Reset',
            recipient=user.email,
            template='password_changed_email',
            username=user.username
        )
        
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

# In utils.py
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except:
        return None

# Updated route for viewing a lesson
@app.route('/course/<int:course_id>/lesson/<int:lesson_id>', methods=['GET'])
@login_required
def lesson(course_id, lesson_id):
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('You must be enrolled in this course to access its lessons.', 'warning')
        return redirect(url_for('course', course_id=course_id))

    lesson = Lesson.query.get_or_404(lesson_id)
    
    if lesson.course_id != course_id:
        abort(404)

    lessons = Lesson.query.filter_by(course_id=course_id).all()
    progress = Progress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    completed = progress is not None

    current_lesson_index = lessons.index(lesson)
    next_lesson = lessons[current_lesson_index + 1] if current_lesson_index + 1 < len(lessons) else None

    # Fetch videos for this lesson, ordered by their order field
    videos = Video.query.filter_by(lesson_id=lesson.id).order_by(Video.order).all()

    # Get Cloudinary URLs for each video
    video_data = [
        {
            'title': video.title,
            'url': get_cloudinary_video_url(video.public_id)
        }
        for video in videos
    ]
    

    return render_template('lesson.html', lesson=lesson, next_lesson=next_lesson, completed=completed, videos=video_data)

@app.route('/code-playground', methods=['GET'])
@login_required
def code_playground():
    return render_template('code_playground.html')

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
        content = request.form['content']
        post = Post(content=content, author=current_user)
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

#Admin
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    courses = Course.query.all()
    users = User.query.all()
    return render_template('admin/dashboard.html', courses=courses, users=users)

@app.route('/admin/courses', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_courses():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        new_course = Course(title=title, description=description, price=price)
        
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                try:
                    image_filename = save_picture(image)
                    new_course.image = image_filename
                except Exception as e:
                    app.logger.error(f"Failed to save course image: {e}")
                    flash('Failed to save course image.', 'danger')
                    return redirect(url_for('admin_courses'))
        
        try:
            db.session.add(new_course)
            db.session.commit()
            flash('New course added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to add new course: {e}")
            flash('Failed to add new course.', 'danger')
        
        return redirect(url_for('admin_courses'))
    
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)


@app.route('/admin/course/<int:course_id>/students')
@login_required
def admin_course_students(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    students = [enrollment.user for enrollment in enrollments]
    return render_template('admin/course_students.html', course=course, students=students)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/enroll', methods=['POST'])
@login_required
def admin_enroll_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    course_id = request.form['course_id']
    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    flash(f'{user.username} has been enrolled in the course.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/progress')
@login_required
def admin_user_progress(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    enrollments = Enrollment.query.filter_by(user_id=user_id).all()
    progress = {}
    for enrollment in enrollments:
        course = enrollment.course
        lessons = Lesson.query.filter_by(course_id=course.id).all()
        completed_lessons = Progress.query.filter_by(user_id=user_id, lesson_id=Lesson.id).filter(Lesson.course_id == course.id).count()
        progress[course.id] = {
            'course': course,
            'completed': completed_lessons,
            'total': len(lessons)
        }
    return render_template('admin/user_progress.html', user=user, progress=progress)

@app.route('/admin/course/<int:course_id>/email', methods=['GET', 'POST'])
@login_required
def admin_email_course(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        recipients = [enrollment.user.email for enrollment in enrollments]
        
        msg = Message(subject, recipients=recipients)
        msg.body = body
        mail.send(msg)
        
        flash('Email sent to all enrolled students.', 'success')
        return redirect(url_for('admin_course_students', course_id=course_id))
    return render_template('admin/email_course.html', course=course)

@app.route('/admin/course/<int:course_id>/lessons', methods=['GET', 'POST'])
@login_required
def admin_lessons(course_id):
    if not current_user.is_admin:
        abort(403)
    course = Course.query.get_or_404(course_id)
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_lesson = Lesson(title=title, content=content, course_id=course_id)
        db.session.add(new_lesson)
        db.session.commit()
        
        # Handle multiple video submissions
        video_titles = request.form.getlist('video_title[]')
        video_files = request.files.getlist('video_file[]')
        for i, (v_title, v_file) in enumerate(zip(video_titles, video_files)):
            if v_title and v_file:
                public_id = upload_video_to_cloudinary(v_file)
                new_video = Video(title=v_title, public_id=public_id, order=i+1, lesson_id=new_lesson.id)
                db.session.add(new_video)
        
        # Handle quiz submission
        quiz_content = request.form.get('quiz')
        if quiz_content:
            new_quiz = Quiz(content=quiz_content, lesson_id=new_lesson.id)
            db.session.add(new_quiz)
        
        # Handle assignment submission
        assignment_content = request.form.get('assignment')
        if assignment_content:
            new_assignment = Assignment(content=assignment_content, lesson_id=new_lesson.id)
            db.session.add(new_assignment)
        
        db.session.commit()
        flash('New lesson added successfully!', 'success')
        return redirect(url_for('admin_lessons', course_id=course_id))
    
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    return render_template('admin/lessons.html', course=course, lessons=lessons)

@app.route('/admin/lesson/<int:lesson_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lesson(lesson_id):
    if not current_user.is_admin:
        abort(403)
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    if request.method == 'POST':
        lesson.title = request.form['title']
        lesson.content = request.form['content']
        
        # Handle video updates
        video_ids = request.form.getlist('video_id[]')
        video_titles = request.form.getlist('video_title[]')
        video_files = request.files.getlist('video_file[]')
        
        for v_id, v_title, v_file in zip(video_ids, video_titles, video_files):
            if v_id:  # Existing video
                video = Video.query.get(int(v_id))
                if video:
                    video.title = v_title
                    if v_file:
                        delete_video_from_cloudinary(video.public_id)
                        new_public_id = upload_video_to_cloudinary(v_file)
                        video.public_id = new_public_id
            elif v_title and v_file:  # New video
                new_public_id = upload_video_to_cloudinary(v_file)
                new_video = Video(title=v_title, public_id=new_public_id, lesson_id=lesson.id)
                db.session.add(new_video)
        
        # Handle quiz update
        quiz_content = request.form.get('quiz')
        if quiz_content:
            if lesson.quiz:
                lesson.quiz.content = quiz_content
            else:
                new_quiz = Quiz(content=quiz_content, lesson_id=lesson.id)
                db.session.add(new_quiz)
        
        # Handle assignment update
        assignment_content = request.form.get('assignment')
        if assignment_content:
            if lesson.assignment:
                lesson.assignment.content = assignment_content
            else:
                new_assignment = Assignment(content=assignment_content, lesson_id=lesson.id)
                db.session.add(new_assignment)
        
        db.session.commit()
        flash('Lesson updated successfully!', 'success')
        return redirect(url_for('admin_lessons', course_id=lesson.course_id))
    
    return render_template('admin/edit_lesson.html', lesson=lesson)

@app.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'{user.username} has been made an admin.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/account_settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        # Handle form submission
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not bcrypt.check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        else:
            current_user.password = bcrypt.generate_password_hash(new_password)
            db.session.commit()
            flash('Password updated successfully.', 'success')

    return render_template('account_settings.html')

@app.route('/faq')
def faq():
    faqs = [
        {"question": "How do I enroll in a course?", "answer": "To enroll in a course, navigate to the course page and click the 'Enroll' button. Follow the prompts to complete the enrollment process."},
        {"question": "Can I access course materials after completing a course?", "answer": "Yes, you will have lifetime access to all course materials after completion."},
        {"question": "How do I reset my password?", "answer": "You can reset your password by going to the Account Settings page and following the 'Change Password' instructions."},
        {"question": "Are there any prerequisites for courses?", "answer": "Prerequisites, if any, are listed on each course's description page."},
        {"question": "How can I contact support?", "answer": "You can contact our support team through the Help Center page or by emailing support@raydexhub.com."}
    ]
    return render_template('faq.html', faqs=faqs)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')


@app.route('/web')
def web_development():
    return render_template('webdevelopment.html')

# Route for machine learning page
@app.route('/ml')
def machine_learning():
    return render_template('machine_learning.html')

# Route for data science page
@app.route('/data')
def data_science():
    return render_template('data_science.html')

# Route for mobile development page
@app.route('/mobile')
def mobile_development():
    return render_template('mobile_development.html')

@app.route('/api/messages/read', methods=['POST'])
@login_required
def mark_messages_read():
    data = request.json
    sender_id = data.get('sender_id')
    ChatMessage.query.filter_by(sender_id=sender_id, recipient_id=current_user.id, read=False).update({'read': True})
    db.session.commit()
    return jsonify({'success': True})

@socketio.on('request_online_users')
def handle_online_users_request():
    online_users = [user.username for user in connected_users]
    emit('online_users_list', {'users': online_users})

# Keep track of connected users
connected_users = set()

@app.route('/course/<int:course_id>/chat')
@login_required
def course_chat(course_id):
    course = Course.query.get_or_404(course_id)
    messages = ChatMessage.query.filter_by(course_id=course_id).order_by(ChatMessage.timestamp.asc()).all()
    return render_template('course_chat.html', course=course, messages=messages)

@app.route('/chat/<int:user_id>')
@login_required
def private_chat(user_id):
    user = User.query.get_or_404(user_id)
    
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return render_template('private_chat.html', user=user, messages=messages)

@app.route('/api/users')
@login_required
def get_users():
    users = User.query.filter(User.id != current_user.id).all()
    return jsonify([{'id': user.id, 'username': user.username, 'email': user.email} for user in users])

@app.route('/api/courses')
@login_required
def get_courses():
    # Assuming the user is enrolled in these courses
    courses = Course.query.join(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    return jsonify([{'id': course.id, 'title': course.title} for course in courses])

@app.route('/chat/users')
@login_required
def chat_users():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('chat_users.html', users=users)

@socketio.on('join')
def on_join(data):
    username = current_user.username
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{username} has entered the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = current_user.username
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{username} has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    username = current_user.username
    room = data['room']
    message_type = data['type']
    content = data['msg']

    if message_type == 'course':
        course_id = int(room.split('_')[1])
        new_message = ChatMessage(content=content, sender_id=current_user.id, course_id=course_id)
        # Emit to all users in the course room
        emit('message', {'msg': content, 'username': username}, room=room)
        # Emit new_message event to all users in the course
        emit('new_message', {'sender': username, 'course_id': course_id}, room=room)
    elif message_type == 'private':
        recipient_id = data['recipient_id']
        recipient = User.query.get(recipient_id)
        new_message = ChatMessage(content=content, sender_id=current_user.id, recipient_id=recipient_id)
        # Emit to the private room
        emit('message', {'msg': content, 'username': username}, room=room)
        # Emit new_message event to the recipient
        emit('new_message', {'sender': username, 'recipient': recipient.username}, room=recipient.username)

    db.session.add(new_message)
    db.session.commit()

@socketio.on('connect')
def handle_connect():
    connected_users.add(current_user)
    join_room(current_user.username)  # Join a room named after the user's username
    emit('user_connected', {'username': current_user.username}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    connected_users.remove(current_user)
    emit('user_disconnected', {'username': current_user.username}, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    room = data['room']
    emit('typing', {'username': current_user.username}, room=room)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data['room']
    emit('stop_typing', {'username': current_user.username}, room=room)

# PWA Manifest
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# PWA Service Worker
@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('csrf_error.html', reason=e.description), 400

# Run the app
if __name__ == '__main__':
    socketio.run(app, debug=True)
