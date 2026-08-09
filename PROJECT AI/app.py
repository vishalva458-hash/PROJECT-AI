import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Resume, InterviewSession, QuestionAnswer
from services.resume_parser import process_resume, SKILL_TAXONOMY
from services.ai_engine import generate_questions, evaluate_answer

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create tables upon startup
with app.app_context():
    db.create_all()


# --- Custom Helper Functions ---
def get_user_skills(user):
    latest_resume = user.get_latest_resume()
    return latest_resume.skills if latest_resume else []


def calculate_dashboard_metrics(user):
    sessions = InterviewSession.query.filter_by(user_id=user.id, status='completed').order_by(InterviewSession.created_at.asc()).all()
    
    total_sessions = len(sessions)
    if total_sessions == 0:
        return {
            "total_sessions": 0,
            "avg_score": 0.0,
            "best_score": 0.0,
            "history_labels": [],
            "history_scores": [],
            "category_scores": {"Technical": 0, "Behavioral": 0, "System Design": 0, "Problem Solving": 0},
            "recommendations": ["Upload your PDF resume to extract skills.", "Take your first personalized AI interview!"]
        }
        
    scores = [s.total_score for s in sessions]
    avg_score = round(sum(scores) / len(scores), 1)
    best_score = round(max(scores), 1)
    
    history_labels = [s.created_at.strftime("%b %d, %H:%M") for s in sessions]
    history_scores = scores

    # Category score averages
    cat_totals = {"Technical": [], "Behavioral": [], "System Design": [], "Problem Solving": []}
    for session in sessions:
        for q in session.questions:
            if q.score is not None and q.category in cat_totals:
                cat_totals[q.category].append(q.score)
                
    category_scores = {}
    for cat, val_list in cat_totals.items():
        category_scores[cat] = round(sum(val_list) / len(val_list), 1) if val_list else 70.0

    # Skill Recommendations based on latest session & target role
    latest_skills = set(get_user_skills(user))
    recommendations = []
    
    if avg_score < 75:
        recommendations.append("Practice using the STAR method (Situation, Task, Action, Result) for behavioral & problem solving questions.")
    if category_scores.get("System Design", 0) < 70:
        recommendations.append("Review System Design fundamentals: Load balancing, caching, database indexing, and microservices trade-offs.")
    if category_scores.get("Technical", 0) < 75:
        recommendations.append("Deepen technical responses by explaining algorithmic complexity (Big-O) and boundary edge cases.")
    if "Docker" not in latest_skills and "Kubernetes" not in latest_skills:
        recommendations.append("Consider learning Containerization (Docker/Kubernetes) to boost DevOps & System Engineering competency.")
    if "System Design" not in latest_skills:
        recommendations.append("Include System Architecture and Cloud design experience in your resume skill profile.")

    if not recommendations:
        recommendations.append("Great overall performance! Keep taking mock sessions to polish speed and confidence under pressure.")

    return {
        "total_sessions": total_sessions,
        "avg_score": avg_score,
        "best_score": best_score,
        "history_labels": history_labels,
        "history_scores": history_scores,
        "category_scores": category_scores,
        "recommendations": recommendations[:4]
    }


