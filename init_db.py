from app import db, Course, Lesson, User, Enrollment, Progress, app, Video
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

    # Sample Courses
    courses_data = [
        {
            'title': 'Python for Beginners',
            'description': 'A complete course to learn Python programming from scratch.',
            'price': 149.99,
            'image': 'python.jpeg'
        },
        {
            'title': 'Web Development with Flask',
            'description': 'Learn to build web applications with Flask, a lightweight Python web framework.',
            'price': 149.99,
            'image': 'web.jpeg'
        },
        {
            'title': 'Data Science with Python',
            'description': 'Unlock the power of data with Python for data science.',
            'price': 149.99,
            'image': 'html.png'
        },
        {
            'title': 'Machine Learning A-Z',
            'description': 'Become a machine learning expert with this comprehensive course.',
            'price': 149.99,
            'image': 'images.jpeg'
        },
    ]

    courses = []
    for course_data in courses_data:
        course = Course(title=course_data['title'], 
                        description=course_data['description'], 
                        price=course_data['price'], 
                        image=course_data['image'])
        courses.append(course)

    db.session.bulk_save_objects(courses)
    db.session.commit()

    # Sample Lessons and Videos for Each Course
    lessons_data = [
        {
            'course_title': 'Python for Beginners',
            'lessons': [
                {'title': 'Introduction to Python', 'content': 'In this lesson, you will learn about Python basics...', 'quiz': 'Quiz 1', 'assignment': 'Assignment 1', 'videos': [
                    {'title': 'Python Basics', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Python Setup', 'public_id': 'videoplayback_gdgxec'}
                ]},
                {'title': 'Python Variables', 'content': 'In this lesson, you will learn about variables in Python...', 'quiz': 'Quiz 2', 'assignment': 'Assignment 2', 'videos': [
                    {'title': 'Understanding Variables', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Variable Types', 'public_id': 'videoplayback_gdgxec'}
                ]},
                {'title': 'Python Control Flow', 'content': 'Learn about if-else statements and loops...', 'quiz': 'Quiz 3', 'assignment': 'Assignment 3', 'videos': [
                    {'title': 'If-Else in Python', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Loops in Python', 'public_id': 'videoplayback_gdgxec'}
                ]},
                {'title': 'Functions in Python', 'content': 'Understand functions and how to define them...', 'quiz': 'Quiz 4', 'assignment': 'Assignment 4', 'videos': [
                    {'title': 'Defining Functions', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Function Parameters', 'public_id': 'videoplayback_gdgxec'}
                ]}
            ]
        },
        {
            'course_title': 'Web Development with Flask',
            'lessons': [
                {'title': 'Introduction to Flask', 'content': 'In this lesson, you will learn about Flask basics...', 'quiz': 'Quiz 1', 'assignment': 'Assignment 1', 'videos': [
                    {'title': 'Flask Basics', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Flask Setup', 'public_id': 'videoplayback_gdgxec'}
                ]},
                {'title': 'Routing in Flask', 'content': 'Learn about routing and URL handling...', 'quiz': 'Quiz 2', 'assignment': 'Assignment 2', 'videos': [
                    {'title': 'Flask Routing', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Dynamic URLs', 'public_id': 'videoplayback_gdgxec'}
                ]},
                {'title': 'Flask Templates', 'content': 'Work with Jinja templates to render dynamic content...', 'quiz': 'Quiz 3', 'assignment': 'Assignment 3', 'videos': [
                    {'title': 'Jinja Basics', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Template Inheritance', 'public_id': 'videoplayback_gdgxec'}
                ]}
            ]
        },
        {
            'course_title': 'Data Science with Python',
            'lessons': [
                {'title': 'Introduction to Data Science', 'content': 'In this lesson, you will learn what data science is...', 'quiz': 'Quiz 1', 'assignment': 'Assignment 1', 'videos': [
                    {'title': 'What is Data Science?', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Data Science Tools', 'public_id': 'videoplayback_gdgxec'}
                ]},
                {'title': 'Data Wrangling', 'content': 'Learn how to clean and organize data...', 'quiz': 'Quiz 2', 'assignment': 'Assignment 2', 'videos': [
                    {'title': 'Pandas Basics', 'public_id': 'videoplayback_gdgxec'},
                    {'title': 'Data Cleaning Techniques', 'public_id': 'videoplayback_gdgxec'}
                ]}
            ]
        },
        {
            'course_title': 'Machine Learning A-Z',
            'lessons': [
                {'title': 'Introduction to Machine Learning', 'content': 'In this lesson, you will learn the basics of machine learning...', 'quiz': 'Quiz 1', 'assignment': 'Assignment 1', 'videos': [
                    {'title': 'Machine Learning Basics', 'public_id': 'ml_basics_id'},
                    {'title': 'Types of Machine Learning', 'public_id': 'ml_types_id'}
                ]},
                {'title': 'Supervised Learning', 'content': 'Learn about supervised learning techniques...', 'quiz': 'Quiz 2', 'assignment': 'Assignment 2', 'videos': [
                    {'title': 'Linear Regression', 'public_id': 'linear_regression_id'},
                    {'title': 'Classification Algorithms', 'public_id': 'classification_algorithms_id'}
                ]}
            ]
        }
    ]

    for course_data in lessons_data:
        course = Course.query.filter_by(title=course_data['course_title']).first()
        for lesson_data in course_data['lessons']:
            lesson = Lesson(
                title=lesson_data['title'],
                content=lesson_data['content'],
                quiz=lesson_data['quiz'],
                assignment=lesson_data['assignment'],
                course_id=course.id
            )
            db.session.add(lesson)
            db.session.flush()  # This will assign an ID to the lesson

            for i, video_data in enumerate(lesson_data['videos'], start=1):
                video = Video(
                    title=video_data['title'],
                    public_id=video_data['public_id'],
                    order=i,
                    lesson_id=lesson.id
                )
                db.session.add(video)

    db.session.commit()

    print("Database has been initialized with sample data!")
