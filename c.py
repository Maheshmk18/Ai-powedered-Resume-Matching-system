from flask import (
    Flask, 
    render_template, 
    render_template_string,  # Added this import
    request, 
    redirect, 
    url_for, 
    session, 
    flash, 
    jsonify, 
    send_from_directory
)
import sqlite3
from werkzeug.utils import secure_filename
import os
import PyPDF2
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
# Replace your existing init_db() function with this one
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        role_name TEXT NOT NULL,
        description TEXT NOT NULL,
        qualifications TEXT NOT NULL,
        experience TEXT NOT NULL,
        location TEXT,
        posted_by INTEGER,
        FOREIGN KEY (posted_by) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        resume_text TEXT NOT NULL,
        skills TEXT,
        education TEXT,
        experience TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        match_percentage INTEGER,
        status TEXT DEFAULT 'pending',
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Add these configurations after app initialization
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
def analyze_resume(filepath):
    """Analyze resume and extract information"""
    text = extract_text_from_file(filepath)

    # Extract basic information
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    # Store the full text for matching
    resume_text = text

    return {
        'skills': skills,
        'education': education,
        'experience': experience,
        'full_text': resume_text
    }

def extract_text_from_file(filepath):
    """Extract text from PDF file"""
    text = ""
    try:
        if filepath.endswith('.pdf'):
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text

def extract_skills(text):
    # ... existing code ...
    
    # Comprehensive skill sets
    technical_skills = {
        # Programming Languages
        'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'golang',
        # Web Technologies
        'html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'django', 'flask', 'spring boot',
        'express.js', 'bootstrap', 'jquery', 'rest api', 'graphql',
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'elasticsearch', 'firebase',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'ci/cd', 'terraform',
        # AI/ML
        'machine learning', 'deep learning', 'neural networks', 'nlp', 'computer vision',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        # Data Science
        'data analysis', 'data visualization', 'statistics', 'r', 'tableau', 'power bi',
        # Mobile Development
        'android', 'ios', 'react native', 'flutter', 'xamarin',
    }
    
    soft_skills = {
        'leadership', 'communication', 'teamwork', 'problem solving', 'time management',
        'project management', 'critical thinking', 'decision making', 'organizational',
        'analytical', 'creativity', 'interpersonal', 'adaptability', 'flexibility',
        'presentation', 'collaboration', 'negotiation', 'conflict resolution'
    }
    
    tools = {
        'jira', 'confluence', 'slack', 'trello', 'asana', 'photoshop', 'illustrator',
        'figma', 'sketch', 'adobe xd', 'visual studio', 'intellij', 'eclipse',
        'postman', 'swagger', 'microsoft office', 'excel', 'powerpoint', 'word'
    }
    
    # Combine all skills
    all_skills = technical_skills.union(soft_skills).union(tools)
    
    # Convert text to lowercase for better matching
    text_lower = text.lower()
    
    # Initialize found skills set
    found_skills = set()
    
    # Extract single-word skills
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in all_skills:
            found_skills.add(word)
    
    # Extract multi-word skills
    for skill in all_skills:
        if ' ' in skill and skill in text_lower:
            found_skills.add(skill)
    
    # Look for common abbreviations
    abbreviations = {
        'ai': 'artificial intelligence',
        'ml': 'machine learning',
        'dl': 'deep learning',
        'nlp': 'natural language processing',
        'oop': 'object oriented programming',
        'ui': 'user interface',
        'ux': 'user experience',
        'api': 'application programming interface',
        'saas': 'software as a service',
        'db': 'database'
    }
    
    for abbr, full_form in abbreviations.items():
        if re.search(r'\b' + abbr + r'\b', text_lower, re.IGNORECASE):
            found_skills.add(full_form)
    
    # Look for version-specific skills (e.g., Python 3, Java 8)
    version_patterns = [
        (r'python\s*[23]\b', 'python'),
        (r'java\s*[8-9]\b', 'java'),
        (r'angular\s*[2-9]\b', 'angular'),
    ]
    
    for pattern, skill in version_patterns:
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    return list(found_skills)
    common_skills = {
        'python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'angular',
        'node.js', 'docker', 'kubernetes', 'aws', 'azure', 'machine learning',
        'data analysis', 'project management', 'agile', 'scrum', 'leadership',
        'communication', 'problem solving', 'teamwork', 'git', 'devops'
    }

    extracted_skills = set()
    text_lower = text.lower()

    for skill in common_skills:
        if skill in text_lower:
            extracted_skills.add(skill.title())

    return list(extracted_skills)

def extract_education(text):
    education_patterns = [
        r'(?i)(?:B\.?Tech|Bachelor of Technology)',
        r'(?i)(?:M\.?Tech|Master of Technology)',
        r'(?i)(?:B\.?E|Bachelor of Engineering)',
        r'(?i)(?:M\.?S|Master of Science)',
        r'(?i)(?:B\.?Sc|Bachelor of Science)',
        r'(?i)(?:Ph\.?D|Doctor of Philosophy)',
        r'(?i)(?:MBA|Master of Business Administration)'
    ]

    education = []
    for pattern in education_patterns:
        matches = re.findall(pattern, text)
        education.extend(matches)

    return list(set(education))

def extract_experience(text):
    # Simple extraction of years of experience
    experience_patterns = [
        r'(\d+)\+?\s+years?\s+(?:of\s+)?experience',
        r'experience\s+(?:of\s+)?(\d+)\+?\s+years?'
    ]

    for pattern in experience_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1) + " years"

    return "Not specified"

def calculate_match_percentage(resume_text, job_description):
    """Calculate match percentage between resume and job description"""
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # Consider both single words and pairs of words
        max_features=5000,    # Increase vocabulary size
        analyzer='word'
    )
    
    # Extract skills from both resume and job description
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)
    
    # Calculate skills match
    if job_skills:
        skills_match = len(set(resume_skills) & set(job_skills)) / len(job_skills) * 100
    else:
        skills_match = 0
        
    # Calculate text similarity using TF-IDF
    try:
        documents = [resume_text, job_description]
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
    except:
        similarity = 0
        
    # Extract experience from both documents
    resume_experience = extract_experience(resume_text)
    required_experience = extract_experience(job_description)
    
    # Calculate experience match
    experience_match = 100 if resume_experience >= required_experience else (resume_experience / required_experience * 100 if required_experience > 0 else 100)
    
    # Calculate weighted average
    final_match = (
        skills_match * 0.4 +      # Skills are important
        similarity * 0.4 +        # Overall content similarity
        experience_match * 0.2    # Experience requirements
    )
    
    return round(final_match, 2)

