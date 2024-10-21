from app import db, Course, Lesson, User, Enrollment, Progress, app, Video, Quiz, Assignment
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()

    # Sample Users
    users_data = [
        {'username': 'john_doe', 'email': 'john@example.com', 'password': 'password'},
        {'username': 'jane_smith', 'email': 'jane@example.com', 'password': 'password123'},
        {'username': 'alice_wonder', 'email': 'alice@example.com', 'password': 'mypassword'},
        {'username': 'bob_builder', 'email': 'bob@example.com', 'password': 'builder123'},
    ]

    users = []
    for user_data in users_data:
        hashed_password = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
        user = User(username=user_data['username'], email=user_data['email'], password=hashed_password)
        users.append(user)

    db.session.bulk_save_objects(users)
    db.session.commit()

    # Sample Courses (keeping the same as provided)
    courses_data = [
        {
            'title': 'Python for Beginners',
            'description': 'A complete course to learn Python programming from scratch.',
            'price': 199.99,
            'image': 'python.jpeg'
        },
        {
            'title': 'Web Development with Flask',
            'description': 'Learn to build web applications with Flask, a lightweight Python web framework.',
            'price': 199.99,
            'image': 'web.jpeg'
        },
        {
            'title': 'Data Science with Python',
            'description': 'Unlock the power of data with Python for data science.',
            'price': 199.99,
            'image': 'html.png'
        },
        {
            'title': 'Machine Learning A-Z',
            'description': 'Become a machine learning expert with this comprehensive course.',
            'price': 199.99,
            'image': 'images.jpeg'
        }
    ]

    courses = []
    for course_data in courses_data:
        course = Course(**course_data)
        courses.append(course)

    db.session.bulk_save_objects(courses)
    db.session.commit()

    # Enhanced Lessons Data with Detailed Quizzes and Assignments
    lessons_data = [
        {
            'course_title': 'Python for Beginners',
            'lessons': [
                {
                    'title': 'Introduction to Python',
                    'content': 'In this lesson, you will learn about Python basics...',
                    'quiz_content': '''
                    <div class="quiz-container">
                        <h2>Python Basics Quiz</h2>
                        <form id="quiz-form">
                            <div class="question">
                                <p>1. What is the output of print(type(5))?</p>
                                <input type="radio" name="q1" value="a"> <label>a) &lt;class 'str'&gt;</label><br>
                                <input type="radio" name="q1" value="b"> <label>b) &lt;class 'int'&gt;</label><br>
                                <input type="radio" name="q1" value="c"> <label>c) &lt;class 'float'&gt;</label><br>
                                <input type="radio" name="q1" value="d"> <label>d) &lt;class 'number'&gt;</label>
                            </div>
                            <div class="question">
                                <p>2. Which of these is a valid variable name in Python?</p>
                                <input type="radio" name="q2" value="a"> <label>a) 2variable</label><br>
                                <input type="radio" name="q2" value="b"> <label>b) my-variable</label><br>
                                <input type="radio" name="q2" value="c"> <label>c) my_variable</label><br>
                                <input type="radio" name="q2" value="d"> <label>d) class</label>
                            </div>
                        </form>
                        <button onclick="checkAnswers()">Submit</button>
                    </div>
                    <script>
                        const correct_answers = {q1: 'b', q2: 'c'};
                        function checkAnswers() {
                            let score = 0;
                            for (let q in correct_answers) {
                                const selected = document.querySelector(`input[name="${q}"]:checked`);
                                if (selected && selected.value === correct_answers[q]) score++;
                            }
                            alert(`You scored ${score} out of ${Object.keys(correct_answers).length}`);
                        }
                    </script>
                    ''',
                    'assignment_content': '''
                    # Python Basic Calculator Assignment
                    
                    Create a simple calculator function that:
                    1. Takes two numbers and an operator (+, -, *, /) as input
                    2. Returns the result of the operation
                    3. Handles division by zero errors
                    4. Handles invalid operator errors
                    
                    Example template:
    
                    def calculator(num1, num2, operator):
                        # Your code here
                        pass
                    
                    # Test your function with these cases:
                    # calculator(10, 5, '+')  # Should return 15
                    # calculator(10, 5, '-')  # Should return 5
                    # calculator(10, 5, '*')  # Should return 50
                    # calculator(10, 5, '/')  # Should return 2.0
                    # calculator(10, 0, '/')  # Should handle division by zero
                    # calculator(10, 5, '%')  # Should handle invalid operator
                    ''',
                    'videos': [
                        {'title': 'Python Basics', 'public_id': 'videoplayback_gdgxec', 'order': 1},
                        {'title': 'Python Setup', 'public_id': 'videoplayback_gdgxec', 'order': 2}
                    ]
                },
                {
                    'title': 'Python Variables',
                    'content': 'In this lesson, you will learn about variables in Python...',
                    'quiz_content': '''
                    <div class="quiz-container">
                        <h2>Python Variables Quiz</h2>
                        <form id="quiz-form">
                            <div class="question">
                                <p>1. What is the value of x after: x = 5; x += 3?</p>
                                <input type="radio" name="q1" value="a"> <label>a) 5</label><br>
                                <input type="radio" name="q1" value="b"> <label>b) 3</label><br>
                                <input type="radio" name="q1" value="c"> <label>c) 8</label><br>
                                <input type="radio" name="q1" value="d"> <label>d) 53</label>
                            </div>
                        </form>
                        <button onclick="checkAnswers()">Submit</button>
                    </div>
                    <script>
                        const correct_answers = {q1: 'c'};
                        function checkAnswers() {
                            let score = 0;
                            for (let q in correct_answers) {
                                const selected = document.querySelector(`input[name="${q}"]:checked`);
                                if (selected && selected.value === correct_answers[q]) score++;
                            }
                            alert(`You scored ${score} out of ${Object.keys(correct_answers).length}`);
                        }
                    </script>
                    ''',
                    'assignment_content': '''
                    # Temperature Converter Assignment
                    
                    Create a temperature conversion program that:
                    1. Converts Celsius to Fahrenheit and vice versa
                    2. Takes temperature value and unit (C or F) as input
                    3. Returns the converted temperature with appropriate unit
                    
                    def convert_temperature(temp, unit):
                        # Your code here
                        pass
                    
                    # Test cases:
                    # convert_temperature(32, 'F')  # Should return "0°C"
                    # convert_temperature(0, 'C')   # Should return "32°F"
                    ''',
                    'videos': [
                        {'title': 'Understanding Variables', 'public_id': 'videoplayback_gdgxec', 'order': 1},
                        {'title': 'Variable Types', 'public_id': 'videoplayback_gdgxec', 'order': 2}
                    ]
                }
            ]
        },
        # Add similar detailed content for other courses...
    ]

    # Create lessons, quizzes, assignments, and videos
    for course_data in lessons_data:
        course = Course.query.filter_by(title=course_data['course_title']).first()
        for lesson_data in course_data['lessons']:
            # Create Lesson
            lesson = Lesson(
                title=lesson_data['title'],
                content=lesson_data['content'],
                course_id=course.id
            )
            db.session.add(lesson)
            db.session.flush()

            # Create Quiz
            quiz = Quiz(
                content=lesson_data['quiz_content'],
                lesson_id=lesson.id
            )
            db.session.add(quiz)

            # Create Assignment
            assignment = Assignment(
                content=lesson_data['assignment_content'],
                lesson_id=lesson.id
            )
            db.session.add(assignment)

            # Create Videos
            for video_data in lesson_data['videos']:
                video = Video(
                    title=video_data['title'],
                    public_id=video_data['public_id'],
                    order=video_data['order'],
                    lesson_id=lesson.id
                )
                db.session.add(video)

    db.session.commit()

    print("Database has been initialized with enhanced sample data!")