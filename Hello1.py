import streamlit as st
import json
import os
from model import get_output
import time

# Page configuration
st.set_page_config(page_title="Synthify", layout="centered")

# Load templates from a JSON file (if any)
def load_templates():
    try:
        with open("templates.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save templates to a JSON file (if any)
def save_templates(templates):
    with open("templates.json", "w") as f:
        json.dump(templates, f)

# Initialize session state variables
def initialize_session():
    session_defaults = {
        "uploaded_file": None,
        "custom_topic": None,
        "page": "upload",
        "response": None,
        "mock_test_questions": [],
        "user_answers": {},
        "mock_test_completed": False,
        "analysis_results": {},
        "start_time": None,
        "time_taken": None,
        "leaderboard": []
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

# Process user input (uploaded file or custom topic)
def process_input(uploaded_file, custom_topic):
    if uploaded_file:
        file_path = f"temp/{uploaded_file.name}"
        os.makedirs("temp", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file = file_path

    if custom_topic:
        st.session_state.custom_topic = custom_topic

    if uploaded_file or custom_topic:
        st.session_state.page = "options"
        st.experimental_rerun()
    else:
        st.warning("⚠️ Please upload a file or enter a topic!")

# Home page (upload file or enter topic)
if st.session_state.page == "upload":
    st.title("📚 Synthify: AI Study Assistant")
    st.subheader("Upload your study material or enter a topic")
    uploaded_file = st.file_uploader("Choose a PDF or Text file", type=["pdf", "txt"])
    custom_topic = st.text_area("Or enter a study topic manually:")
    if st.button("Next ➡️"):
        process_input(uploaded_file, custom_topic)

# Options page (choose action)
elif st.session_state.page == "options":
    st.title("📖 Study Assistant")
    st.subheader("Choose an action:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📌 Extract Important Topics"):
            st.session_state.page = "topics"
            st.experimental_rerun()
        if st.button("📝 Generate Important Questions"):
            st.session_state.page = "questions"
            st.experimental_rerun()
    with col2:
        if st.button("🎯 Generate Mock Tests"):
            st.session_state.page = "mock_tests"
            st.experimental_rerun()
        if st.button("📊 Performance Analysis"):
            st.session_state.page = "analysis"
            st.experimental_rerun()
    if st.button("🏠 Back to Home"):
        st.session_state.page = "upload"
        st.experimental_rerun()

# Generate mock test questions
JSON_FILE = "mock_test_questions.json"

def load_questions():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return []

def save_analysis(results):
    with open("analysis_results.json", "w") as f:
        json.dump(results, f, indent=4)

def generate_mock_test():
    topic = st.session_state.custom_topic or st.session_state.uploaded_file
    if not topic:
        st.warning("⚠️ Please upload a file or enter a topic first!")
        return
    
    prompt = f"Generate a mock test with 5 MCQs and 3 short-answer questions based on: {topic}"
    questions = get_output(prompt)
    
    try:
        questions_data = json.loads(questions)
        with open(JSON_FILE, "w") as f:
            json.dump(questions_data, f, indent=4)
        
        st.session_state.mock_test_questions = questions_data
        st.session_state.start_time = time.time()
        st.session_state.page = "mock_tests"
        st.experimental_rerun()
    except json.JSONDecodeError:
        st.error("Invalid JSON response from AI. Please check the output format.")

def analyze_performance():
    if not st.session_state.mock_test_completed:
        st.warning("⚠️ Complete the mock test first!")
        return
    
    if st.session_state.start_time is None:
        st.session_state.time_taken = 0  # Default to 0 if start_time is missing
    else:
        st.session_state.time_taken = round(time.time() - st.session_state.start_time, 2)

    correct_mcqs = sum(1 for q in st.session_state.mock_test_questions 
                       if q["type"] == "MCQ" and 
                       st.session_state.user_answers.get(q["question"]) == q["answer"])
    
    total_mcqs = sum(1 for q in st.session_state.mock_test_questions if q["type"] == "MCQ")

    descriptive_feedback = []
    for q in st.session_state.mock_test_questions:
        if q["type"] == "Short Answer":
            user_answer = st.session_state.user_answers.get(q["question"], "").lower()
            keywords = q.get("keywords", [])
            matched_keywords = [kw for kw in keywords if kw in user_answer]
            descriptive_feedback.append((q["question"], len(matched_keywords), len(keywords)))

    st.session_state.analysis_results = {
        "correct_mcqs": correct_mcqs,
        "total_mcqs": total_mcqs,
        "descriptive_feedback": descriptive_feedback,
        "time_taken": st.session_state.time_taken
    }

    st.session_state.leaderboard.append((st.session_state.time_taken, correct_mcqs))
    st.session_state.leaderboard.sort()
    st.session_state.page = "analysis"
    st.experimental_rerun()

# Process tasks like extracting topics or generating questions
def process_task(task_name, prompt_template):
    st.title(f"🔍 {task_name}")
    st.write("Processing... (AI is working)")
    user_input = st.session_state.uploaded_file or st.session_state.custom_topic
    if user_input:
        prompt = prompt_template.format(user_input)
        st.session_state.response = get_output(prompt)
        st.write(st.session_state.response)
    if st.button("⬅️ Back to Options"):
        st.session_state.page = "options"
        st.experimental_rerun()

# Extract important topics
if st.session_state.page == "topics":
    process_task("Important Topics", "Extract the most important topics from: {}")

# Generate important questions
elif st.session_state.page == "questions":
    st.title("📝 Generate Important Questions")
    option = st.radio("Choose an option:", ["Generate Key Questions", "Generate a Full Question Paper"])
    
    if option == "Generate Key Questions":
        process_task("Important Questions", "Generate 5 key questions for: {}")
    else:
        def generate_prompt(num_mcq, num_3_marks, num_5_marks, difficulty_level, subject, topics=None):
            prompt = f"Generate a Question Paper of {subject} having "
            if num_mcq > 0:
                prompt += f'{num_mcq} MCQs with 1 mark each, '
            if num_3_marks > 0:
                prompt += f'{num_3_marks} Questions with 3 marks each, '
            if num_5_marks > 0:
                prompt += f'{num_5_marks} Questions with 5 marks each. '
            prompt += f'Difficulty level: {difficulty_level}. '
            if topics:
                prompt += f'Cover topics: {topics}. '
            return prompt
        
        subjects = { 'Data Structures': ['Trees', 'Sorting', 'Graphs'], 'Operating Systems': ['Memory Management', 'Scheduling'], 'DBMS': ['Normalization', 'SQL Queries'] }
        subject = st.selectbox("📚 Select Subject", list(subjects.keys()))
        topics = st.multiselect("📖 Select Topics", subjects[subject])
        num_mcq = st.slider("Number of MCQs", 0, 20, 5)
        num_3_marks = st.slider("Number of 3-mark Questions", 0, 20, 3)
        num_5_marks = st.slider("Number of 5-mark Questions", 0, 20, 2)
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
        if st.button("🚀 Generate Question Paper"):
            prompt = generate_prompt(num_mcq, num_3_marks, num_5_marks, difficulty, subject, topics)
            prompt += f"\nUse this reference: {st.session_state.custom_topic or st.session_state.uploaded_file}"
            st.session_state.response = get_output(prompt)
            st.text_area("📄 Generated Question Paper:", st.session_state.response, height=300)

# Mock test page
if st.session_state.page == "mock_tests":
    st.title("📝 Mock Test")
    st.write("Answer the following questions:")
    st.session_state.mock_test_questions = load_questions()
    st.session_state.start_time = time.time()

    for q in st.session_state.mock_test_questions:
        if q["type"] == "MCQ":
            st.session_state.user_answers[q["question"]] = st.radio(q["question"], q["options"], key=q["question"])
        elif q["type"] == "Short Answer":
            st.session_state.user_answers[q["question"]] = st.text_area(q["question"], key=q["question"])
    
    if st.button("Submit Test"):
        st.session_state.mock_test_completed = True
        analyze_performance()

if st.session_state.page == "analysis":
    st.title("📊 Performance Analysis")
    results = st.session_state.analysis_results

    st.write(f"Correct MCQs: {results['correct_mcqs']} out of {results['total_mcqs']}")
    st.write(f"Time Taken: {results['time_taken']} seconds")
    
    st.write("### Descriptive Answers Feedback:")
    for q, matched, total in results['descriptive_feedback']:
        st.write(f"**{q}**: {matched}/{total} keywords matched")

    st.write("### Leaderboard:")
    for i, (time_taken, score) in enumerate(st.session_state.leaderboard[:5], 1):
        st.write(f"{i}. Score: {score} | Time: {time_taken}s")

    if st.button("Back to Options"):
        st.session_state.page = "options"
        st.experimental_rerun()