def get_user_id(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return user[0]
    return None
# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML Templates
home_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        @keyframes slideInLeft {
            from { transform: translateX(-100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        @keyframes rotateIn {
            from { transform: rotate(-180deg); opacity: 0; }
            to { transform: rotate(0); opacity: 1; }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }

        nav {
            display: flex;
            justify-content: space-between;
            padding: 20px 40px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            box-sizing: border-box;
        }

        .nav-links {
            display: flex;
            gap: 20px;
        }

        .nav-button {
            color: #fff;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .nav-button:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        .nav-button.primary {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            border: none;
        }

        .nav-button.primary:hover {
            background: linear-gradient(45deg, #00ff9d, #00d4ff);
        }

        .hero {
            text-align: center;
            padding: 180px 20px 100px;
            animation: fadeIn 1s ease-out;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(5px);
        }

        .hero h1 {
            font-size: 4.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            animation: float 6s ease-in-out infinite;
        }

        .hero p {
            font-size: 1.5rem;
            margin-bottom: 40px;
            opacity: 0;
            animation: fadeIn 1s ease-out forwards;
            animation-delay: 0.5s;
        }

        .hero .btn {
            padding: 15px 40px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            display: inline-block;
            opacity: 0;
            animation: fadeIn 1s ease-out forwards;
            animation-delay: 1s;
            position: relative;
            overflow: hidden;
        }

        .hero .btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .hero .btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        section {
            padding: 80px 20px;
            text-align: center;
            background: rgba(0, 0, 0, 0.7);
            margin: 20px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            opacity: 0;
            animation: fadeIn 1s ease-out forwards;
        }

        section h2 {
            font-size: 2.5rem;
            margin-bottom: 40px;
            color: #fff;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        ul, ol {
            list-style: none;
            padding: 0;
            max-width: 800px;
            margin: 0 auto;
        }

        li {
            margin: 20px 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            transition: transform 0.3s ease;
            cursor: pointer;
        }

        li:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.2);
        }

        .title-highlight {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            font-weight: bold;
            display: inline-block;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 20px;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .feature-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
        }

        @media (max-width: 768px) {
            .hero h1 {
                font-size: 3rem;
            }
            
            nav {
                padding: 15px 20px;
            }
            
            .nav-links {
                gap: 10px;
            }
            
            .nav-button {
                padding: 8px 15px;
                font-size: 0.9rem;
            }
            
            section {
                margin: 10px;
                padding: 40px 15px;
            }
        }

        .cta-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 30px;
        }

        .cta-btn {
            padding: 15px 30px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            text-decoration: none;
            border-radius: 30px;
            font-weight: bold;
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
        }

        .cta-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .testimonials {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            padding: 20px;
        }

        .testimonial-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            animation: fadeIn 0.5s ease-out forwards;
        }

        .testimonial-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.2);
        }

        .why-us-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            padding: 20px;
        }

        .why-us-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 25px;
            border-radius: 15px;
            transition: all 0.3s ease;
            animation: slideInRight 0.5s ease-out forwards;
        }

        .why-us-card:hover {
            transform: translateY(-5px) scale(1.02);
            background: rgba(255, 255, 255, 0.2);
        }

        .process-steps {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            padding: 20px;
        }

        .process-step {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            transition: all 0.3s ease;
            animation: rotateIn 0.5s ease-out forwards;
        }

        .process-step:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <nav>
        <div class="nav-links">
            <a href="/" class="nav-button">Home</a>
            <a href="#features" class="nav-button">Features</a>
            <a href="#workflow" class="nav-button">How It Works</a>
        </div>
        <div class="nav-links">
            <a href="/login" class="nav-button">Login</a>
            <a href="/register" class="nav-button primary">Register</a>
        </div>
    </nav>
    <div class="hero">
        <h1><span class="title-highlight">CareerSync AI</span></h1>
        <p>Your Gateway to Smarter Job Matching</p>
        <p class="subtitle">Empowering job seekers and recruiters with AI-driven solutions for a smarter, fairer, and more sustainable future.</p>
        <div class="cta-buttons">
            <a href="/register?type=seeker" class="cta-btn">Find Your Dream Job</a>
            <a href="/register?type=recruiter" class="cta-btn">Hire the Best Talent</a>
        </div>
    </div>
    <section id="features">
        <h2>Key Features</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <h3>Smart Matching</h3>
                <p>AI-driven skill mapping and predictive career paths using cutting-edge algorithms.</p>
            </div>
            <div class="feature-card">
                <h3>Sustainability Focus</h3>
                <p>Green job integration and environmental impact tracking for conscious careers.</p>
            </div>
            <div class="feature-card">
                <h3>Inclusive Hiring</h3>
                <p>Bias-free algorithms and diversity promotion for equal opportunities.</p>
            </div>
        </div>
    </section>
    <section id="workflow">
        <h2>How It Works</h2>
        <ol>
            <li>
                <h3>Upload Your Profile</h3>
                <p>Share your resume or job description with our AI system</p>
            </li>
            <li>
                <h3>AI Analysis</h3>
                <p>Our advanced AI analyzes skills, experience, and qualifications in real-time</p>
            </li>
            <li>
                <h3>Smart Recommendations</h3>
                <p>Get personalized job matches or ranked candidate shortlists</p>
            </li>
            <li>
                <h3>Growth Planning</h3>
                <p>Identify skill gaps and receive tailored upskilling suggestions</p>
            </li>
        </ol>
    </section>
    <section id="why-us">
        <h2>Why Choose CareerSync AI?</h2>
        <div class="why-us-grid">
            <div class="why-us-card">
                <h3>For Job Seekers</h3>
                <ul>
                    <li>Personalized job recommendations</li>
                    <li>Skill gap analysis</li>
                    <li>Access to green job opportunities</li>
                </ul>
            </div>
            <div class="why-us-card">
                <h3>For Recruiters</h3>
                <ul>
                    <li>AI-powered candidate shortlisting</li>
                    <li>Automated resume parsing</li>
                    <li>Bias-free hiring algorithms</li>
                </ul>
            </div>
        </div>
    </section>
    <section id="how-it-works">
        <h2>How CareerSync AI Works</h2>
        <div class="process-steps">
            <div class="process-step">
                <h3>1. Upload</h3>
                <p>Upload your resume or job description</p>
            </div>
            <div class="process-step">
                <h3>2. Analyze</h3>
                <p>AI analyzes skills and qualifications</p>
            </div>
            <div class="process-step">
                <h3>3. Match</h3>
                <p>Get personalized recommendations</p>
            </div>
            <div class="process-step">
                <h3>4. Grow</h3>
                <p>Access upskilling opportunities</p>
            </div>
        </div>
    </section>
    <section id="testimonials">
        <h2>What Our Users Say</h2>
        <div class="testimonials">
            <div class="testimonial-card">
                <p>"CareerSync AI helped me find my dream job in just a week! The recommendations were spot on."</p>
                <h4>- Sarah Johnson</h4>
                <p class="role">Software Engineer</p>
            </div>
            <div class="testimonial-card">
                <p>"As a recruiter, I saved hours of manual screening. The AI shortlists are incredibly accurate."</p>
                <h4>- Michael Chen</h4>
                <p class="role">HR Manager</p>
            </div>
        </div>
    </section>
    <section id="join-us">
        <h2>Ready to Get Started?</h2>
        <p>Whether you're looking for your next big opportunity or the perfect candidate, CareerSync AI is here to help.</p>
        <a href="/register" class="cta-btn">Sign Up Now</a>
    </section>