# --- Routes ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Registration successful! Welcome to AI Interview Prep.', 'success')
        return redirect(url_for('resume_page'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not new_password:
            flash('Please enter your account email and new password.', 'danger')
            return redirect(url_for('reset_password'))

        if new_password != confirm_password:
            flash('Passwords do not match. Please verify both password fields.', 'danger')
            return redirect(url_for('reset_password'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with this email address.', 'danger')
            return redirect(url_for('reset_password'))

        user.set_password(new_password)
        db.session.commit()

        flash('Your password has been successfully reset! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html')


# --- Resume & Skill Management ---

@app.route('/resume', methods=['GET'])
@login_required
def resume_page():
    resume = current_user.get_latest_resume()
    skills = resume.skills if resume else []
    return render_template('resume.html', resume=resume, skills=skills)


@app.route('/resume/upload', methods=['POST'])
@login_required
def upload_resume():
    if 'resume_file' not in request.files:
        flash('No file attached. Please select a PDF resume.', 'danger')
        return redirect(url_for('resume_page'))

    file = request.files['resume_file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('resume_page'))

    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process Resume PDF
        try:
            parsed_data = process_resume(filepath)
            
            # Save or Update Resume model
            resume = Resume(
                user_id=current_user.id,
                filename=file.filename,
                filepath=filepath,
                extracted_text=parsed_data['text'],
                skills=parsed_data['skills']
            )
            db.session.add(resume)
            db.session.commit()

            skill_count = len(parsed_data['skills'])
            flash(f'Resume successfully parsed! {skill_count} skills extracted.', 'success')
        except Exception as e:
            flash(f'Error reading PDF: {str(e)}', 'danger')

        return redirect(url_for('resume_page'))
    else:
        flash('Invalid file format. Only PDF files are supported.', 'danger')
        return redirect(url_for('resume_page'))


@app.route('/resume/skills/add', methods=['POST'])
@login_required
def add_skill():
    new_skill = request.form.get('skill', '').strip()
    resume = current_user.get_latest_resume()

    if not new_skill:
        flash('Skill name cannot be empty.', 'warning')
        return redirect(url_for('resume_page'))

    if not resume:
        # Create dummy placeholder resume for custom user skills
        resume = Resume(user_id=current_user.id, filename="Custom Profile", filepath="", extracted_text="", skills=[])
        db.session.add(resume)

    current_skills = resume.skills
    if any(s.lower() == new_skill.lower() for s in current_skills):
        flash(f'Skill "{new_skill}" is already in your profile.', 'info')
    else:
        current_skills.append(new_skill)
        resume.skills = current_skills
        db.session.commit()
        flash(f'Skill "{new_skill}" added to profile.', 'success')

    return redirect(url_for('resume_page'))


@app.route('/resume/skills/remove', methods=['POST'])
@login_required
def remove_skill():
    skill_to_remove = request.form.get('skill', '').strip()
    resume = current_user.get_latest_resume()

    if resume and skill_to_remove:
        current_skills = [s for s in resume.skills if s.lower() != skill_to_remove.lower()]
        resume.skills = current_skills
        db.session.commit()
        flash(f'Skill "{skill_to_remove}" removed.', 'info')

    return redirect(url_for('resume_page'))


# --- Interview Setup & Session ---

@app.route('/interview/setup', methods=['GET'])
@login_required
def interview_setup():
    resume = current_user.get_latest_resume()
    skills = resume.skills if resume else []
    
    available_roles = [
        "Python Backend Engineer",
        "Full Stack Developer",
        "Data Scientist / AI Engineer",
        "DevOps / Cloud Engineer",
        "Software Engineer (General)",
        "Frontend React Developer",
        "System Architect"
    ]
    return render_template('interview/setup.html', skills=skills, roles=available_roles)


@app.route('/interview/start', methods=['POST'])
@login_required
def start_interview():
    target_role = request.form.get('target_role', 'Software Engineer (General)').strip()
    experience_level = request.form.get('experience_level', 'Mid Level').strip()

    resume = current_user.get_latest_resume()
    skills = resume.skills if resume else []

    # Create new Interview Session
    session = InterviewSession(
        user_id=current_user.id,
        target_role=target_role,
        experience_level=experience_level,
        status='in_progress'
    )
    db.session.add(session)
    db.session.commit()

    # Generate 5 personalized questions
    generated_q_data = generate_questions(skills, target_role, experience_level, count=5)

    for i, q in enumerate(generated_q_data, start=1):
        qa = QuestionAnswer(
            session_id=session.id,
            question_num=i,
            question_text=q['question'],
            category=q.get('category', 'Technical')
        )
        db.session.add(qa)

    db.session.commit()
    return redirect(url_for('interview_session', session_id=session.id))


@app.route('/interview/<int:session_id>', methods=['GET'])
@login_required
def interview_session(session_id):
    session = InterviewSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    
    # Find current unanswered question
    questions = session.questions
    current_q = None
    for q in questions:
        if q.user_answer is None:
            current_q = q
            break

    if not current_q:
        # All questions answered! Mark as completed & compute total score
        session.status = 'completed'
        session.calculate_overall_score()
        db.session.commit()
        return redirect(url_for('interview_results', session_id=session.id))

    progress_percent = int(((current_q.question_num - 1) / len(questions)) * 100)

    return render_template(
        'interview/session.html', 
        session=session, 
        current_q=current_q, 
        total_q=len(questions),
        progress_percent=progress_percent
    )


@app.route('/interview/<int:session_id>/submit', methods=['POST'])
@login_required
def submit_answer(session_id):
    session = InterviewSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    question_num = request.form.get('question_num', type=int)
    user_answer = request.form.get('user_answer', '').strip()

    qa = QuestionAnswer.query.filter_by(session_id=session.id, question_num=question_num).first_or_404()

    resume = current_user.get_latest_resume()
    skills = resume.skills if resume else []

    # Evaluate answer using AI engine
    eval_result = evaluate_answer(
        question_text=qa.question_text,
        category=qa.category,
        user_answer=user_answer,
        skills=skills,
        target_role=session.target_role
    )

    qa.user_answer = user_answer
    qa.score = eval_result['score']
    qa.feedback = eval_result['feedback']
    qa.strengths = eval_result['strengths']
    qa.improvements = eval_result['improvements']
    qa.sample_answer = eval_result['sample_answer']
    qa.answered_at = datetime.utcnow()

    db.session.commit()

    return redirect(url_for('interview_session', session_id=session.id))


@app.route('/interview/<int:session_id>/results', methods=['GET'])
@login_required
def interview_results(session_id):
    session = InterviewSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    
    if session.status != 'completed':
        session.calculate_overall_score()
        session.status = 'completed'
        db.session.commit()

    return render_template('interview/results.html', session=session)


# --- Dashboard & Progress Analytics ---

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    resume = current_user.get_latest_resume()
    skills = resume.skills if resume else []
    metrics = calculate_dashboard_metrics(current_user)

    recent_sessions = InterviewSession.query.filter_by(user_id=current_user.id).order_by(InterviewSession.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        skills=skills,
        metrics=metrics,
        recent_sessions=recent_sessions
    )


# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# --- Health check ---
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "user": current_user.username if current_user.is_authenticated else None})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
