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
                'price': 49.99,
                'image': 'python.jpeg'
            },
            {
                'title': 'Web Development with Flask',
                'description': 'Learn to build web applications with Flask, a lightweight Python web framework.',
                'price': 79.99,
                'image': 'web.jpeg'
            },
            {
                'title': 'Data Science with Python',
                'description': 'Unlock the power of data with Python for data science.',
                'price': 99.99,
                'image': 'html.png'
            },
            {
                'title': 'Machine Learning A-Z',
                'description': 'Become a machine learning expert with this comprehensive course.',
                'price': 129.99,
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
                        {'title': 'Python Basics', 'public_id': 'sample_public_id_1'},
                        {'title': 'Python Setup', 'public_id': 'sample_public_id_2'}
                    ]},
                    {'title': 'Python Variables', 'content': 'In this lesson, you will learn about variables in Python...', 'quiz': 'Quiz 2', 'assignment': 'Assignment 2', 'videos': [
                        {'title': 'Understanding Variables', 'public_id': 'sample_public_id_3'},
                        {'title': 'Variable Types', 'public_id': 'sample_public_id_4'}
                    ]},
                    # ... other lessons ...
                ]
            },
            # ... other courses ...
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