</body>
</html>
"""
# Add these new HTML templates

job_seeker_dashboard = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Seeker Dashboard - CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        @keyframes slideInLeft {
            from { transform: translateX(-100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }

        .container {
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 250px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            padding: 100px 0 20px 0;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideInLeft 0.5s ease-out;
        }

        .sidebar-logo {
            padding: 0 20px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 30px;
            text-align: center;
        }

        .sidebar-logo img {
            max-width: 150px;
            filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
        }

        .sidebar-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .sidebar-menu li {
            padding: 12px 25px;
            margin: 5px 15px;
            cursor: pointer;
            display: flex;
            align-items: center;
            transition: all 0.3s;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.1);
        }

        .sidebar-menu li:hover, .sidebar-menu li.active {
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 157, 0.2));
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        .sidebar-menu li.active {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
        }

        .sidebar-menu li i {
            margin-right: 10px;
            width: 20px;
            text-align: center;
        }

        .main-content {
            flex: 1;
            padding: 100px 20px 20px;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(5px);
            animation: fadeIn 0.8s ease-out;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 1s ease-out;
        }

        .search-bar {
            flex: 1;
            max-width: 500px;
            position: relative;
        }

        .search-bar input {
            width: 100%;
            padding: 12px 20px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 14px;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            transition: all 0.3s;
        }

        .search-bar input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.2);
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
        }

        .search-bar input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }

        .user-profile {
            display: flex;
            align-items: center;
        }

        .user-profile img {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 15px;
            border: 2px solid #00d4ff;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }

        .job-filters {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 30px;
            animation: fadeIn 1.2s ease-out;
        }

        .filter-pill {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            font-size: 14px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transition: all 0.3s;
        }

        .filter-pill:hover, .filter-pill.active {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border-color: transparent;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        .job-list {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .job-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            transition: all 0.3s;
            animation: fadeIn 0.5s ease-out forwards;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .job-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            border-color: rgba(255, 255, 255, 0.3);
        }

        .job-logo {
            width: 70px;
            height: 70px;
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 157, 0.2));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: pulse 4s infinite;
        }

        .job-logo img {
            max-width: 45px;
            max-height: 45px;
            filter: brightness(0) invert(1);
        }

        .job-info {
            flex: 1;
        }

        .job-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #fff;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .job-company {
            font-size: 15px;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 15px;
        }

        .job-details {
            display: flex;
            gap: 20px;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 20px;
        }

        .job-details span {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .job-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .match-indicator {
            display: flex;
            align-items: center;
        }

        .match-percentage {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            margin-right: 15px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }

        .high-match {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
        }

        .medium-match {
            background: linear-gradient(45deg, #ffd166, #ff9f1c);
            box-shadow: 0 0 15px rgba(255, 209, 102, 0.5);
        }

        .low-match {
            background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
            box-shadow: 0 0 15px rgba(255, 107, 107, 0.5);
        }

        .match-text {
            font-size: 14px;
            font-weight: 600;
        }

        .apply-btn {
            padding: 10px 25px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            position: relative;
            overflow: hidden;
        }

        .apply-btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .apply-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        .resume-upload {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.8s ease-out;
        }

        .resume-upload h2 {
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 22px;
            color: #fff;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .upload-btn {
            display: inline-block;
            padding: 12px 25px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
            position: relative;
            overflow: hidden;
        }

        .upload-btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .upload-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        .file-input {
            display: none;
        }

        .resume-status {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            font-size: 14px;
        }

        .skills-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }

        .skill-tag {
            padding: 6px 12px;
            background: rgba(0, 212, 255, 0.2);
            color: #fff;
            border-radius: 20px;
            font-size: 13px;
            border: 1px solid rgba(0, 212, 255, 0.3);
            transition: all 0.3s;
        }

        .skill-tag:hover {
            background: rgba(0, 212, 255, 0.4);
            transform: translateY(-2px);
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            animation: fadeIn 0.3s ease-out;
        }

        .modal-content {
            background: rgba(10, 10, 10, 0.9);
            margin: 5% auto;
            padding: 30px;
            border-radius: 20px;
            width: 70%;
            max-width: 800px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
            animation: fadeIn 0.5s ease-out;
        }

        .close-btn {
            color: rgba(255, 255, 255, 0.6);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }

        .close-btn:hover {
            color: #fff;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }

        .job-detail-header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
        }

        .job-detail-logo {
            width: 90px;
            height: 90px;
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 157, 0.2));
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 25px;
            animation: pulse 4s infinite;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .job-detail-logo img {
            max-width: 60px;
            max-height: 60px;
            filter: brightness(0) invert(1);
        }

        .job-detail-info h2 {
            margin: 0 0 10px 0;
            font-size: 26px;
            color: #fff;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .job-detail-company {
            font-size: 16px;
            color: rgba(255, 255, 255, 0.8);
        }

        .job-detail-section {
            margin-bottom: 30px;
        }

        .job-detail-section h3 {
            margin-top: 0;
            font-size: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 12px;
            color: #fff;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        .job-detail-section p {
            color: rgba(255, 255, 255, 0.8);
            line-height: 1.6;
        }

        .apply-section {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .apply-section button {
            padding: 12px 35px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        .apply-section button::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .apply-section button:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
        }

        .title-highlight {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            font-weight: bold;
            display: inline-block;
        }

        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                padding: 80px 0 20px;
            }
            
            .main-content {
                padding-top: 20px;
            }
            
            .job-card {
                flex-direction: column;
            }
            
            .job-logo {
                margin-bottom: 20px;
                margin-right: 0;
            }
            
            .modal-content {
                width: 90%;
                margin-top: 10%;
            }
            
            .job-detail-header {
                flex-direction: column;
                text-align: center;
            }
            
            .job-detail-logo {
                margin-right: 0;
                margin-bottom: 20px;
            }
            
            .header {
                flex-direction: column;
                gap: 15px;
            }
            
            .search-bar {
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-logo">
                <h2>CareerSync AI</h2>
            </div>
            <ul class="sidebar-menu">
                <li class="active"><i class="fas fa-briefcase"></i> Jobs</li>
                <li id="resume-menu-item"><i class="fas fa-file-alt"></i> Resume</li>
                <li><i class="fas fa-user"></i> Profile</li>
                <li><i class="fas fa-cog"></i> Settings</li>
                <li><a href="/logout" style="text-decoration: none; color: inherit;"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>
        
        <div class="main-content">
            <div class="header">
                <div class="search-bar">
                    <input type="text" placeholder="Search for jobs...">
                </div>
                <div class="user-profile">
                    <img src="https://via.placeholder.com/40" alt="User">
                    <span>{{ username }}</span>
                </div>
            </div>
            
            <div id="jobs-section">
                <div class="job-filters">
                    <div class="filter-pill active">All Jobs</div>
                    <div class="filter-pill">Remote</div>
                    <div class="filter-pill">Full-time</div>
                    <div class="filter-pill">Entry Level</div>
                </div>
                
                <div class="job-list">
                    {% for job in jobs %}
                    <div class="job-card" data-job-id="{{ job.id }}">
                        <div class="job-logo">
                            <img src="https://via.placeholder.com/40" alt="{{ job.company_name }}">
                        </div>
                        <div class="job-info">
                            <div class="job-title">{{ job.role_name }}</div>
                            <div class="job-company">{{ job.company_name }}</div>
                            <div class="job-details">
                                <span><i class="fas fa-map-marker-alt"></i> {{ job.location|default('Not specified') }}</span>
                                <span><i class="fas fa-briefcase"></i> {{ job.experience }}</span>
                            </div>
                        </div>
                        <div class="job-actions">
                            <div class="match-indicator">
                                {% set match_class = 'high-match' if job.match_percentage >= 70 else ('medium-match' if job.match_percentage >= 40 else 'low-match') %}
                                <div class="match-percentage {{ match_class }}">{{ job.match_percentage }}%</div>
                                <div class="match-text">{{ 'Good Match' if job.match_percentage >= 70 else ('Fair Match' if job.match_percentage >= 40 else 'Low Match') }}</div>
                            </div>
                            <button class="apply-btn" data-job-id="{{ job.id }}">Apply Now</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div id="resume-section" style="display: none;">
                <div class="resume-upload">
                    <h2>Upload Your Resume</h2>
                    <form action="/upload_resume" method="POST" enctype="multipart/form-data">
                        <label for="resume-file" class="upload-btn">Choose File</label>
                        <input type="file" id="resume-file" name="resume" class="file-input" accept=".pdf,.doc,.docx">
                        <span id="file-name">No file chosen</span>
                        <button type="submit" class="upload-btn" style="margin-left: 10px;">Upload</button>
                    </form>
                    
                    {% if has_resume %}
                    <div class="resume-status">
                        <h3>Resume Analysis</h3>
                        <p><strong>Skills:</strong></p>
                        <div class="skills-container">
                            {% for skill in skills %}
                            <div class="skill-tag">{{ skill }}</div>
                            {% endfor %}
                        </div>
                        <p><strong>Education:</strong> {{ education|join(', ') }}</p>
                        <p><strong>Experience:</strong> {{ experience }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <div id="job-detail-modal" class="modal">
        <div class="modal-content">
            <span class="close-btn">&times;</span>
            <div class="job-detail-header">
                <div class="job-detail-logo">
                    <img src="https://via.placeholder.com/60" alt="Company Logo">
                </div>
                <div class="job-detail-info">
                    <h2 id="modal-job-title"></h2>
                    <div id="modal-job-company" class="job-detail-company"></div>
                </div>
            </div>
            
            <div class="job-detail-section">
                <h3>Job Description</h3>
                <p id="modal-job-description"></p>
            </div>
            
            <div class="job-detail-section">
                <h3>Qualifications</h3>
                <p id="modal-job-qualifications"></p>
            </div>
            
            <div class="job-detail-section">
                <h3>Experience Required</h3>
                <p id="modal-job-experience"></p>
            </div>
            
            <div class="job-detail-section">
                <h3>Match Analysis</h3>
                <div id="modal-match-details"></div>
            </div>
            
            <div class="apply-section">
                <button id="modal-apply-btn">Apply for this Position</button>
            </div>
        </div>
    </div>
    
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
    <script>
        // Toggle between jobs and resume sections
        document.getElementById('resume-menu-item').addEventListener('click', function() {
            document.getElementById('jobs-section').style.display = 'none';
            document.getElementById('resume-section').style.display = 'block';
            
            // Update active menu item
            document.querySelector('.sidebar-menu li.active').classList.remove('active');
            this.classList.add('active');
        });
        
        // Show file name when selected
        document.getElementById('resume-file').addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
            document.getElementById('file-name').textContent = fileName;
        });
        
        // Job detail modal functionality
        const modal = document.getElementById('job-detail-modal');
        const closeBtn = document.querySelector('.close-btn');
        
        // Close modal when clicking the X
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Open modal when clicking on job card
        document.querySelectorAll('.job-card').forEach(card => {
            card.addEventListener('click', function(e) {
                // Don't open modal if clicking apply button
                if (e.target.classList.contains('apply-btn')) return;
                
                const jobId = this.getAttribute('data-job-id');
                fetchJobDetails(jobId);
            });
        });
        
        // Apply button functionality
        document.querySelectorAll('.apply-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent opening the modal
                const jobId = this.getAttribute('data-job-id');
                applyForJob(jobId);
            });
        });
        
        // Modal apply button
        document.getElementById('modal-apply-btn').addEventListener('click', function() {
            const jobId = this.getAttribute('data-job-id');
            applyForJob(jobId);
        });
        
        // Fetch job details for modal
        function fetchJobDetails(jobId) {
            fetch(`/job_details/${jobId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('modal-job-title').textContent = data.role_name;
                    document.getElementById('modal-job-company').textContent = data.company_name;
                    document.getElementById('modal-job-description').textContent = data.description;
                    document.getElementById('modal-job-qualifications').textContent = data.qualifications;
                    document.getElementById('modal-job-experience').textContent = data.experience;
                    
                    // Match details
                    const matchHtml = `
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div class="match-percentage ${data.match_percentage >= 70 ? 'high-match' : (data.match_percentage >= 40 ? 'medium-match' : 'low-match')}" style="margin-right: 15px;">
                                ${data.match_percentage}%
                            </div>
                            <div>
                                <div style="font-weight: bold; margin-bottom: 5px;">
                                    ${data.match_percentage >= 70 ? 'Good Match' : (data.match_percentage >= 40 ? 'Fair Match' : 'Low Match')}
                                </div>
                                <div>Based on your resume and the job requirements</div>
                            </div>
                        </div>
                        <div>
                            <p>Your resume matches ${data.match_percentage}% of the job requirements. ${
                                data.match_percentage >= 70 ? 
                                'You have a strong profile for this position!' : 
                                (data.match_percentage >= 40 ? 
                                'You meet some of the key requirements for this role.' : 
                                'You might need additional skills or experience for this role.')
                            }</p>
                        </div>
                    `;
                    document.getElementById('modal-match-details').innerHTML = matchHtml;
                    
                    // Set job ID for apply button
                    document.getElementById('modal-apply-btn').setAttribute('data-job-id', jobId);
                    
                    // Show modal
                    modal.style.display = 'block';
                })
                .catch(error => console.error('Error fetching job details:', error));
        }
        
        // Apply for job
        function applyForJob(jobId) {
            fetch(`/apply_job/${jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Application submitted successfully!');
                    // Update button to show applied
                    const applyBtns = document.querySelectorAll(`.apply-btn[data-job-id="${jobId}"]`);
                    applyBtns.forEach(btn => {
                        btn.textContent = 'Applied';
                        btn.disabled = true;
                        btn.style.backgroundColor = '#4CAF50';
                    });
                    
                    // Close modal if open
                    modal.style.display = 'none';
                } else {
                    alert(data.message || 'Failed to submit application. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error applying for job:', error);
                alert('An error occurred. Please try again.');
            });
        }
    </script>
</body>
</html>
"""

