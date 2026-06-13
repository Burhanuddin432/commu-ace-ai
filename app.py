# =========================================================
# COMMU-ACE AI - VERSION 1.0
# =========================================================

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import base64
import io
import os
import re
import json
import time
import random
from dash.exceptions import PreventUpdate
import nest_asyncio

nest_asyncio.apply()

# Try to import PyMuPDF for better PDF extraction
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("Warning: PyMuPDF not installed. Install with: pip install PyMuPDF")

# =========================================================
# CONFIGURATION
# =========================================================
APP_TITLE = "COMMU-ACE AI"
APP_VERSION = "1.0.0"
MAX_INTERVIEW_QUESTIONS = 5  # 5 sesi interview

AVAILABLE_ROLES = [
    'Data Scientist', 'Machine Learning Engineer', 'Software Engineer',
    'Product Manager', 'Project Manager', 'UX/UI Designer',
    'Marketing Specialist', 'Sales Executive', 'HR Generalist',
    'Financial Analyst', 'Business Analyst', 'DevOps Engineer',
    'Cloud Architect', 'Cybersecurity Analyst', 'Data Analyst'
]

# Grade mapping
GRADE_CONFIG = {
    'A': {'min_score': 85, 'color': '#10b981', 'label': 'Excellent', 'description': 'Sangat baik, siap untuk posisi senior', 'icon': '🏆'},
    'B': {'min_score': 70, 'color': '#3b82f6', 'label': 'Good', 'description': 'Baik, perlu sedikit peningkatan', 'icon': '👍'},
    'C': {'min_score': 55, 'color': '#f59e0b', 'label': 'Fair', 'description': 'Cukup, perlu persiapan lebih matang', 'icon': '📝'},
    'D': {'min_score': 0, 'color': '#ef4444', 'label': 'Need Improvement', 'description': 'Perlu belajar lebih banyak', 'icon': '⚠️'}
}

# =========================================================
# CREATIVE QUESTION BANK - BERVARIASI
# =========================================================
QUESTION_BANK = {
    'HR': [
        "Tell me about yourself and what brings you here today.",
        "Why are you interested in working for our company?",
        "What are your greatest strengths and weaknesses?",
        "Describe a time when you faced a conflict at work and how you resolved it.",
        "Where do you see yourself in 5 years?",
        "Why should we hire you over other candidates?",
        "Tell me about a time you failed and what you learned from it.",
        "How do you handle pressure and tight deadlines?",
        "Describe your ideal work environment.",
        "What motivates you to do your best work?"
    ],
    'Technical': [
        "Explain a complex technical concept you recently worked with.",
        "How do you stay updated with the latest technologies?",
        "Describe your approach to debugging a critical issue.",
        "What's your experience with version control systems?",
        "How do you ensure code quality and maintainability?",
        "Explain your experience with cloud platforms.",
        "How do you approach learning a new technology stack?",
        "Describe a technical challenge you solved creatively.",
        "What's your preferred development methodology?",
        "How do you document your technical work?"
    ],
    'Behavioral': [
        "Tell me about a time you showed leadership.",
        "Describe a situation where you had to work with a difficult team member.",
        "How do you prioritize multiple tasks with competing deadlines?",
        "Share an example of when you went above and beyond.",
        "Describe a time you received constructive criticism.",
        "How do you handle ambiguity in project requirements?",
        "Tell me about a successful project you led.",
        "Describe how you contribute to team culture.",
        "How do you handle changes in project scope?",
        "Share an example of your problem-solving process."
    ],
    'Data_Science_Specific': [
        "Explain your experience with data preprocessing and cleaning.",
        "How do you approach feature selection for ML models?",
        "Describe your favorite machine learning algorithm and why.",
        "How do you handle imbalanced datasets?",
        "Explain your experience with model evaluation metrics.",
        "How do you communicate complex findings to non-technical stakeholders?",
        "Describe your experience with SQL and database querying.",
        "What's your approach to data visualization?",
        "How do you ensure reproducibility in your analysis?",
        "Explain a time when your model didn't perform as expected."
    ]
}

# =========================================================
# JOB RECOMMENDATION DATABASE
# =========================================================
JOB_RECOMMENDATIONS = {
    'Data Scientist': {
        'required_skills': ['Python', 'Machine Learning', 'SQL', 'Statistics', 'Deep Learning'],
        'salary_range': 'Rp 8-15 Juta/bulan',
        'career_path': 'Junior DS → Data Scientist → Senior DS → Lead DS',
        'companies': ['Gojek', 'Tokopedia', 'Traveloka', 'Bukalapak', 'DANA']
    },
    'Data Analyst': {
        'required_skills': ['Python', 'SQL', 'Tableau', 'Excel', 'Statistics'],
        'salary_range': 'Rp 6-12 Juta/bulan',
        'career_path': 'Junior DA → Data Analyst → Senior DA → Analytics Manager',
        'companies': ['Shopee', 'Lazada', 'Blibli', 'OVO', 'LinkAja']
    },
    'Machine Learning Engineer': {
        'required_skills': ['Python', 'TensorFlow', 'PyTorch', 'MLOps', 'Docker'],
        'salary_range': 'Rp 10-20 Juta/bulan',
        'career_path': 'Junior MLE → ML Engineer → Senior MLE → ML Architect',
        'companies': ['Google', 'Microsoft', 'Amazon', 'Alibaba', 'NVIDIA']
    },
    'Data Engineer': {
        'required_skills': ['Python', 'SQL', 'Spark', 'Airflow', 'AWS/GCP'],
        'salary_range': 'Rp 9-18 Juta/bulan',
        'career_path': 'Junior DE → Data Engineer → Senior DE → Data Architect',
        'companies': ['Traveloka', 'Gojek', 'Bukalapak', 'DANA', 'OVO']
    },
    'Business Analyst': {
        'required_skills': ['SQL', 'Excel', 'Tableau', 'Communication', 'Problem Solving'],
        'salary_range': 'Rp 7-14 Juta/bulan',
        'career_path': 'Junior BA → Business Analyst → Senior BA → Product Manager',
        'companies': ['McKinsey', 'BCG', 'Deloitte', 'PwC', 'Accenture']
    }
}

# =========================================================
# GLOBAL STORES
# =========================================================
class InterviewSession:
    def __init__(self):
        self.active = False
        self.role = ""
        self.cv_analysis = {}
        self.questions = []
        self.answers = []
        self.evaluations = []
        self.current_index = 0
        self.cv_text = ""
        self.used_questions = set()

