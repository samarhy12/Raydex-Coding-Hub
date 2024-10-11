from app import db, Course, Lesson, User, Enrollment, Progress, app
from flask_bcrypt import Bcrypt

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

    # Sample Lessons for Each Course
    lessons_data = [
        {
            'course_title': 'Python for Beginners',
            'lessons': [
                {'title': 'Introduction to Python', 'content': 'In this lesson, you will learn about Python basics...', 'video_url': 'https://example.com/video1', 'quiz': 'Quiz 1', 'assignment': 'Assignment 1'},
                {'title': 'Python Variables', 'content': 'In this lesson, you will learn about variables in Python...', 'video_url': 'https://example.com/video2', 'quiz': 'Quiz 2', 'assignment': 'Assignment 2'},
                {'title': 'Control Structures', 'content': 'Learn how to control the flow of your Python programs...', 'video_url': 'https://example.com/video3', 'quiz': 'Quiz 3', 'assignment': 'Assignment 3'},
                {'title': 'Functions in Python', 'content': 'Understand how to create and use functions in Python...', 'video_url': 'https://example.com/video4', 'quiz': 'Quiz 4', 'assignment': 'Assignment 4'},
            ]
        },
        {
            'course_title': 'Web Development with Flask',
            'lessons': [
                {'title': 'Introduction to Flask', 'content': 'In this lesson, you will learn about Flask basics...', 'video_url': 'https://example.com/video5', 'quiz': 'Quiz 5', 'assignment': 'Assignment 5'},
                {'title': 'Flask Routing', 'content': 'In this lesson, you will learn about routing in Flask...', 'video_url': 'https://example.com/video6', 'quiz': 'Quiz 6', 'assignment': 'Assignment 6'},
                {'title': 'Templates in Flask', 'content': 'Learn how to use templates to render HTML...', 'video_url': 'https://example.com/video7', 'quiz': 'Quiz 7', 'assignment': 'Assignment 7'},
                {'title': 'Forms in Flask', 'content': 'Understand how to handle forms in Flask applications...', 'video_url': 'https://example.com/video8', 'quiz': 'Quiz 8', 'assignment': 'Assignment 8'},
            ]
        },
        {
            'course_title': 'Data Science with Python',
            'lessons': [
                {'title': 'Introduction to Data Science', 'content': 'Explore what data science is and its applications...', 'video_url': 'https://example.com/video9', 'quiz': 'Quiz 9', 'assignment': 'Assignment 9'},
                {'title': 'Data Analysis with Pandas', 'content': 'Learn to manipulate data using the Pandas library...', 'video_url': 'https://example.com/video10', 'quiz': 'Quiz 10', 'assignment': 'Assignment 10'},
                {'title': 'Data Visualization with Matplotlib', 'content': 'Create visualizations to represent data...', 'video_url': 'https://example.com/video11', 'quiz': 'Quiz 11', 'assignment': 'Assignment 11'},
                {'title': 'Statistical Analysis', 'content': 'Understand basic statistics and its application in data analysis...', 'video_url': 'https://example.com/video12', 'quiz': 'Quiz 12', 'assignment': 'Assignment 12'},
            ]
        },
        {
            'course_title': 'Machine Learning A-Z',
            'lessons': [
                {'title': 'Introduction to Machine Learning', 'content': 'Learn what machine learning is and its types...', 'video_url': 'https://example.com/video13', 'quiz': 'Quiz 13', 'assignment': 'Assignment 13'},
                {'title': 'Data Preprocessing', 'content': 'Understand how to preprocess data for machine learning...', 'video_url': 'https://example.com/video14', 'quiz': 'Quiz 14', 'assignment': 'Assignment 14'},
                {'title': 'Building Models', 'content': 'Learn to build various machine learning models...', 'video_url': 'https://example.com/video15', 'quiz': 'Quiz 15', 'assignment': 'Assignment 15'},
                {'title': 'Model Evaluation', 'content': 'Explore how to evaluate and tune your models...', 'video_url': 'https://example.com/video16', 'quiz': 'Quiz 16', 'assignment': 'Assignment 16'},
            ]
        },
    ]

    for course_data in lessons_data:
        course = Course.query.filter_by(title=course_data['course_title']).first()
        for lesson in course_data['lessons']:
            lesson_instance = Lesson(
                title=lesson['title'],
                content=lesson['content'],
                video_url=lesson['video_url'],
                quiz=lesson['quiz'],
                assignment=lesson['assignment'],
                course_id=course.id
            )
            db.session.add(lesson_instance)

    db.session.commit()

  

    print("Database has been initialized with sample data!")