# Continue the recruiter_dashboard template

recruiter_dashboard = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recruiter Dashboard - CareerSync AI</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        @keyframes shine {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }

        @keyframes slideInLeft {
            from { transform: translateX(-100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(100px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.8), rgba(0,0,0,0.5)),
                url('https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-1.2.1');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }

        .container {
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar Styling */
        .sidebar {
            width: 250px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            padding: 20px 0;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideInLeft 0.5s ease-out;
        }

        .sidebar-logo {
            padding: 0 20px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 20px;
            animation: fadeIn 0.8s ease-out;
        }

        .sidebar-logo img {
            max-width: 150px;
        }

        .sidebar-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .sidebar-menu li {
            padding: 10px 20px;
            margin: 5px 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            transition: all 0.3s;
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out forwards;
        }

        .sidebar-menu li:hover, .sidebar-menu li.active {
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.2), rgba(0, 255, 157, 0.2));
            color: #fff;
            transform: translateX(5px);
        }

        .sidebar-menu li.active {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
        }

        .sidebar-menu li i {
            margin-right: 10px;
            width: 20px;
            text-align: center;
        }

        /* Main Content Styling */
        .main-content {
            flex: 1;
            padding: 20px;
            background: rgba(0, 0, 0, 0.4);
            animation: fadeIn 0.5s ease-out;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out;
        }

        .page-title {
            font-size: 24px;
            font-weight: 600;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: float 6s ease-in-out infinite;
        }

        .user-profile {
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 15px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .user-profile:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        .user-profile img {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid rgba(0, 212, 255, 0.7);
        }

        /* Dashboard Stats */
        .dashboard-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
            animation: fadeIn 0.8s ease-out;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            flex-direction: column;
            transition: all 0.3s;
            animation: fadeIn 0.5s ease-out forwards;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .stat-label {
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
        }

        /* Tabs Styling */
        .content-tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .tab {
            padding: 10px 20px;
            cursor: pointer;
            transition: all 0.3s;
            border-radius: 10px 10px 0 0;
            margin-right: 5px;
            color: rgba(255, 255, 255, 0.7);
        }

        .tab:hover {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }

        .tab.active {
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.3), rgba(0, 255, 157, 0.3));
            color: #fff;
            border-bottom: 2px solid #00d4ff;
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease-out;
        }

        .tab-content.active {
            display: block;
        }

        /* Section Headers */
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .action-btn {
            padding: 10px 20px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            position: relative;
            overflow: hidden;
        }

        .action-btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .action-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        /* Job Lists */
        .job-list, .applicant-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .job-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            transition: all 0.3s;
            animation: fadeIn 0.5s ease-out forwards;
        }

        .job-card:hover {
            transform: translateY(-3px);
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .job-info {
            flex: 1;
        }

        .job-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 5px;
            color: #fff;
        }

        .job-company {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 10px;
        }

        .job-meta {
            display: flex;
            gap: 15px;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.6);
        }

        .job-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Applicant Cards */
        .applicant-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
            animation: fadeIn 0.5s ease-out forwards;
        }

        .applicant-card:hover {
            transform: translateY(-3px);
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        .applicant-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .applicant-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.3), rgba(0, 255, 157, 0.3));
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #fff;
            border: 2px solid rgba(0, 212, 255, 0.7);
        }

        .applicant-details h3 {
            margin: 0 0 5px 0;
            font-size: 16px;
        }

        .applicant-details p {
            margin: 0;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.7);
        }

        /* Status Badges */
        .match-badge {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 14px;
            font-weight: 600;
            color: white;
            animation: pulse 2s infinite;
        }

        .high-match {
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
        }

        .medium-match {
            background: linear-gradient(45deg, #ffd166, #ff9f1c);
        }

        .low-match {
            background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
        }

        .status-badge {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-pending {
            background: rgba(0, 112, 243, 0.2);
            color: #00d4ff;
        }

        .status-approved {
            background: rgba(40, 167, 69, 0.2);
            color: #00ff9d;
        }

        .status-rejected {
            background: rgba(220, 53, 69, 0.2);
            color: #ff6b6b;
        }

        /* Modal Styling */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            animation: fadeIn 0.3s ease-out;
        }

        .modal-content {
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(15px);
            margin: 10% auto;
            padding: 30px;
            border-radius: 15px;
            width: 60%;
            max-width: 700px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            animation: fadeIn 0.5s ease-out;
        }

        .close-btn {
            color: rgba(255, 255, 255, 0.7);
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }

        .close-btn:hover {
            color: #fff;
            transform: rotate(90deg);
        }

        /* Form Styling */
        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.9);
        }

        .form-group input, .form-group textarea {
            width: 100%;
            padding: 12px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: #fff;
            font-size: 14px;
            transition: all 0.3s;
        }

        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: rgba(0, 212, 255, 0.7);
            background: rgba(255, 255, 255, 0.15);
        }

        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }

        .submit-btn {
            padding: 12px 25px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            position: relative;
            overflow: hidden;
        }

        .submit-btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .submit-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        /* Applicant Detail */
        .applicant-detail-header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            animation: fadeIn 0.5s ease-out;
        }

        .applicant-detail-avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(45deg, rgba(0, 212, 255, 0.3), rgba(0, 255, 157, 0.3));
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 24px;
            color: #fff;
            margin-right: 20px;
            border: 2px solid rgba(0, 212, 255, 0.7);
            animation: pulse 3s infinite;
        }

        .applicant-detail-info h2 {
            margin: 0 0 5px 0;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .applicant-detail-job {
            font-size: 16px;
            color: rgba(255, 255, 255, 0.7);
        }

        .applicant-detail-section {
            margin-bottom: 30px;
            animation: fadeIn 0.8s ease-out;
        }

        .applicant-detail-section h3 {
            margin-top: 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
            color: rgba(255, 255, 255, 0.9);
        }

        .skills-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }

        .skill-tag {
            padding: 8px 12px;
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            border-radius: 15px;
            font-size: 12px;
            transition: all 0.3s;
            border: 1px solid rgba(0, 212, 255, 0.3);
        }

        .skill-tag:hover {
            transform: translateY(-2px);
            background: rgba(0, 212, 255, 0.3);
        }

        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }

        .approve-btn {
            padding: 12px 25px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            position: relative;
            overflow: hidden;
        }

        .approve-btn::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            transform: rotate(45deg);
            animation: shine 3s infinite;
        }

        .approve-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        .reject-btn {
            padding: 12px 25px;
            background: rgba(220, 53, 69, 0.3);
            color: white;
            border: 1px solid rgba(220, 53, 69, 0.5);
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }

        .reject-btn:hover {
            transform: translateY(-3px);
            background: rgba(220, 53, 69, 0.5);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }

        /* Responsive Styling */
        @media (max-width: 768px) {
            .container {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                padding: 10px 0;
            }
            
            .dashboard-stats {
                grid-template-columns: 1fr;
            }
            
            .job-card, .applicant-card {
                flex-direction: column;
            }
            
            .job-actions, .applicant-actions {
                margin-top: 15px;
            }
            
            .modal-content {
                width: 90%;
            }
            
            .hero h1 {
                font-size: 2.5rem;
            }
            
            .section {
                margin: 10px;
                padding: 20px 15px;
            }
            
            .action-btn, .submit-btn, .approve-btn, .reject-btn {
                padding: 10px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="sidebar-logo">
                <h2>CareerSync AI</h2>
            </div>
            <ul class="sidebar-menu">
                <li class="active" data-tab="dashboard"><i class="fas fa-tachometer-alt"></i> Dashboard</li>
                <li data-tab="jobs"><i class="fas fa-briefcase"></i> Jobs</li>
                <li data-tab="applicants"><i class="fas fa-users"></i> Applicants</li>
                <li data-tab="analytics"><i class="fas fa-chart-bar"></i> Analytics</li>
                <li><a href="/logout" style="text-decoration: none; color: inherit;"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
            </ul>
        </div>
        
        <div class="main-content">
            <div class="header">
                <div class="page-title">Recruiter Dashboard</div>
                <div class="user-profile">
                    <img src="https://via.placeholder.com/40" alt="User">
                    <span>{{ username }}</span>
                </div>
            </div>
            
            <!-- Dashboard Tab -->
            <div id="dashboard-tab" class="tab-content active">
                <div class="dashboard-stats">
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.active_jobs }}</div>
                        <div class="stat-label">Active Jobs</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.total_applicants }}</div>
                        <div class="stat-label">Total Applicants</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.new_applicants }}</div>
                        <div class="stat-label">New Applicants</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{{ stats.avg_match }}%</div>
                        <div class="stat-label">Avg. Match Rate</div>
                    </div>
                </div>
                
                <div class="section-header">
                    <div class="section-title">Recent Jobs</div>
                    <a href="#" class="action-btn" id="post-job-btn">Post New Job</a>
                </div>
                
                <div class="job-list">
                    {% for job in jobs %}
                    <div class="job-card">
                        <div class="job-info">
                            <div class="job-title">{{ job.role_name }}</div>
                            <div class="job-company">{{ job.company_name }}</div>
                            <div class="job-meta">
                                <span><i class="fas fa-map-marker-alt"></i> {{ job.location }}</span>
                                <span><i class="fas fa-user-friends"></i> {{ job.applicant_count }} applicants</span>
                                <span><i class="fas fa-calendar-alt"></i> Posted on {{ job.posted_date }}</span>
                            </div>
                        </div>
                        <div class="job-actions">
                            <button class="action-btn view-job-btn" data-job-id="{{ job.id }}">View Details</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <div class="section-header" style="margin-top: 30px;">
                    <div class="section-title">Recent Applicants</div>
                    <a href="#" class="action-btn" data-tab="applicants">View All</a>
                </div>
                
                <div class="applicant-list">
                    {% for applicant in applicants %}
                    <div class="applicant-card" data-applicant-id="{{ applicant.id }}">
                        <div class="applicant-info">
                            <div class="applicant-avatar">{{ applicant.username[0] }}</div>
                            <div class="applicant-details">
                                <h3>{{ applicant.username }}</h3>
                                <p>Applied for {{ applicant.role_name }}</p>
                                <p><small>{{ applicant.application_date }}</small></p>
                            </div>
                        </div>
                        <div class="applicant-actions">
                            {% set match_class = 'high-match' if applicant.match_percentage >= 70 else ('medium-match' if applicant.match_percentage >= 40 else 'low-match') %}
                            <span class="match-badge {{ match_class }}">{{ applicant.match_percentage }}% Match</span>
                            {% set status_class = 'status-pending' if applicant.status == 'pending' else ('status-approved' if applicant.status == 'approved' else 'status-rejected') %}
                            <span class="status-badge {{ status_class }}">{{ applicant.status|title }}</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Jobs Tab -->
            <div id="jobs-tab" class="tab-content">
                <div class="section-header">
                    <div class="section-title">All Jobs</div>
                    <a href="#" class="action-btn" id="post-job-btn-2">Post New Job</a>
                </div>
                
                <div class="job-list">
                    {% for job in all_jobs %}
                    <div class="job-card">
                        <div class="job-info">
                            <div class="job-title">{{ job.role_name }}</div>
                            <div class="job-company">{{ job.company_name }}</div>
                            <div class="job-meta">
                                <span><i class="fas fa-map-marker-alt"></i> {{ job.location }}</span>
                                <span><i class="fas fa-user-friends"></i> {{ job.applicant_count }} applicants</span>
                                <span><i class="fas fa-calendar-alt"></i> Posted on {{ job.posted_date }}</span>
                            </div>
                        </div>
                        <div class="job-actions">
                            <button class="action-btn view-job-btn" data-job-id="{{ job.id }}">View Details</button>
                            <button class="action-btn view-applicants-btn" data-job-id="{{ job.id }}">View Applicants</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Applicants Tab -->
            <div id="applicants-tab" class="tab-content">
                <div class="section-header">
                    <div class="section-title">All Applicants</div>
                </div>
                
                <div class="applicant-list">
                    {% for applicant in all_applicants %}
                    <div class="applicant-card" data-applicant-id="{{ applicant.id }}">
                        <div class="applicant-info">
                            <div class="applicant-avatar">{{ applicant.username[0] }}</div>
                            <div class="applicant-details">
                                <h3>{{ applicant.username }}</h3>
                                <p>Applied for {{ applicant.role_name }}</p>
                                <p><small>{{ applicant.application_date }}</small></p>
                            </div>
                        </div>
                        <div class="applicant-actions">
                            {% set match_class = 'high-match' if applicant.match_percentage >= 70 else ('medium-match' if applicant.match_percentage >= 40 else 'low-match') %}
                            <span class="match-badge {{ match_class }}">{{ applicant.match_percentage }}% Match</span>
                            {% set status_class = 'status-pending' if applicant.status == 'pending' else ('status-approved' if applicant.status == 'approved' else 'status-rejected') %}
                            <span class="status-badge {{ status_class }}">{{ applicant.status|title }}</span>
                            <button class="action-btn view-applicant-btn" data-applicant-id="{{ applicant.id }}">View Profile</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Analytics Tab -->
            <div id="analytics-tab" class="tab-content">
                <div class="section-header">
                    <div class="section-title">Analytics</div>
                </div>
                
                <p>Analytics features coming soon...</p>
            </div>
        </div>
    </div>
    
    <!-- Post Job Modal -->
    <div id="post-job-modal" class="modal">
        <div class="modal-content">
            <span class="close-btn">&times;</span>
            <h2>Post a New Job</h2>
            <form id="post-job-form" action="/post_job" method="POST">
                <div class="form-group">
                    <label for="company_name">Company Name</label>
                    <input type="text" id="company_name" name="company_name" required>
                </div>
                <div class="form-group">
                    <label for="role_name">Job Title</label>
                    <input type="text" id="role_name" name="role_name" required>
                </div>
                <div class="form-group">
                    <label for="description">Job Description</label>
                    <textarea id="description" name="description" required></textarea>
                </div>
                <div class="form-group">
                    <label for="qualifications">Required Qualifications</label>
                    <textarea id="qualifications" name="qualifications" required></textarea>
                </div>
                <div class="form-group">
                    <label for="experience">Required Experience</label>
                    <textarea id="experience" name="experience" required></textarea>
                </div>
                <div class="form-group">
                    <label for="location">Location</label>
                    <input type="text" id="location" name="location">
                </div>
                <button type="submit" class="submit-btn">Post Job</button>
            </form>
        </div>
    </div>
    
    <!-- Applicant Detail Modal -->
    <div id="applicant-detail-modal" class="modal">
        <div class="modal-content">
            <span class="close-btn">&times;</span>
            <div class="applicant-detail-header">
                <div class="applicant-detail-avatar" id="applicant-detail-avatar"></div>
                <div class="applicant-detail-info">
                    <h2 id="applicant-detail-name"></h2>
                    <div id="applicant-detail-job" class="applicant-detail-job"></div>
                </div>
            </div>
            
            <div class="applicant-detail-section">
                <h3>Match Analysis</h3>
                <div id="applicant-match-details"></div>
            </div>
            
            <div class="applicant-detail-section">
                <h3>Skills</h3>
                <div id="applicant-skills" class="skills-container"></div>
            </div>
            
            <div class="applicant-detail-section">
                <h3>Education</h3>
                <div id="applicant-education"></div>
            </div>
            
            <div class="applicant-detail-section">
                <h3>Experience</h3>
                <div id="applicant-experience"></div>
            </div>
            
            <div class="applicant-detail-section">
                <h3>Resume Text</h3>
                <div id="applicant-resume-text" style="max-height: 200px; overflow-y: auto; background-color: #f5f7fa; padding: 10px; border-radius: 5px;"></div>
            </div>
            
            <div class="action-buttons">
                <button id="approve-btn" class="approve-btn">Approve Application</button>
                <button id="reject-btn" class="reject-btn">Reject Application</button>
            </div>
        </div>
    </div>
    
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
    <script>
        // Tab switching functionality
        document.querySelectorAll('.sidebar-menu li[data-tab]').forEach(item => {
            item.addEventListener('click', function() {
                // Update active tab in sidebar
                document.querySelector('.sidebar-menu li.active').classList.remove('active');
                this.classList.add('active');
                
                // Show corresponding tab content
                const tabId = this.getAttribute('data-tab');
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.remove('active');
                });
                document.getElementById(tabId + '-tab').classList.add('active');
            });
        });
        
        // Modal functionality
        const postJobModal = document.getElementById('post-job-modal');
        const applicantDetailModal = document.getElementById('applicant-detail-modal');
        const closeBtns = document.querySelectorAll('.close-btn');
        
        // Open post job modal
        document.getElementById('post-job-btn').addEventListener('click', function() {
            postJobModal.style.display = 'block';
        });
        
        document.getElementById('post-job-btn-2').addEventListener('click', function() {
            postJobModal.style.display = 'block';
        });
        
        // Close modals when clicking the X
        closeBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                postJobModal.style.display = 'none';
                applicantDetailModal.style.display = 'none';
            });
        });
        
        // Close modals when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === postJobModal) {
                postJobModal.style.display = 'none';
            }
            if (event.target === applicantDetailModal) {
                applicantDetailModal.style.display = 'none';
            }
        });
        
        // View applicant details
        document.querySelectorAll('.applicant-card, .view-applicant-btn').forEach(item => {
            item.addEventListener('click', function(e) {
                // Don't trigger if clicking on a button inside the card
                if (e.target.classList.contains('action-btn') && !e.target.classList.contains('view-applicant-btn')) return;
                
                const applicantId = this.closest('.applicant-card').getAttribute('data-applicant-id');
                fetchApplicantDetails(applicantId);
            });
        });
        
        // Fetch applicant details
        function fetchApplicantDetails(applicantId) {
            fetch(`/applicant_details/${applicantId}`)
                .then(response => response.json())
                .then(data => {
                    // Set applicant details in modal
                    document.getElementById('applicant-detail-avatar').textContent = data.username[0];
                    document.getElementById('applicant-detail-name').textContent = data.username;
                    document.getElementById('applicant-detail-job').textContent = `Applied for ${data.role_name} at ${data.company_name}`;
                    
                    // Match details
                    const matchClass = data.match_percentage >= 70 ? 'high-match' : (data.match_percentage >= 40 ? 'medium-match' : 'low-match');
                    const matchHtml = `
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div class="match-badge ${matchClass}" style="margin-right: 15px;">
                                ${data.match_percentage}%
                            </div>
                            <div>
                                <div style="font-weight: bold; margin-bottom: 5px;">
                                    ${data.match_percentage >= 70 ? 'Good Match' : (data.match_percentage >= 40 ? 'Fair Match' : 'Low Match')}
                                </div>
                                <div>Based on job requirements and candidate's resume</div>
                            </div>
                        </div>
                    `;
                    document.getElementById('applicant-match-details').innerHTML = matchHtml;
                    
                    // Skills
                    const skillsHtml = data.skills.map(skill => `<div class="skill-tag">${skill}</div>`).join('');
                    document.getElementById('applicant-skills').innerHTML = skillsHtml || 'No skills extracted';
                    
                    // Education
                    document.getElementById('applicant-education').textContent = data.education.join(', ') || 'Not specified';
                    
                    // Experience
                    document.getElementById('applicant-experience').textContent = data.experience;
                    
                    // Resume text
                    document.getElementById('applicant-resume-text').textContent = data.resume_text;
                    
                    // Set application ID for approve/reject buttons
                    document.getElementById('approve-btn').setAttribute('data-application-id', data.id);
                    document.getElementById('reject-btn').setAttribute('data-application-id', data.id);
                    
                    // Update button states based on current status
                    if (data.status === 'approved') {
                        document.getElementById('approve-btn').disabled = true;
                        document.getElementById('approve-btn').textContent = 'Already Approved';
                        // Continue the recruiter_dashboard JavaScript
                        document.getElementById('reject-btn').disabled = false;
                    } else if (data.status === 'rejected') {
                        document.getElementById('reject-btn').disabled = true;
                        document.getElementById('reject-btn').textContent = 'Already Rejected';
                        document.getElementById('approve-btn').disabled = false;
                    } else {
                        document.getElementById('approve-btn').disabled = false;
                        document.getElementById('reject-btn').disabled = false;
                        document.getElementById('approve-btn').textContent = 'Approve Application';
                        document.getElementById('reject-btn').textContent = 'Reject Application';
                    }
                    
                    // Show modal
                    applicantDetailModal.style.display = 'block';
                })
                .catch(error => console.error('Error fetching applicant details:', error));
        }
        
        // Approve application
        document.getElementById('approve-btn').addEventListener('click', function() {
            const applicationId = this.getAttribute('data-application-id');
            updateApplicationStatus(applicationId, 'approved');
        });
        
        // Reject application
        document.getElementById('reject-btn').addEventListener('click', function() {
            const applicationId = this.getAttribute('data-application-id');
            updateApplicationStatus(applicationId, 'rejected');
        });
        
        // Update application status
        function updateApplicationStatus(applicationId, status) {
            fetch(`/update_application_status/${applicationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: status })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close modal
                    applicantDetailModal.style.display = 'none';
                    
                    // Update UI to reflect the new status
                    const statusClass = status === 'approved' ? 'status-approved' : 'status-rejected';
                    const statusText = status.charAt(0).toUpperCase() + status.slice(1);
                    
                    document.querySelectorAll(`.applicant-card[data-applicant-id="${applicationId}"] .status-badge`).forEach(badge => {
                        badge.className = `status-badge ${statusClass}`;
                        badge.textContent = statusText;
                    });
                    
                    alert(`Application ${statusText} successfully!`);
                } else {
                    alert('Failed to update application status. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error updating application status:', error);
                alert('An error occurred. Please try again.');
            });
        }
    </script>
</body>
</html>
"""

post_job_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post a Job - CareerSync AI</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
            color: #333;
        }
        
        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 30px;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            margin-top: 0;
            margin-bottom: 30px;
            color: #333;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        .button-group {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
        }
        
        .submit-btn {
            padding: 12px 30px;
            background-color: #0070f3;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .submit-btn:hover {
            background-color: #005bcc;
        }
        
        .cancel-btn {
            padding: 12px 30px;
            background-color: #f5f5f5;
            color: #333;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .cancel-btn:hover {
            background-color: #e5e5e5;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .back-link {
            color: #0070f3;
            text-decoration: none;
            display: flex;
            align-items: center;
        }
        
        .back-link i {
            margin-right: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/dashboard" class="back-link"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
        </div>
        
        <h1>Post a New Job</h1>
        
        <form action="/post_job" method="POST">
            <div class="form-group">
                <label for="company_name">Company Name</label>
                <input type="text" id="company_name" name="company_name" required>
            </div>
            
            <div class="form-group">
                <label for="role_name">Job Title</label>
                <input type="text" id="role_name" name="role_name" required>
            </div>
            
            <div class="form-group">
                <label for="description">Job Description</label>
                <textarea id="description" name="description" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="qualifications">Required Qualifications</label>
                <textarea id="qualifications" name="qualifications" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="experience">Required Experience</label>
                <textarea id="experience" name="experience" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="location">Location</label>
                <input type="text" id="location" name="location" placeholder="e.g., Remote, New York, NY">
            </div>
            
            <div class="button-group">
                <a href="/dashboard" class="cancel-btn">Cancel</a>
                <button type="submit" class="submit-btn">Post Job</button>
            </div>
        </form>
    </div>
    
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
</body>
</html>
"""

login_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - CareerSync AI</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(to right, #1e3c72, #2a5298);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-container {
            background: #fff;
            color: #000;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 300px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .login-container input {
            width: 90%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .login-container button {
            padding: 10px 20px;
            background: #1e3c72;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <form method="POST">
            <h2>Login</h2>
            {% if error %}
                <p style="color: red;">{{ error }}</p>
            {% endif %}
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            
            <button type="submit">Login</button>
            <div style="margin-top: 10px; font-size: 0.9em;">
                Don't have an account? <a href="/register">Register here</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

register_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - CareerSync AI</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(to right, #1e3c72, #2a5298);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .register-container {
            background: #fff;
            color: #000;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            width: 300px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .register-container input, .register-container select {
            width: 90%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .register-container button {
            padding: 10px 20px;
            background: #1e3c72;
            color: #fff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .login-link {
            margin-top: 10px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="register-container">
        <form method="POST">
            <h2>Register</h2>
            {% if error %}
                <p style="color: red;">{{ error }}</p>
            {% endif %}
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <select name="role" required>
                <option value="job_seeker">Job Seeker</option>
                <option value="recruiter">Recruiter</option>
            </select>
            <button type="submit">Register</button>
        </form>
        <div class="login-link">
            Already have an account? <a href="/login">Login here</a>
        </div>
    </div>
</body>
</html>
"""

dashboard_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - CareerSync AI</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: 
                linear-gradient(120deg, rgba(0,0,0,0.7), rgba(0,0,0,0.4)),
                url('https://images.unsplash.com/photo-1497215728101-856f4ea42174?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            min-height: 100vh;
        }
        nav {
            display: flex;
            justify-content: space-between;
            padding: 15px 30px;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
        }
        nav a {
            color: #fff;
            text-decoration: none;
            margin: 0 10px;
            padding: 8px 15px;
            border-radius: 20px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.1);
        }
        nav a:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        .upload-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            text-align: center;
            margin-bottom: 30px;
        }
        .upload-section h2 {
            margin-bottom: 20px;
            color: #fff;
        }
        .file-upload {
            display: none;
        }
        .upload-btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            color: #fff;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 15px;
        }
        .upload-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .submit-btn {
            padding: 12px 30px;
            background: #00ff9d;
            color: #fff;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .submit-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .skills-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            margin-top: 30px;
        }
        .skills-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .skill-item {
            background: rgba(255, 255, 255, 0.2);
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .skill-item:hover {
            transform: translateY(-3px);
            background: rgba(255, 255, 255, 0.3);
        }
        #selected-file {
            margin-top: 10px;
            color: #fff;
        }
        .error-message {
            color: #ff6b6b;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/logout">Logout</a>
    </nav>
    <div class="container">
        <h1>Welcome to {{ role }}</h1>
        {% if role == "Job Seeker Dashboard" %}
        <div class="upload-section">
            <h2>Upload Your Resume</h2>
            <form action="/upload_resume" method="POST" enctype="multipart/form-data">
                <input type="file" name="resume" id="resume" class="file-upload" accept=".pdf,.doc,.docx">
                <label for="resume" class="upload-btn">Choose File</label>
                <div id="selected-file">No file chosen</div>
                {% if error %}
                    <div class="error-message">{{ error }}</div>
                {% endif %}
                <button type="submit" class="submit-btn">Analyze Resume</button>
            </form>
        </div>
        <a href="/view_jobs" class="nav-button">View Available Jobs</a>
        {% elif role == "Recruiter Dashboard" %}
        <div class="recruiter-section">
            <h2>Recruiter Tools</h2>
            <a href="/post_job" class="nav-button">Post New Job</a>
            <a href="/view_jobs" class="nav-button">View Posted Jobs</a>
        </div>
        {% endif %}
        {% if skills %}
        <div class="skills-section">
            <h2>Extracted Skills</h2>
            <div class="skills-grid">
                {% for skill in skills %}
                    <div class="skill-item">{{ skill }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        document.getElementById('resume').addEventListener('change', function(e) {
            var fileName = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
            document.getElementById('selected-file').textContent = fileName;
        });
    </script>
</body>
</html>
"""

post_job_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post a Job </title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(120deg, #ff9a9e, #fad0c4, #fbc2eb, #a18cd1);
            background-size: 400% 400%;
            animation: gradientBG 10s ease infinite;
            min-height: 100vh;
            color: #fff;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .container {
            max-width: 800px;
            margin: 80px auto;
            padding: 30px;
            background: rgba(0, 0, 0, 0.7);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #fff;
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        label {
            font-weight: bold;
            color: #fff;
        }

        input, textarea {
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            font-size: 16px;
        }

        textarea {
            min-height: 120px;
            resize: vertical;
        }

        button {
            padding: 15px;
            background: linear-gradient(45deg, #00d4ff, #00ff9d);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        nav {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px 0;
            backdrop-filter: blur(10px);
        }

        nav a {
            color: #fff;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 15px;
            border-radius: 20px;
            transition: all 0.3s ease;
        }

        nav a:hover {
            background: rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body>
    <nav>
        <a href="/dashboard">Dashboard</a>
        <a href="/logout">Logout</a>
    </nav>
    <div class="container">
        <h1>Post a New Job</h1>
        <form method="POST">
            <div class="form-group">
                <label for="company_name">Company Name</label>
                <input type="text" id="company_name" name="company_name" required>
            </div>
            <div class="form-group">
                <label for="role_name">Role Name</label>
                <input type="text" id="role_name" name="role_name" required>
            </div>
            <div class="form-group">
                <label for="description">Job Description</label>
                <textarea id="description" name="description" required></textarea>
            </div>
            <div class="form-group">
                <label for="qualifications">Required Qualifications</label>
                <textarea id="qualifications" name="qualifications" required></textarea>
            </div>
            <div class="form-group">
                <label for="experience">Required Experience</label>
                <textarea id="experience" name="experience" required></textarea>
            </div>
            <button type="submit">Post Job</button>
        </form>
    </div>
</body>
</html>
"""

view_jobs_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Jobs </title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(120deg, #ff9a9e, #fad0c4, #fbc2eb, #a18cd1);
            background-size: 400% 400%;
            animation: gradientBG 10s ease infinite;
            min-height: 100vh;
            color: #fff;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .container {
            max-width: 1200px;
            margin: 80px auto;
            padding: 20px;
        }

        .jobs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }

        .job-card {
            background: rgba(0, 0, 0, 0.7);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }

        .job-card:hover {
            transform: translateY(-5px);
        }

        .job-card h3 {
            color: #00d4ff;
            margin-bottom: 10px;
        }

        .job-card h4 {
            color: #00ff9d;
            margin-bottom: 15px;
        }

        .job-card p {
            margin: 10px 0;
            color: #fff;
        }

        nav {
            position: fixed;
            top: 0;
            width: 100%;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px 0;
            backdrop-filter: blur(10px);
            z-index: 1000;
        }

        nav a {
            color: #fff;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 15px;
            border-radius: 20px;
            transition: all 0.3s ease;
        }

        nav a:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #fff;
        }
    </style>
</head>
<body>
    <nav>
        <a href="/dashboard">Dashboard</a>
        <a href="/logout">Logout</a>
    </nav>
    <div class="container">
        <h1>Available Jobs</h1>
        <div class="jobs-grid">
            {% for job in jobs %}
            <div class="job-card">
                <h3>{{ job[2] }}</h3>
                <h4>{{ job[1] }}</h4>
                <p><strong>Description:</strong> {{ job[3] }}</p>
                <p><strong>Qualifications:</strong> {{ job[4] }}</p>
                <p><strong>Experience:</strong> {{ job[5] }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

# Routes
@app.route('/')
def home():
    return render_template_string(home_page)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, password, role))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string(register_page, error="Username already exists")
        
    return render_template_string(register_page)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(login_page, error="Invalid credentials")
    return render_template_string(login_page)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Add new route for resume upload


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    role = session['role']
    user_id = get_user_id(session['username'])

    if role == 'job_seeker':
        # Get user's resume data if exists
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM resumes WHERE user_id = ?', (user_id,))
        resume_data = cursor.fetchone()

        # Get all jobs with match percentage
        jobs = []
        if resume_data:
            cursor.execute('SELECT * FROM jobs')
            all_jobs = cursor.fetchall()

            for job in all_jobs:
                job_id = job[0]
                company_name = job[1]
                role_name = job[2]
                description = job[3]
                qualifications = job[4]
                experience = job[5]
                location = job[6] if len(job) > 6 else "Not specified"

                # Calculate match percentage
                job_description = f"{role_name} {description} {qualifications} {experience}"
                match_percentage = calculate_match_percentage(resume_data[2], job_description)

                # Check if user has already applied
                cursor.execute('SELECT * FROM applications WHERE job_id = ? AND user_id = ?',
                              (job_id, user_id))
                application = cursor.fetchone()

                jobs.append({
                    'id': job_id,
                    'company_name': company_name,
                    'role_name': role_name,
                    'description': description,
                    'qualifications': qualifications,
                    'experience': experience,
                    'location': location,
                    'match_percentage': match_percentage,
                    'applied': application is not None
                })

            # Sort jobs by match percentage (highest first)
            jobs.sort(key=lambda x: x['match_percentage'], reverse=True)

        # Parse skills, education, and experience from resume data
        skills = []
        education = []
        experience = "Not specified"
        has_resume = False

        if resume_data:
            has_resume = True
            skills = resume_data[3].split(',') if resume_data[3] else []
            education = resume_data[4].split(',') if resume_data[4] else []
            experience = resume_data[5] if resume_data[5] else "Not specified"

        conn.close()

        return render_template_string(job_seeker_dashboard,
                                     username=session['username'],
                                     jobs=jobs,
                                     has_resume=has_resume,
                                     skills=skills,
                                     education=education,
                                     experience=experience)

    elif role == 'recruiter':
        # Get recruiter dashboard data
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Get jobs posted by this recruiter
        cursor.execute('''
            SELECT j.id, j.company_name, j.role_name, j.description, j.qualifications, j.experience,
                   j.location, COUNT(a.id) as applicant_count, datetime(j.id, 'unixepoch') as posted_date
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id
            WHERE j.posted_by = ?
            GROUP BY j.id
            ORDER BY j.id DESC
        ''', (user_id,))

        jobs_data = cursor.fetchall()
        jobs = []

        for job in jobs_data:
            jobs.append({
                'id': job[0],
                'company_name': job[1],
                'role_name': job[2],
                'description': job[3],
                'qualifications': job[4],
                'experience': job[5],
                'location': job[6] if job[6] else "Not specified",
                'applicant_count': job[7],
                'posted_date': job[8]
            })

        # Get recent applicants
        cursor.execute('''
            SELECT a.id, u.username, j.role_name, a.match_percentage,
                   datetime(a.application_date) as app_date, a.status
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN jobs j ON a.job_id = j.id
            WHERE j.posted_by = ?
            ORDER BY a.application_date DESC
            LIMIT 10
        ''', (user_id,))

        applicants_data = cursor.fetchall()
        applicants = []

        for applicant in applicants_data:
            applicants.append({
                'id': applicant[0],
                'username': applicant[1],
                'role_name': applicant[2],
                'match_percentage': applicant[3],
                'application_date': applicant[4],
                'status': applicant[5]
            })

        # Get all applicants for the applicants tab
        cursor.execute('''
            SELECT a.id, u.username, j.role_name, a.match_percentage,
                   datetime(a.application_date) as app_date, a.status
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN jobs j ON a.job_id = j.id
            WHERE j.posted_by = ?
            ORDER BY a.application_date DESC
        ''', (user_id,))

        all_applicants_data = cursor.fetchall()
        all_applicants = []

        for applicant in all_applicants_data:
            all_applicants.append({
                'id': applicant[0],
                'username': applicant[1],
                'role_name': applicant[2],
                'match_percentage': applicant[3],
                'application_date': applicant[4],
                'status': applicant[5]
            })

        # Get all jobs for the jobs tab
        cursor.execute('''
            SELECT j.id, j.company_name, j.role_name, j.description, j.qualifications, j.experience,
                   j.location, COUNT(a.id) as applicant_count, datetime(j.id, 'unixepoch') as posted_date
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id
            WHERE j.posted_by = ?
            GROUP BY j.id
            ORDER BY j.id DESC
        ''', (user_id,))

        all_jobs_data = cursor.fetchall()
        all_jobs = []

        for job in all_jobs_data:
            all_jobs.append({
                'id': job[0],
                'company_name': job[1],
                'role_name': job[2],
                'description': job[3],
                'qualifications': job[4],
                'experience': job[5],
                'location': job[6] if job[6] else "Not specified",
                'applicant_count': job[7],
                'posted_date': job[8]
            })

        # Calculate dashboard stats
        active_jobs = len(jobs)
        total_applicants = len(all_applicants)
        new_applicants = len([a for a in all_applicants if a['status'] == 'pending'])

        # Calculate average match percentage
        avg_match = 0
        if total_applicants > 0:
            avg_match = sum(a['match_percentage'] for a in all_applicants) // total_applicants

        stats = {
            'active_jobs': active_jobs,
            'total_applicants': total_applicants,
            'new_applicants': new_applicants,
            'avg_match': avg_match
        }

        conn.close()

        return render_template_string(recruiter_dashboard,
                                     username=session['username'],
                                     jobs=jobs,
                                     applicants=applicants,
                                     all_jobs=all_jobs,
                                     all_applicants=all_applicants,
                                     stats=stats)

    return redirect(url_for('login'))

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'username' not in session or session['role'] != 'job_seeker':
        return redirect(url_for('login'))

    if 'resume' not in request.files:
        return redirect(url_for('dashboard'))

    file = request.files['resume']
    if file.filename == '':
        return redirect(url_for('dashboard'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Analyze resume
        resume_analysis = analyze_resume(filepath)

        # Store resume data in database
        user_id = get_user_id(session['username'])

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Check if user already has a resume
        cursor.execute('SELECT id FROM resumes WHERE user_id = ?', (user_id,))
        existing_resume = cursor.fetchone()

        if existing_resume:
            # Update existing resume
            cursor.execute('''
                UPDATE resumes
                SET resume_text = ?, skills = ?, education = ?, experience = ?
                WHERE user_id = ?
            ''', (
                resume_analysis['full_text'],
                ','.join(resume_analysis['skills']),
                ','.join(resume_analysis['education']),
                resume_analysis['experience'],
                user_id
            ))
        else:
            # Insert new resume
            cursor.execute('''
                INSERT INTO resumes (user_id, resume_text, skills, education, experience)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                resume_analysis['full_text'],
                ','.join(resume_analysis['skills']),
                ','.join(resume_analysis['education']),
                resume_analysis['experience']
            ))

        conn.commit()
        conn.close()

        # Delete the file after processing
        os.remove(filepath)

    return redirect(url_for('dashboard'))

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'username' not in session or session['role'] != 'recruiter':
        return redirect(url_for('login'))

    if request.method == 'POST':
        company_name = request.form['company_name']
        role_name = request.form['role_name']
        description = request.form['description']
        qualifications = request.form['qualifications']
        experience = request.form['experience']
        location = request.form.get('location', '')

        user_id = get_user_id(session['username'])

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO jobs (company_name, role_name, description, qualifications, experience, location, posted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (company_name, role_name, description, qualifications, experience, location, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template_string(post_job_page)

@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()

    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404

    # Calculate match percentage if job seeker
    match_percentage = 0
    if session['role'] == 'job_seeker':
        user_id = get_user_id(session['username'])
        cursor.execute('SELECT resume_text FROM resumes WHERE user_id = ?', (user_id,))
        resume = cursor.fetchone()

        if resume:
            job_description = f"{job[2]} {job[3]} {job[4]} {job[5]}"
            match_percentage = calculate_match_percentage(resume[0], job_description)

    # Check if user has already applied
    user_id = get_user_id(session['username'])
    cursor.execute('SELECT id FROM applications WHERE job_id = ? AND user_id = ?', (job_id, user_id))
    application = cursor.fetchone()

    conn.close()

    return jsonify({
        'id': job[0],
        'company_name': job[1],
        'role_name': job[2],
        'description': job[3],
        'qualifications': job[4],
        'experience': job[5],
        'location': job[6] if len(job) > 6 else "Not specified",
        'match_percentage': match_percentage,
        'applied': application is not None
    })

@app.route('/apply_job/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'username' not in session or session['role'] != 'job_seeker':
        return jsonify({'success': False, 'message': 'Not authorized'}), 401

    user_id = get_user_id(session['username'])

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Check if user has already applied
    cursor.execute('SELECT id FROM applications WHERE job_id = ? AND user_id = ?', (job_id, user_id))
    existing_application = cursor.fetchone()

    if existing_application:
        conn.close()
        return jsonify({'success': False, 'message': 'You have already applied for this job'})

    # Check if user has a resume
    cursor.execute('SELECT resume_text FROM resumes WHERE user_id = ?', (user_id,))
    resume = cursor.fetchone()

    if not resume:
        conn.close()
        return jsonify({'success': False, 'message': 'Please upload your resume before applying'})

    # Get job details
    cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = cursor.fetchone()

    if not job:
        conn.close()
        return jsonify({'success': False, 'message': 'Job not found'})

    # Calculate match percentage
    job_description = f"{job[2]} {job[3]} {job[4]} {job[5]}"
    match_percentage = calculate_match_percentage(resume[0], job_description)

    # Create application
    cursor.execute('''
        INSERT INTO applications (job_id, user_id, match_percentage, status)
        VALUES (?, ?, ?, ?)
    ''', (job_id, user_id, match_percentage, 'pending'))

    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/applicant_details/<int:application_id>')
def applicant_details(application_id):
    if 'username' not in session or session['role'] != 'recruiter':
        return jsonify({'error': 'Not authorized'}), 401

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get application details
    cursor.execute('''
        SELECT a.id, a.job_id, a.user_id, a.match_percentage, a.status,
               u.username, j.role_name, j.company_name
        FROM applications a
        JOIN users u ON a.user_id = u.id
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ?
    ''', (application_id,))

    application = cursor.fetchone()

    if not application:
        conn.close()
        return jsonify({'error': 'Application not found'}), 404

    # Get resume details
    cursor.execute('SELECT * FROM resumes WHERE user_id = ?', (application[2],))
    resume = cursor.fetchone()

    if not resume:
        conn.close()
        return jsonify({'error': 'Resume not found'}), 404

    # Parse skills and education
    skills = resume[3].split(',') if resume[3] else []
    education = resume[4].split(',') if resume[4] else []
    experience = resume[5] if resume[5] else "Not specified"

    conn.close()

    return jsonify({
        'id': application[0],
        'job_id': application[1],
        'user_id': application[2],
        'match_percentage': application[3],
        'status': application[4],
        'username': application[5],
        'role_name': application[6],
        'company_name': application[7],
        'skills': skills,
        'education': education,
        'experience': experience,
        'resume_text': resume[2]
    })

@app.route('/update_application_status/<int:application_id>', methods=['POST'])
def update_application_status(application_id):
    if 'username' not in session or session['role'] != 'recruiter':
        return jsonify({'success': False, 'message': 'Not authorized'}), 401

    data = request.json
    status = data.get('status')

    if status not in ['approved', 'rejected']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Update application status
    cursor.execute('UPDATE applications SET status = ? WHERE id = ?', (status, application_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/view_jobs')
def view_jobs():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs')
    jobs = cursor.fetchall()
    conn.close()
    
    return render_template_string(view_jobs_page, jobs=jobs)

if __name__ == '__main__':
    app.run(debug=True)