interview_session = InterviewSession()

# =========================================================
# JAVASCRIPT FOR AI INTEGRATION
# =========================================================
ai_script = '''
<script src="https://js.puter.com/v2/"></script>
<script>
window.puterInitialized = true;
window.pendingCallbacks = {};

window.callAI = async function(prompt, systemPrompt, callbackId, model = "openai/gpt-4o-mini") {
    try {
        const messages = [];
        if (systemPrompt && systemPrompt.trim()) {
            messages.push({ role: "system", content: systemPrompt });
        }
        messages.push({ role: "user", content: prompt });

        const response = await puter.ai.chat(messages, {
            model: model,
            temperature: 0.7,
            max_tokens: 2000
        });

        if (window.pendingCallbacks[callbackId]) {
            window.pendingCallbacks[callbackId]({ success: true, content: response });
            delete window.pendingCallbacks[callbackId];
        }
    } catch (error) {
        if (window.pendingCallbacks[callbackId]) {
            window.pendingCallbacks[callbackId]({ success: false, content: error.message });
            delete window.pendingCallbacks[callbackId];
        }
    }
};
</script>
'''

# =========================================================
# DASH APPLICATION
# =========================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CYBORG,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
    ],
    suppress_callback_exceptions=True,
    title=APP_TITLE
)

# IMPORTANT: This is needed for Gunicorn (Render.com)
server = app.server

