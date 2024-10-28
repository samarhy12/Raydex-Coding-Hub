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
        {'username': 'Themma_target', 'email': 'agyareyraphael@example.com', 'password': '10836799'},
        {'username': 'targettt', 'email': 'rywagyarey@gmail.com', 'password': '10836799'},
    ]

    users = []
    for user_data in users_data:
        hashed_password = bcrypt.generate_password_hash(user_data['password']).decode('utf-8')
        user = User(username=user_data['username'], email=user_data['email'], password=hashed_password)
        users.append(user)

    db.session.bulk_save_objects(users)
    db.session.commit()

    # HTML, CSS, and JavaScript Course
    course_data = {
        'title': 'HTML, CSS, and JavaScript',
        'description': 'A complete guide to learning web development with HTML, CSS, and JavaScript.',
        'price': 199.99,
        'image': 'html.png'
    }

    course = Course(**course_data)
    db.session.add(course)
    db.session.commit()

    # Create 30 lessons for the HTML, CSS, and JavaScript course
    lessons_data = [
        {
            'title': f'Lesson {i+1}',
            'content': f'Content for Lesson {i+1} on HTML, CSS, and JavaScript...',
            'quiz_content': f'''
            <div class="quiz-container">
                <h2>Quiz for Lesson {i+1}</h2>
                <form id="quiz-form">
                    <div class="question">
                        <p>1. Sample question for Lesson {i+1}?</p>
                        <input type="radio" name="q1" value="a"> <label>a) Option A</label><br>
                        <input type="radio" name="q1" value="b"> <label>b) Option B</label><br>
                    </div>
                </form>
                <button onclick="checkAnswers()">Submit</button>
            </div>
            <script>
                const correct_answers = {{q1: 'a'}};
                function checkAnswers() {{
                    let score = 0;
                    for (let q in correct_answers) {{
                        const selected = document.querySelector(`input[name="${{q}}"]:checked`);
                        if (selected && selected.value === correct_answers[q]) score++;
                    }}
                    alert(`You scored ${{score}} out of 1`);
                }}
            </script>
            ''',
            'assignment_content': f'''
            # Assignment for Lesson {i+1}
            
            Write a simple HTML page that includes:
            1. A heading with "Lesson {i+1}".
            2. A paragraph describing what you learned in this lesson.
            3. Any additional content related to Lesson {i+1}.
            ''',
            'videos': [
                {'title': f'Video for Lesson {i+1}', 'public_id': 'Introduction_v2dk7a', 'order': i+1}
            ]
        } for i in range(30)
    ]

    for lesson_data in lessons_data:
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

        # Create Video
        for video_data in lesson_data['videos']:
            video = Video(
                title=video_data['title'],
                public_id=video_data['public_id'],
                order=video_data['order'],
                lesson_id=lesson.id
            )
            db.session.add(video)

    db.session.commit()

    print("Database has been initialized with the HTML, CSS, and JavaScript course and 30 lessons!")