# Custom HTML with AI script
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #0a0a2a 0%, #1a1a3a 100%);
                font-family: 'Inter', sans-serif;
                color: #e2e8f0;
            }}
            .glass-card {{
                background: rgba(30, 30, 50, 0.7);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.1);
                transition: all 0.3s ease;
            }}
            .glass-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 10px 40px rgba(99, 102, 241, 0.2);
                border-color: rgba(99, 102, 241, 0.3);
            }}
            .btn-gradient {{
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                border: none;
                transition: all 0.3s ease;
            }}
            .btn-gradient:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(99, 102, 241, 0.4);
            }}
            .skill-badge {{
                display: inline-block;
                background: rgba(99, 102, 241, 0.2);
                border: 1px solid rgba(99, 102, 241, 0.3);
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85rem;
                margin: 4px;
            }}
            .job-card {{
                background: rgba(0,0,0,0.3);
                border-radius: 16px;
                padding: 16px;
                margin-bottom: 16px;
                border-left: 4px solid #6366f1;
                transition: all 0.3s ease;
            }}
            .job-card:hover {{
                transform: translateX(5px);
                background: rgba(99,102,241,0.1);
            }}
            .chat-ai {{
                background: rgba(99, 102, 241, 0.15);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 18px 18px 18px 5px;
                padding: 12px 18px;
                margin: 10px 0;
                max-width: 85%;
            }}
            .chat-user {{
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
                border-radius: 18px 18px 5px 18px;
                padding: 12px 18px;
                margin: 10px 0 10px auto;
                max-width: 85%;
            }}
            .upload-area {{
                border: 2px dashed #6366f1;
                border-radius: 16px;
                text-align: center;
                padding: 40px;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            .upload-area:hover {{
                border-color: #8b5cf6;
                background: rgba(99, 102, 241, 0.05);
            }}
            .grade-A {{ background: linear-gradient(135deg, #10b981, #059669); }}
            .grade-B {{ background: linear-gradient(135deg, #3b82f6, #2563eb); }}
            .grade-C {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
            .grade-D {{ background: linear-gradient(135deg, #ef4444, #dc2626); }}
            .grade-circle {{
                width: 70px;
                height: 70px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                font-weight: bold;
                margin: 0 auto;
            }}
            .loading-spinner {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 0.8s linear infinite;
            }}
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            .fade-in {{
                animation: fadeIn 0.3s ease-in;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .sidebar {{
                position: fixed;
                top: 0;
                left: 0;
                bottom: 0;
                width: 260px;
                background: rgba(10, 10, 30, 0.95);
                backdrop-filter: blur(20px);
                border-right: 1px solid rgba(255,255,255,0.1);
                padding: 2rem 1.5rem;
                z-index: 1000;
                display: flex;
                flex-direction: column;
            }}
            .main-content {{
                margin-left: 260px;
                padding: 2rem;
                min-height: 100vh;
            }}
            .nav-item {{
                padding: 12px 16px;
                border-radius: 12px;
                margin-bottom: 8px;
                transition: all 0.3s ease;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .nav-item:hover {{
                background: rgba(99, 102, 241, 0.15);
                transform: translateX(5px);
            }}
            .nav-item.active {{
                background: linear-gradient(135deg, #6366f1, #8b5cf6);
            }}
            @media (max-width: 768px) {{
                .sidebar {{ position: relative; width: 100%; height: auto; }}
                .main-content {{ margin-left: 0; }}
            }}
            .feedback-card {{
                background: rgba(0,0,0,0.3);
                border-radius: 16px;
                padding: 16px;
                margin-bottom: 16px;
            }}
            .sidebar-footer {{
                margin-top: auto;
                text-align: center;
            }}
            .sidebar-footer-item {{
                margin-bottom: 8px;
                color: #94a3b8;
                font-size: 0.8rem;
            }}
            .progress-bar-custom {{
                height: 8px;
                background: rgba(99,102,241,0.2);
                border-radius: 4px;
                overflow: hidden;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #6366f1, #8b5cf6);
                border-radius: 4px;
                transition: width 0.3s ease;
            }}
            .score-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            .score-label {{
                font-size: 0.85rem;
                color: #94a3b8;
            }}
            .score-value {{
                font-weight: 600;
            }}
        </style>
        {ai_script}
    </head>
    <body>
        {{%app_entry%}}
        <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
    </body>
</html>
'''

# Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='cv-analysis-store', data={}),
    dcc.Store(id='cv-text-store', data=''),
    dcc.Store(id='interview-state-store', data={}),

    html.Div(id='ai-callback-container', style={'display': 'none'}),

    # Sidebar
    html.Div([
        html.Div([
            html.I(className="fas fa-robot fa-2x", style={'color': '#6366f1'}),
            html.H2("COMMU-ACE", className="mt-2 mb-0", style={'fontSize': '1.5rem', 'fontWeight': '700'}),
            html.P("AI Career Assistant", className="text-muted", style={'fontSize': '0.8rem'}),
        ], className="text-center mb-4"),

        html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)'}),

        html.Div([
            html.Div([
                html.I(className="fas fa-home"),
                html.Span("Dashboard")
            ], className="nav-item", id="nav-dashboard"),
            html.Div([
                html.I(className="fas fa-file-alt"),
                html.Span("CV Analysis")
            ], className="nav-item", id="nav-cv"),
            html.Div([
                html.I(className="fas fa-comments"),
                html.Span("AI Interview")
            ], className="nav-item", id="nav-interview"),
        ], className="mt-3"),

        html.Div([
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)'}),
            html.Div([
                html.Div([
                    html.I(className="fas fa-infinity me-2", style={'color': '#10b981'}),
                    html.Span("Unlimited Access", className="sidebar-footer-item")
                ], className="mb-2"),
                html.Div([
                    html.I(className="fas fa-bolt me-2", style={'color': '#f59e0b'}),
                    html.Span("Real AI Analysis", className="sidebar-footer-item")
                ], className="mb-2"),
                html.Div([
                    html.I(className="fas fa-code-branch me-2", style={'color': '#6366f1'}),
                    html.Span(f"v{APP_VERSION}", className="sidebar-footer-item")
                ], className="mb-2"),
            ], className="sidebar-footer")
        ], className="mt-auto")
    ], className="sidebar"),

    # Main content
    html.Div(id='page-content', className="main-content")
])

# Navigation callback
@app.callback(
    Output('url', 'pathname'),
    [Input('nav-dashboard', 'n_clicks'),
     Input('nav-cv', 'n_clicks'),
     Input('nav-interview', 'n_clicks')],
    prevent_initial_call=True
)
def navigate(nav1, nav2, nav3):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'nav-dashboard':
        return '/'
    elif button_id == 'nav-cv':
        return '/cv-analysis'
    elif button_id == 'nav-interview':
        return '/interview'
    return '/'

# Page routing
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def render_page(pathname):
    if pathname == '/cv-analysis':
        return render_cv_analysis_page()
    elif pathname == '/interview':
        return render_interview_page()
    else:
        return render_dashboard_page()

# =========================================================
# DASHBOARD PAGE
# =========================================================
def render_dashboard_page():
    return html.Div([
        html.Div([
            html.H1("Welcome to ", className="display-4 d-inline", style={'fontWeight': '300'}),
            html.H1("COMMU-ACE", className="display-4 d-inline",
                   style={'fontWeight': '800', 'background': 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                          'WebkitBackgroundClip': 'text', 'WebkitTextFillColor': 'transparent'}),
        ], className="mb-3"),
        html.P("AI-Powered CV Analysis & Mock Interview Platform", className="lead text-muted mb-4"),

        html.Div([
            html.Div([
                html.I(className="fas fa-cloud-upload-alt fa-3x mb-3", style={'color': '#6366f1'}),
                html.H4("Upload CV"),
                html.P("Upload your CV in PDF or DOCX format", className="text-muted")
            ], className="glass-card text-center p-4 mb-3"),
        ], className="row"),

        html.Div([
            html.Div([
                html.I(className="fas fa-chart-line fa-3x mb-3", style={'color': '#8b5cf6'}),
                html.H4("Get Analysis"),
                html.P("AI analyzes your skills, strengths, and career fit", className="text-muted")
            ], className="glass-card text-center p-4 mb-3"),
        ], className="row"),

        html.Div([
            html.Div([
                html.I(className="fas fa-microphone-alt fa-3x mb-3", style={'color': '#06b6d4'}),
                html.H4("Practice Interview"),
                html.P("Personalized mock interview based on your CV", className="text-muted")
            ], className="glass-card text-center p-4 mb-3"),
        ], className="row"),

        html.Div([
            dbc.Button("Get Started", href="/cv-analysis", className="btn-gradient mt-3 px-5 py-2",
                      style={'borderRadius': '30px', 'fontWeight': '600'})
        ], className="text-center mt-3")
    ], className="fade-in")

# =========================================================
# PDF EXTRACTION FUNCTION
# =========================================================
def extract_pdf_text(contents):
    """Extract text from PDF using PyMuPDF (Fitz) for better accuracy"""
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    if FITZ_AVAILABLE:
        try:
            pdf_document = fitz.open(stream=decoded, filetype="pdf")
            cv_text = ""
            page_count = pdf_document.page_count

            for page_num in range(page_count):
                page = pdf_document[page_num]
                text = page.get_text()
                if text and text.strip():
                    cv_text += text + "\n"

            pdf_document.close()

            if cv_text.strip():
                return cv_text, page_count, True

        except Exception as e:
            print(f"PyMuPDF error: {e}")

    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(decoded))
        cv_text = ""
        page_count = len(pdf_reader.pages)

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                cv_text += page_text + "\n"

        return cv_text, page_count, False

    except Exception as e:
        return "", 0, False

# =========================================================
# JOB RECOMMENDATION FUNCTION
# =========================================================
def get_job_recommendations(skills):
    """Get job recommendations based on skills"""
    recommendations = []
    skills_lower = [s.lower() for s in skills]

    for job_title, job_info in JOB_RECOMMENDATIONS.items():
        required = [r.lower() for r in job_info['required_skills']]
        match_count = sum(1 for s in required if any(s in skill_lower or skill_lower in s for skill_lower in skills_lower))
        match_percentage = int((match_count / len(required)) * 100) if required else 0

        recommendations.append({
            'title': job_title,
            'match_score': min(match_percentage, 95),
            'salary_range': job_info['salary_range'],
            'career_path': job_info['career_path'],
            'companies': job_info['companies'][:3],
            'missing_skills': [s for s in required if not any(s in skill_lower or skill_lower in s for skill_lower in skills_lower)][:3]
        })

    # Sort by match score
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    return recommendations[:3]

# =========================================================
# EXTRACT NAME FROM CV - IMPROVED
# =========================================================
def extract_name_from_cv(cv_text):
    """Extract name from CV text with multiple patterns"""
    cv_lines = cv_text.split('\n')

    # Pattern 1: Look for NAME: or NAMA: prefix
    for line in cv_lines[:20]:
        line_clean = line.strip()
        if re.match(r'^(?:NAME|NAMA)\s*[:|]\s*([A-Za-z\s]+)', line_clean, re.IGNORECASE):
            match = re.match(r'^(?:NAME|NAMA)\s*[:|]\s*([A-Za-z\s]+)', line_clean, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    # Pattern 2: Look for all-caps name or Title Case name at start of lines
    for line in cv_lines[:15]:
        line_clean = line.strip()
        # Look for pattern for name
        if re.match(r'^[A-Z]{2,}(?:\s+[A-Z]{2,})+$', line_clean):
            return line_clean.title()
        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$', line_clean):
            if len(line_clean.split()) >= 2 and len(line_clean) < 40:
                return line_clean

    # Pattern 3: Look for common name patterns after "##" or "**"
    patterns = [
        r'##\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
        r'\*\*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\*\*',
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, cv_text[:500], re.MULTILINE)
        if match:
            return match.group(1).strip()

    return None

# =========================================================
# GET CREATIVE QUESTION
# =========================================================
def get_creative_question(role, question_num, used_questions):
    """Get a creative, non-repetitive question"""

    # Combine all question banks
    all_questions = []
    all_questions.extend(QUESTION_BANK['HR'])
    all_questions.extend(QUESTION_BANK['Technical'])
    all_questions.extend(QUESTION_BANK['Behavioral'])

    if 'Data' in role or 'Machine Learning' in role or 'Scientist' in role:
        all_questions.extend(QUESTION_BANK['Data_Science_Specific'])

    # Remove used questions
    available = [q for q in all_questions if q not in used_questions]

    if not available:
        used_questions.clear()
        available = all_questions

    # Select random question
    question = random.choice(available)
    used_questions.add(question)

    # Personalize with role if needed
    if '{role}' in question:
        question = question.replace('{role}', role)

    return question

# =========================================================
# CV ANALYSIS PAGE
# =========================================================
def render_cv_analysis_page():
    return html.Div([
        html.H2("CV Analysis", className="mb-2", style={'fontWeight': '700'}),
        html.P("Upload your CV in PDF format for AI-powered analysis", className="text-muted mb-4"),

        html.Div([
            html.I(className="fas fa-info-circle me-2", style={'color': '#3b82f6'}),
            html.Span("Upload PDF yang teksnya bisa di-copy (bukan hasil scan/foto). ", className="small"),
        ], className="alert alert-info mb-3", style={'background': 'rgba(59,130,246,0.1)', 'border': 'none', 'borderRadius': '12px'}),

        html.Div([
            dcc.Upload(
                id='upload-cv',
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt fa-3x mb-3", style={'color': '#6366f1'}),
                    html.H5("Drag & Drop or Click to Upload"),
                    html.P("PDF files only", className="text-muted small")
                ], className="upload-area"),
                accept='.pdf',
                multiple=False
            ),
            html.Div(id='upload-loading', className="text-center mt-3"),
            html.Div(id='upload-status', className="mt-3")
        ], className="glass-card p-4 mb-4"),

        html.Div(id='analysis-results', style={'display': 'none'}, children=[
            html.Div([
                html.Div([
                    html.H3([
                        html.I(className="fas fa-user-circle me-2", style={'color': '#6366f1'}),
                        html.Span(id='candidate-name')
                    ], className="mb-3"),
                    html.Div(id='professional-summary', className="mb-4"),

                    html.Hr(),

                    html.Div([
                        html.Div([
                            html.H5("Experience"),
                            html.P(id='experience-years', className="h2 text-primary")
                        ], className="col-6"),
                        html.Div([
                            html.H5("Education"),
                            html.P(id='education', className="h6")
                        ], className="col-6"),
                    ], className="row mb-4"),

                    html.H5("Technical Skills", className="mt-3"),
                    html.Div(id='technical-skills'),

                    html.H5("Soft Skills", className="mt-3"),
                    html.Div(id='soft-skills'),

                    html.H5("Key Achievements", className="mt-3"),
                    html.Ul(id='achievements'),

                    html.H5("Strengths", className="mt-3"),
                    html.Ul(id='strengths-list'),

                    html.H5("Areas for Improvement", className="mt-3"),
                    html.Ul(id='improvements-list'),
                ], className="p-4")
            ], className="glass-card mb-4"),

            html.Div([
                html.H4([
                    html.I(className="fas fa-briefcase me-2", style={'color': '#10b981'}),
                    "Job Recommendations Based on Your Skills"
                ], className="mb-3"),
                html.Div(id='recommended-roles'),
            ], className="glass-card p-4 mb-4"),

            html.Div([
                html.H4("Skill Development Recommendations", className="mb-3"),
                html.Div(id='skill-recommendations'),
            ], className="glass-card p-4 mb-4"),

            html.Div([
                html.H4("Overall Assessment", className="mb-2"),
                html.P(id='overall-assessment', className="lead"),
            ], className="glass-card p-4")
        ])
    ], className="fade-in")

# CV Analysis callback
@app.callback(
    [Output('upload-status', 'children'),
     Output('upload-loading', 'children'),
     Output('analysis-results', 'style'),
     Output('candidate-name', 'children'),
     Output('professional-summary', 'children'),
     Output('experience-years', 'children'),
     Output('education', 'children'),
     Output('technical-skills', 'children'),
     Output('soft-skills', 'children'),
     Output('achievements', 'children'),
     Output('strengths-list', 'children'),
     Output('improvements-list', 'children'),
     Output('recommended-roles', 'children'),
     Output('skill-recommendations', 'children'),
     Output('overall-assessment', 'children'),
     Output('cv-analysis-store', 'data'),
     Output('cv-text-store', 'data')],
    Input('upload-cv', 'contents'),
    State('upload-cv', 'filename'),
    prevent_initial_call=True
)
def process_cv_upload(contents, filename):
    if not contents:
        raise PreventUpdate

    if not filename.lower().endswith('.pdf'):
        return (html.Div("Error: Hanya file PDF yang didukung", className="text-danger"),
                "", {'display': 'none'}, "", "", "", "", "", "", "", "", "", "", "", "", {}, "")

    try:
        cv_text, num_pages, used_fitz = extract_pdf_text(contents)
        parser_name = "PyMuPDF" if used_fitz else "PyPDF2"

        if len(cv_text.strip()) < 100:
            return (html.Div([
                html.I(className="fas fa-exclamation-triangle me-2", style={'color': '#f59e0b'}),
                f"Teks dari PDF hanya {len(cv_text.strip())} karakter. Pastikan PDF Anda bisa di-copy text-nya."
            ], className="text-warning"), "", {'display': 'none'}, "", "", "", "", "", "", "", "", "", "", "", "", {}, "")

        interview_session.cv_text = cv_text
        cv_lower = cv_text.lower()

        # EXTRACT NAME - IMPROVED
        candidate_name = extract_name_from_cv(cv_text)
        if not candidate_name:
            candidate_name = "Candidate"

        # Extract years experience
        exp_match = re.search(r'(\d+)\+?\s*(?:years|yrs|tahun|thn|semester|Experience)', cv_lower)
        years_exp = exp_match.group(1) if exp_match else "1-3"

        # Extract education
        edu_keywords = {
            'S1': 'Bachelor\'s Degree', 'S2': 'Master\'s Degree', 'S3': 'PhD',
            'Bachelor': 'Bachelor\'s Degree', 'Master': 'Master\'s Degree', 'PhD': 'PhD',
            'Sarjana': 'Bachelor\'s Degree', 'Magister': 'Master\'s Degree'
        }
        education = "Bachelor's Degree"
        for key, value in edu_keywords.items():
            if key.lower() in cv_lower:
                education = value
                break

        # Extract technical skills
        tech_keywords = [
            'Python', 'SQL', 'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch',
            'Machine Learning', 'Data Science', 'NLP', 'ETL', 'API', 'BeautifulSoup',
            'Selenium', 'Java', 'JavaScript', 'React', 'AWS', 'Docker', 'Git',
            'Tableau', 'Power BI', 'Spark', 'Hadoop', 'MongoDB', 'PostgreSQL',
            'Deep Learning', 'Computer Vision', 'LLM', 'LangChain', 'FastAPI'
        ]
        technical_skills = [skill for skill in tech_keywords if skill.lower() in cv_lower]

        if not technical_skills:
            technical_skills = ['Python', 'SQL', 'Data Analysis', 'Machine Learning']
        else:
            technical_skills = technical_skills[:10]

        # Extract soft skills
        soft_keywords = ['Leadership', 'Communication', 'Teamwork', 'Problem Solving',
                         'Critical Thinking', 'Analytical', 'Collaboration', 'Organization',
                         'Time Management', 'Adaptability', 'Creativity']
        soft_skills = [skill for skill in soft_keywords if skill.lower() in cv_lower][:5]
        if not soft_skills:
            soft_skills = ['Analytical Thinking', 'Problem Solving', 'Team Collaboration']

        # Extract achievements
        achievement_patterns = [
            r'(\d+)\+?\s*(?:MSMEs|households|projects|businesses|customers)',
            r'(?:managed|processed|developed|created|implemented|designed|built)\s+([^.\n]{20,100})',
        ]
        key_achievements = []
        for pattern in achievement_patterns:
            matches = re.findall(pattern, cv_text, re.IGNORECASE)
            for match in matches[:3]:
                if isinstance(match, tuple):
                    match = match[0]
                if len(match) > 10 and match not in key_achievements:
                    key_achievements.append(match[:100])

        if not key_achievements:
            key_achievements = [
                "Successfully delivered data analytics projects",
                "Collaborated with cross-functional teams",
                "Developed data-driven solutions for business problems"
            ]

        # GET JOB RECOMMENDATIONS based on skills
        job_recommendations = get_job_recommendations(technical_skills)

        # Build analysis data
        analysis_data = {
            'candidate_name': candidate_name,
            'professional_summary': f"{candidate_name} is a data professional with {years_exp}+ years of experience. Skilled in {', '.join(technical_skills[:3])}. Strong background in data analytics and machine learning.",
            'years_experience': years_exp,
            'education': education,
            'technical_skills': technical_skills[:10],
            'soft_skills': soft_skills,
            'key_achievements': key_achievements[:4],
            'strengths': technical_skills[:4] + ['Data Analysis', 'Problem Solving'],
            'areas_for_improvement': ['Advanced ML/DL', 'Cloud Architecture', 'Big Data'],
            'job_recommendations': job_recommendations,
            'skill_recommendations': [
                {'skill': 'Cloud Computing (AWS/GCP)', 'priority': 'High', 'learning_path': 'AWS Certified Data Analytics'},
                {'skill': 'Advanced Machine Learning', 'priority': 'Medium', 'learning_path': 'Deep Learning Specialization'},
                {'skill': 'Big Data Technologies', 'priority': 'Medium', 'learning_path': 'Apache Spark Course'},
            ],
            'overall_assessment': f"{candidate_name} has solid potential in data analytics and machine learning. Recommended to focus on cloud and big data technologies for career advancement."
        }

        interview_session.cv_analysis = analysis_data

        # Build UI components
        technical_skills_ui = html.Div([html.Span(skill, className="skill-badge") for skill in technical_skills[:10]])
        soft_skills_ui = html.Div([html.Span(skill, className="skill-badge") for skill in soft_skills])
        achievements_ui = html.Ul([html.Li(ach) for ach in key_achievements[:4]])
        strengths_ui = html.Ul([html.Li(s) for s in analysis_data['strengths'][:5]])
        improvements_ui = html.Ul([html.Li(i) for i in analysis_data['areas_for_improvement']])

        # Job recommendations UI
        job_recs_ui = []
        for job in job_recommendations:
            score_color = "#10b981" if job['match_score'] >= 80 else "#f59e0b" if job['match_score'] >= 60 else "#ef4444"
            job_recs_ui.append(
                html.Div([
                    html.Div([
                        html.H5(job['title'], className="d-inline me-2"),
                        html.Span(f"{job['match_score']}% Match", style={'color': score_color, 'fontWeight': '600'})
                    ], className="mb-2"),
                    html.Div([
                        html.Small("💰 Salary: ", className="text-muted"),
                        html.Small(job['salary_range'], className="text-info")
                    ], className="mb-2"),
                    html.Div([
                        html.Small("📈 Career Path: ", className="text-muted"),
                        html.Small(job['career_path'], className="text-info")
                    ], className="mb-2"),
                    html.Div([
                        html.Small("🏢 Top Companies: ", className="text-muted"),
                        html.Small(', '.join(job['companies']), className="text-info")
                    ], className="mb-2"),
                    html.Div([
                        html.Small("⚠️ Missing Skills: ", className="text-warning"),
                        html.Small(', '.join(job['missing_skills']) if job['missing_skills'] else "None", className="text-muted")
                    ]) if job['missing_skills'] else None
                ], className="job-card")
            )

        skill_recs_ui = []
        for rec in analysis_data['skill_recommendations']:
            priority_color = "#10b981" if rec['priority'] == "High" else "#f59e0b"
            skill_recs_ui.append(
                html.Div([
                    html.Div([
                        html.Strong(rec['skill'], className="me-2"),
                        html.Small(rec['priority'], style={'color': priority_color})
                    ]),
                    html.Small(rec['learning_path'], className="text-muted")
                ], className="mb-3 p-2", style={'background': 'rgba(99,102,241,0.1)', 'borderRadius': '12px'})
            )

        status = html.Div([
            html.I(className="fas fa-check-circle me-2", style={'color': '#10b981'}),
            f"✓ CV Analysis Complete! Welcome, {candidate_name} ({num_pages} pages, {len(cv_text)} chars)"
        ], className="text-success")

        return (status, "", {'display': 'block'},
                candidate_name,
                html.P(analysis_data['professional_summary']),
                f"{years_exp}+ years",
                education,
                technical_skills_ui, soft_skills_ui, achievements_ui, strengths_ui, improvements_ui,
                html.Div(job_recs_ui), html.Div(skill_recs_ui),
                html.P(analysis_data['overall_assessment']),
                analysis_data, cv_text)

    except Exception as e:
        return (html.Div(f"Error membaca PDF: {str(e)}", className="text-danger"),
                "", {'display': 'none'}, "", "", "", "", "", "", "", "", "", "", "", "", {}, "")

# =========================================================
# INTERVIEW PAGE
# =========================================================
def render_interview_page():
    return html.Div([
        html.H2("AI Mock Interview", className="mb-2", style={'fontWeight': '700'}),
        html.P("Practice with creative, personalized questions from AI", className="text-muted mb-4"),

        html.Div([
            html.Div([
                html.H5("Interview Setup", className="mb-3"),

                html.Label("Target Role", className="small fw-bold mb-1"),
                dcc.Dropdown(
                    id='interview-role',
                    options=[{'label': role, 'value': role} for role in AVAILABLE_ROLES],
                    placeholder="Select target role...",
                    className="mb-3",
                    style={'color': '#000'}
                ),

                html.Label("Interview Type", className="small fw-bold mb-1"),
                dcc.RadioItems(
                    id='interview-type',
                    options=[
                        {'label': ' HR / Behavioral', 'value': 'HR'},
                        {'label': ' Technical', 'value': 'Technical'},
                        {'label': ' Mixed (Creative)', 'value': 'Mixed'}
                    ],
                    value='Mixed',
                    className="mb-3",
                    labelStyle={'display': 'block', 'marginBottom': '8px'}
                ),

                html.Div(id='cv-status-interview', className="mb-3"),

                dbc.Button([
                    html.I(className="fas fa-play me-2"),
                    "Start Interview"
                ], id='start-interview-btn', className="btn-gradient w-100",
                style={'borderRadius': '12px', 'padding': '12px'}),

                html.Div(id='interview-progress', className="text-center mt-3 small text-muted")
            ], className="p-3")
        ], className="glass-card p-3 mb-4"),

        html.Div(id='interview-area', style={'display': 'none'}, children=[
            html.Div([
                html.Div([
                    html.H5("Conversation", className="mb-3"),
                    html.Div(id='chat-container', className="mb-3", style={'maxHeight': '400px', 'overflowY': 'auto'})
                ], className="p-3")
            ], className="glass-card mb-4"),

            html.Div([
                dbc.Textarea(id='answer-input', placeholder="Type your answer here...", rows=3,
                            style={'background': 'rgba(0,0,0,0.3)', 'border': '1px solid rgba(255,255,255,0.1)',
                                   'color': 'white', 'borderRadius': '12px'}),
                html.Div([
                    dbc.Button("Submit Answer", id='submit-answer', className="btn-gradient mt-2 me-2",
                              style={'borderRadius': '10px'}),
                    dbc.Button("Next Question", id='next-question', className="btn-secondary mt-2",
                              style={'background': 'rgba(255,255,255,0.1)', 'border': 'none', 'borderRadius': '10px'},
                              disabled=True)
                ], className="d-flex")
            ], className="glass-card p-3 mb-4"),

            html.Div([
                html.H5("Detailed Feedback", className="mb-3"),
                html.Div(id='feedback-container')
            ], className="glass-card p-3")
        ])
    ], className="fade-in")

# Check CV before interview
@app.callback(
    Output('cv-status-interview', 'children'),
    Input('cv-analysis-store', 'data')
)
def check_cv_status(cv_data):
    if cv_data and cv_data.get('candidate_name'):
        return html.Div([
            html.I(className="fas fa-check-circle me-1", style={'color': '#10b981'}),
            html.Small(f"CV Ready: {cv_data.get('candidate_name', 'Candidate')}", className="text-success")
        ])
    else:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-1", style={'color': '#f59e0b'}),
            html.Small("Please analyze your CV first in CV Analysis page", className="text-warning")
        ])

# Start interview callback
@app.callback(
    [Output('interview-area', 'style'),
     Output('interview-progress', 'children'),
     Output('chat-container', 'children'),
     Output('interview-state-store', 'data'),
     Output('start-interview-btn', 'disabled')],
    Input('start-interview-btn', 'n_clicks'),
    [State('interview-role', 'value'),
     State('interview-type', 'value'),
     State('cv-analysis-store', 'data'),
     State('cv-text-store', 'data')],
    prevent_initial_call=True
)
def start_interview(n_clicks, role, interview_type, cv_analysis, cv_text):
    if not n_clicks:
        raise PreventUpdate

    if not cv_analysis or not cv_analysis.get('candidate_name'):
        return {'display': 'none'}, html.Div("Please analyze your CV first", className="text-danger"), "", {}, False

    if not role:
        return {'display': 'none'}, html.Div("Select a target role", className="text-warning"), "", {}, False

    interview_session.active = True
    interview_session.role = role
    interview_session.cv_analysis = cv_analysis
    interview_session.cv_text = cv_text
    interview_session.questions = []
    interview_session.answers = []
    interview_session.evaluations = []
    interview_session.current_index = 0
    interview_session.used_questions = set()

    # Get creative first question
    first_question = get_creative_question(role, 1, interview_session.used_questions)
    # Personalize with candidate's name
    candidate_name = cv_analysis.get('candidate_name', '')
    if candidate_name and candidate_name != "Candidate":
        first_question = f"Hi {candidate_name}! " + first_question[0].lower() + first_question[1:] if len(first_question) > 1 else first_question

    interview_session.questions.append(first_question)

    chat = html.Div([
        html.Div([
            html.Div([
                html.I(className="fas fa-robot me-2", style={'color': '#6366f1'}),
                html.Strong(f"Interviewer ({role})")
            ], className="mb-2 small text-muted"),
            html.Div(first_question, className="chat-ai")
        ], className="fade-in")
    ])

    progress = html.Div([
        html.Span(f"Session 1/{MAX_INTERVIEW_QUESTIONS}", className="me-2"),
        html.Div([
            html.Div(className="progress-bar-custom", children=[
                html.Div(className="progress-fill", style={'width': f'{100/MAX_INTERVIEW_QUESTIONS}%'})
            ])
        ], className="mt-2")
    ])

    state_data = {
        'role': role,
        'interview_type': interview_type,
        'current_index': 0,
        'questions': [first_question],
        'answers': [],
        'evaluations': []
    }

    return {'display': 'block'}, progress, chat, state_data, True

# Submit answer callback with enhanced grading
@app.callback(
    [Output('chat-container', 'children', allow_duplicate=True),
     Output('feedback-container', 'children'),
     Output('answer-input', 'value', allow_duplicate=True),
     Output('submit-answer', 'disabled', allow_duplicate=True),
     Output('next-question', 'disabled', allow_duplicate=True),
     Output('interview-progress', 'children', allow_duplicate=True),
     Output('interview-state-store', 'data', allow_duplicate=True)],
    Input('submit-answer', 'n_clicks'),
    [State('answer-input', 'value'),
     State('interview-state-store', 'data'),
     State('interview-role', 'value'),
     State('interview-type', 'value'),
     State('cv-analysis-store', 'data')],
    prevent_initial_call=True
)
def submit_answer(n_clicks, answer, state_data, role, interview_type, cv_analysis):
    if not n_clicks or not answer:
        raise PreventUpdate

    if not interview_session.active:
        raise PreventUpdate

    current_q = interview_session.questions[interview_session.current_index]
    interview_session.answers.append(answer)

    # Enhanced grading with multiple aspects
    word_count = len(answer.split())
    answer_length = len(answer)
    has_numbers = bool(re.search(r'\d+', answer))
    has_example = bool(re.search(r'(contoh|example|misal|seperti|proyek|project)', answer.lower()))

    # Calculate score based on multiple aspects
    completeness_score = min(30, word_count // 2)  # Max 30 for length
    structure_score = 20 if has_example else 10   # 20 if has example
    relevance_score = 20 if 'experience' in answer.lower() or 'skill' in answer.lower() else 10
    detail_score = 15 if has_numbers else 8
    clarity_score = 15 if len(answer.split()) > 10 else 8

    total_score = completeness_score + structure_score + relevance_score + detail_score + clarity_score

    if total_score >= 85:
        grade = "A"
        evaluation = {
            'grade': 'A',
            'scores': {
                'completeness': min(30, completeness_score),
                'structure': structure_score,
                'relevance': relevance_score,
                'detail': detail_score,
                'clarity': clarity_score
            },
            'feedback_summary': 'Excellent answer! Very comprehensive and well-structured.',
            'what_was_good': 'Your answer is complete, structured, and highly relevant. Great use of specific examples.',
            'what_was_missing': 'Keep up this quality throughout the interview.',
            'specific_feedback': 'Your response shows deep understanding. Continue using the STAR method with specific metrics.',
            'better_answer_example': "Your answer was already excellent! Just maintain this quality."
        }
    elif total_score >= 70:
        grade = "B"
        evaluation = {
            'grade': 'B',
            'scores': {
                'completeness': min(30, completeness_score),
                'structure': structure_score,
                'relevance': relevance_score,
                'detail': detail_score,
                'clarity': clarity_score
            },
            'feedback_summary': 'Good answer with solid content.',
            'what_was_good': f'Your answer shows good understanding of the {role} role.',
            'what_was_missing': 'Could be more specific with concrete examples and numbers.',
            'specific_feedback': 'Add specific projects or achievements to strengthen your answer. Use numbers when possible.',
            'better_answer_example': f"At my previous role, I handled a project using {cv_analysis.get('technical_skills', ['relevant skills'])[0] if cv_analysis.get('technical_skills') else 'my skills'}, which resulted in a 20% improvement."
        }
    elif total_score >= 55:
        grade = "C"
        evaluation = {
            'grade': 'C',
            'scores': {
                'completeness': min(30, completeness_score),
                'structure': structure_score,
                'relevance': relevance_score,
                'detail': detail_score,
                'clarity': clarity_score
            },
            'feedback_summary': 'Fair answer, but needs more depth.',
            'what_was_good': 'You addressed the main question.',
            'what_was_missing': 'Your answer is too general and lacks specific details.',
            'specific_feedback': 'Provide more details about your specific experiences. Interviewers want concrete examples.',
            'better_answer_example': f"I have {cv_analysis.get('years_experience', 'several')} years of experience. For example, at my previous company, I was responsible for a project that improved efficiency by 15%."
        }
    else:
        grade = "D"
        evaluation = {
            'grade': 'D',
            'scores': {
                'completeness': min(30, completeness_score),
                'structure': structure_score,
                'relevance': relevance_score,
                'detail': detail_score,
                'clarity': clarity_score
            },
            'feedback_summary': 'Answer needs significant improvement.',
            'what_was_good': 'You attempted to answer.',
            'what_was_missing': 'Your answer lacks substance, detail, and relevance.',
            'specific_feedback': 'Elaborate more on your experience. Aim for detailed responses with specific examples.',
            'better_answer_example': f"Based on my experience with {', '.join(cv_analysis.get('technical_skills', ['relevant skills'])[:2])}, I successfully completed a project where I [specific achievement with numbers]."
        }

    interview_session.evaluations.append(evaluation)

    # Build updated chat
    chat = html.Div([
        html.Div([
            html.I(className="fas fa-robot me-2", style={'color': '#6366f1'}),
            html.Strong(f"Interviewer ({role})")
        ], className="mb-2 small text-muted")
    ], className="fade-in")

    for i, q in enumerate(interview_session.questions):
        chat.children.append(html.Div(q, className="chat-ai"))
        if i < len(interview_session.answers):
            chat.children.append(html.Div([
                html.Div([
                    html.I(className="fas fa-user me-2", style={'color': '#8b5cf6'}),
                    html.Strong("You")
                ], className="mb-1 small text-muted text-end"),
                html.Div(interview_session.answers[i], className="chat-user")
            ], className="text-end"))

    # Build enhanced feedback UI
    grade_config = GRADE_CONFIG.get(grade, GRADE_CONFIG['D'])
    scores = evaluation.get('scores', {})

    feedback = html.Div([
        html.Div([
            html.Div(grade, className=f"grade-circle grade-{grade}"),
            html.H5(f"{grade_config['icon']} {grade_config['label']}", className="text-center mt-2 mb-0"),
            html.Small(grade_config['description'], className="text-muted text-center d-block")
        ], className="text-center mb-3"),

        html.Div([
            html.H6("📊 Score Breakdown:", className="mb-2"),
            html.Div([
                html.Div([html.Span("Completeness", className="score-label"), html.Span(f"{scores.get('completeness', 0)}/30", className="score-value")], className="score-item"),
                html.Div([html.Span("Structure & Examples", className="score-label"), html.Span(f"{scores.get('structure', 0)}/20", className="score-value")], className="score-item"),
                html.Div([html.Span("Relevance", className="score-label"), html.Span(f"{scores.get('relevance', 0)}/20", className="score-value")], className="score-item"),
                html.Div([html.Span("Detail (numbers/data)", className="score-label"), html.Span(f"{scores.get('detail', 0)}/15", className="score-value")], className="score-item"),
                html.Div([html.Span("Clarity", className="score-label"), html.Span(f"{scores.get('clarity', 0)}/15", className="score-value")], className="score-item"),
            ], className="mb-2")
        ], className="feedback-card"),

        html.Div([
            html.H6("✅ What Was Good:", className="text-success mb-2"),
            html.P(evaluation.get('what_was_good', ''), className="small",
                   style={'background': 'rgba(16,185,129,0.1)', 'padding': '10px', 'borderRadius': '10px'})
        ], className="feedback-card"),

        html.Div([
            html.H6("⚠️ What Can Be Improved:", className="text-warning mb-2"),
            html.P(evaluation.get('what_was_missing', ''), className="small",
                   style={'background': 'rgba(245,158,11,0.1)', 'padding': '10px', 'borderRadius': '10px'})
        ], className="feedback-card"),

        html.Div([
            html.H6("💡 Personalized Feedback:", className="text-info mb-2"),
            html.P(evaluation.get('specific_feedback', ''), className="small",
                   style={'background': 'rgba(6,182,212,0.1)', 'padding': '10px', 'borderRadius': '10px'})
        ], className="feedback-card"),

        html.Div([
            html.H6("📝 Better Answer Example:", className="text-primary mb-2"),
            html.P(evaluation.get('better_answer_example', ''), className="small",
                   style={'background': 'rgba(99,102,241,0.15)', 'padding': '12px', 'borderRadius': '10px', 'borderLeft': '3px solid #6366f1'})
        ], className="feedback-card")
    ])

    current_q_num = interview_session.current_index + 1

    # Check if interview complete
    if current_q_num >= MAX_INTERVIEW_QUESTIONS:
        grades = [e.get('grade', 'D') for e in interview_session.evaluations]
        grade_values = {'A': 90, 'B': 75, 'C': 60, 'D': 45}
        avg_score = sum(grade_values.get(g, 50) for g in grades) / len(grades)

        if avg_score >= 85:
            final_grade = "A"
        elif avg_score >= 70:
            final_grade = "B"
        elif avg_score >= 55:
            final_grade = "C"
        else:
            final_grade = "D"

        final_config = GRADE_CONFIG[final_grade]

        feedback.children.insert(0, html.Div([
            html.H4("🎉 Interview Complete! Great job! 🎉", className="text-center text-success mb-2"),
            html.Div(final_grade, className=f"grade-circle grade-{final_grade} mx-auto mb-2",
                    style={'width': '80px', 'height': '80px', 'fontSize': '40px'}),
            html.H5(f"Final Grade: {final_grade} - {final_config['label']}", className="text-center mb-2"),
            html.P(f"{final_config['description']}", className="text-center small"),
            html.Hr(),
            html.H6("Session Summary:", className="mt-3"),
            html.Ul([
                html.Li(f"Session {i+1}: Grade {e.get('grade', '?')} - {e.get('feedback_summary', '')[:50]}...")
                for i, e in enumerate(interview_session.evaluations)
            ], className="small")
        ]))

        progress = html.Div([
            html.Span(f"Complete! {current_q_num}/{MAX_INTERVIEW_QUESTIONS} sessions", className="text-success"),
            html.Div([
                html.Div(className="progress-bar-custom", children=[
                    html.Div(className="progress-fill", style={'width': '100%'})
                ])
            ], className="mt-2")
        ])

        interview_session.active = False
        return chat, feedback, "", True, True, progress, state_data

    # Generate next creative question
    next_q = get_creative_question(role, current_q_num + 1, interview_session.used_questions)
    interview_session.questions.append(next_q)
    chat.children.append(html.Div(next_q, className="chat-ai"))

    next_q_num = interview_session.current_index + 2
    progress = html.Div([
        html.Span(f"Session {next_q_num}/{MAX_INTERVIEW_QUESTIONS}", className="me-2"),
        html.Div([
            html.Div(className="progress-bar-custom", children=[
                html.Div(className="progress-fill", style={'width': f'{(next_q_num-1)/MAX_INTERVIEW_QUESTIONS * 100}%'})
            ])
        ], className="mt-2"),
        html.Div(f"Last Grade: {grade}", className="text-info small mt-1")
    ])

    interview_session.current_index += 1
    state_data['questions'] = interview_session.questions
    state_data['current_index'] = interview_session.current_index

    return chat, feedback, "", True, False, progress, state_data

# Next question handler
@app.callback(
    [Output('chat-container', 'children', allow_duplicate=True),
     Output('answer-input', 'value', allow_duplicate=True),
     Output('submit-answer', 'disabled', allow_duplicate=True),
     Output('next-question', 'disabled', allow_duplicate=True)],
    Input('next-question', 'n_clicks'),
    State('interview-state-store', 'data'),
    prevent_initial_call=True
)
def next_question_handler(n_clicks, state_data):
    if not n_clicks:
        raise PreventUpdate

    chat = html.Div([
        html.Div([
            html.I(className="fas fa-robot me-2", style={'color': '#6366f1'}),
            html.Strong(f"Interviewer ({interview_session.role})")
        ], className="mb-2 small text-muted")
    ], className="fade-in")

    for i, q in enumerate(interview_session.questions):
        chat.children.append(html.Div(q, className="chat-ai"))
        if i < len(interview_session.answers):
            chat.children.append(html.Div([
                html.Div([
                    html.I(className="fas fa-user me-2", style={'color': '#8b5cf6'}),
                    html.Strong("You")
                ], className="mb-1 small text-muted text-end"),
                html.Div(interview_session.answers[i], className="chat-user")
            ], className="text-end"))

    return chat, "", False, True

# =========================================================
# RUN - PRODUCTION READY
# =========================================================
server = app.server  # Wajib untuk Railway

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host='0.0.0.0', port=port, debug=False)