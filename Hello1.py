import streamlit as st
import json
import os
import time
from model import get_output

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(page_title="Edugenius", layout="centered")

# -----------------------------
# Session State Initialization
# -----------------------------
def initialize_session():
    defaults = {
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
        "leaderboard": [],
        "rerun_flag": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session()

# -----------------------------
# Load/Save Templates
# -----------------------------
def load_templates():
    try:
        with open("templates.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_templates(templates):
    with open("templates.json", "w") as f:
        json.dump(templates, f)

# -----------------------------
# Process User Input
# -----------------------------
def process_input(uploaded_file, custom_topic):
    if uploaded_file:
        os.makedirs("temp", exist_ok=True)
        file_path = f"temp/{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_file = file_path

    if custom_topic:
        st.session_state.custom_topic = custom_topic

    if uploaded_file or custom_topic:
        st.session_state.page = "options"
        st.rerun()
    else:
        st.warning("⚠️ Please upload a file or enter a topic!")

# -----------------------------
# Load/Save Mock Test
# -----------------------------
JSON_FILE = "mock_test_questions.json"

def load_questions():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return []

def save_analysis(results):
    with open("analysis_results.json", "w") as f:
        json.dump(results, f, indent=4)

# -----------------------------
# Generate Mock Test
# -----------------------------
def generate_mock_test():
    topic = st.session_state.custom_topic or st.session_state.uploaded_file
    if not topic:
        st.warning("⚠️ Please upload a file or enter a topic first!")
        return

    # More specific and structured prompt
    prompt = f"""
    Create a mock test about: {topic}
    
    Generate exactly:
    - 5 Multiple Choice Questions (MCQs)
    - 3 Short Answer Questions
    
    Format your response as a JSON array with this exact structure:
    
    [
      {{
        "type": "MCQ",
        "question": "Your multiple choice question here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Correct Option"
      }},
      {{
        "type": "Short Answer", 
        "question": "Your short answer question here?",
        "keywords": ["keyword1", "keyword2", "keyword3"]
      }}
    ]
    
    Important:
    - Return ONLY the JSON, no additional text
    - Use double quotes for all strings
    - For MCQs, the answer must exactly match one option
    - For Short Answer, provide 3-4 relevant keywords
    - Ensure valid JSON format
    """

    with st.spinner("🔄 Generating mock test questions..."):
        response = get_output(prompt)

    # Debug: Show raw response
    st.write("**Raw AI Response:**")
    st.code(response)

    # Try to extract and parse JSON
    questions_data = extract_json_from_response(response)
    
    if questions_data:
        # Successfully parsed JSON
        with open(JSON_FILE, "w") as f:
            json.dump(questions_data, f, indent=4)

        st.session_state.mock_test_questions = questions_data
        st.session_state.start_time = time.time()
        st.session_state.page = "mock_tests"
        st.rerun()
    else:
        # JSON parsing failed - use fallback
        st.error("❌ Could not parse AI response as JSON. Using sample questions.")
        use_fallback_questions(topic)

def extract_json_from_response(response):
    """Extract and parse JSON from AI response"""
    try:
        # Clean the response
        cleaned = response.strip()
        
        # Remove markdown code blocks
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        # Find JSON array start and end
        start_idx = cleaned.find('[')
        end_idx = cleaned.rfind(']') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_str = cleaned[start_idx:end_idx]
            return json.loads(json_str)
        else:
            # Try parsing the whole response
            return json.loads(cleaned)
            
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None

def use_fallback_questions(topic):
    """Create sample questions when AI fails"""
    sample_questions = [
        {
            "type": "MCQ",
            "question": f"What is the primary purpose of {topic}?",
            "options": ["To solve problems", "To organize data", "To automate tasks", "All of the above"],
            "answer": "All of the above"
        },
        {
            "type": "MCQ", 
            "question": f"Which concept is fundamental to understanding {topic}?",
            "options": ["Basic principles", "Advanced techniques", "Historical context", "Future trends"],
            "answer": "Basic principles"
        },
        {
            "type": "MCQ",
            "question": f"What is a common tool used in {topic}?",
            "options": ["Python", "Java", "C++", "Various tools depending on application"],
            "answer": "Various tools depending on application"
        },
        {
            "type": "MCQ",
            "question": f"How does {topic} benefit modern applications?",
            "options": ["Improves efficiency", "Reduces costs", "Enhances functionality", "All of these"],
            "answer": "All of these"
        },
        {
            "type": "MCQ",
            "question": f"What skill is most important for working with {topic}?",
            "options": ["Analytical thinking", "Memorization", "Creativity", "All are important"],
            "answer": "Analytical thinking"
        },
        {
            "type": "Short Answer",
            "question": f"Explain the basic concept of {topic} in your own words.",
            "keywords": ["fundamental", "purpose", "application", "benefits"]
        },
        {
            "type": "Short Answer", 
            "question": f"Describe a real-world application of {topic}.",
            "keywords": ["practical", "implementation", "use case", "example"]
        },
        {
            "type": "Short Answer",
            "question": f"What are the key advantages of learning {topic}?",
            "keywords": ["career", "skills", "knowledge", "opportunities"]
        }
    ]
    
    # Save sample questions
    with open(JSON_FILE, "w") as f:
        json.dump(sample_questions, f, indent=4)
    
    st.session_state.mock_test_questions = sample_questions
    st.session_state.start_time = time.time()
    st.session_state.page = "mock_tests"
    st.rerun()

# -----------------------------
# Analyze Performance
# -----------------------------
def analyze_performance():
    if not st.session_state.mock_test_completed:
        st.warning("⚠️ Complete the mock test first!")
        return

    start_time = st.session_state.start_time
    st.session_state.time_taken = round(time.time() - start_time, 2) if start_time else 0

    correct_mcqs = sum(
        1 for q in st.session_state.mock_test_questions
        if q["type"] == "MCQ" and st.session_state.user_answers.get(q["question"]) == q["answer"]
    )

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
    st.rerun()

# -----------------------------
# Process Tasks (Topics/Questions)
# -----------------------------
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
        st.rerun()

# -----------------------------
# Pages
# -----------------------------
# Home Page
if st.session_state.page == "upload":
    st.title("📚 Edugenius: AI Study Companion")
    st.subheader("Upload your study material or enter a topic")
    uploaded_file = st.file_uploader("Choose a PDF or Text file", type=["pdf", "txt"])
    custom_topic = st.text_area("Or enter a study topic manually:")
    if st.button("Next ➡️"):
        process_input(uploaded_file, custom_topic)

# Options Page
elif st.session_state.page == "options":
    st.title("📖 Study Assistant")
    st.subheader("Choose an action:")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📌 Extract Important Topics"):
            st.session_state.page = "topics"
            st.rerun()
        if st.button("📝 Generate Important Questions"):
            st.session_state.page = "questions"
            st.rerun()
    with col2:
        if st.button("🎯 Generate Mock Tests"):
            generate_mock_test()
        if st.button("📊 Performance Analysis"):
            st.session_state.page = "analysis"
            st.rerun()
    if st.button("🏠 Back to Home"):
        st.session_state.page = "upload"
        st.rerun()

# Topics Page
elif st.session_state.page == "topics":
    process_task("Important Topics", "Extract the most important topics from: {}")

# Questions Page
elif st.session_state.page == "questions":
    st.title("📝 Generate Important Questions")
    option = st.radio("Choose an option:", ["Generate Key Questions", "Generate a Full Question Paper"])

    if option == "Generate Key Questions":
        process_task("Important Questions", "Generate 5 key questions for: {}")
    else:
        # Full Question Paper
        def generate_prompt(num_mcq, num_3_marks, num_5_marks, difficulty_level, subject, topics=None):
            prompt = f"Generate a Question Paper of {subject} having "
            if num_mcq > 0:
                prompt += f"{num_mcq} MCQs with 1 mark each, "
            if num_3_marks > 0:
                prompt += f"{num_3_marks} Questions with 3 marks each, "
            if num_5_marks > 0:
                prompt += f"{num_5_marks} Questions with 5 marks each. "
            prompt += f"Difficulty level: {difficulty_level}. "
            if topics:
                prompt += f"Cover topics: {topics}. "
            return prompt

        subjects = {
            'Data Structures': ['Trees', 'Sorting', 'Graphs'],
            'Operating Systems': ['Memory Management', 'Scheduling'],
            'DBMS': ['Normalization', 'SQL Queries']
        }
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

# Mock Test Page
# Mock Test Page
elif st.session_state.page == "mock_tests":
    st.title("📝 Mock Test")
    st.write("Answer the following questions:")

    st.session_state.mock_test_questions = load_questions()
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()

    # Initialize answers if not set
    for q in st.session_state.mock_test_questions:
        if q["question"] not in st.session_state.user_answers:
            st.session_state.user_answers[q["question"]] = None

    for i, q in enumerate(st.session_state.mock_test_questions):
        st.write(f"**Question {i+1}:**")
        
        if q["type"] == "MCQ":
            # FIXED: Added index=None to prevent auto-selection
            answer = st.radio(
                q["question"], 
                q["options"], 
                key=f"mcq_{i}",  # Changed key to include index
                index=None,  # This prevents auto-selection
                help="Select your answer"
            )
            st.session_state.user_answers[q["question"]] = answer
            
        elif q["type"] == "Short Answer":
            answer = st.text_area(
                q["question"], 
                key=f"short_{i}",
                placeholder="Type your answer here..."
            )
            st.session_state.user_answers[q["question"]] = answer
        
        st.write("---")  # Separator between questions

    if st.button("Submit Test"):
        # Check if all questions are answered
        unanswered_questions = []
        for q in st.session_state.mock_test_questions:
            if not st.session_state.user_answers.get(q["question"]):
                unanswered_questions.append(f"Q{st.session_state.mock_test_questions.index(q)+1}")
        
        if unanswered_questions:
            st.error(f"❌ Please answer all questions. Missing: {', '.join(unanswered_questions)}")
        else:
            st.session_state.mock_test_completed = True
            analyze_performance()

# Analysis Page
elif st.session_state.page == "analysis":
    st.title("📊 Performance Analysis")
    results = st.session_state.analysis_results

    st.write(f"Correct MCQs: {results.get('correct_mcqs',0)} out of {results.get('total_mcqs',0)}")
    st.write(f"Time Taken: {results.get('time_taken',0)} seconds")

    st.write("### Descriptive Answers Feedback:")
    for q, matched, total in results.get('descriptive_feedback', []):
        st.write(f"**{q}**: {matched}/{total} keywords matched")

    st.write("### Leaderboard:")
    for i, (time_taken, score) in enumerate(st.session_state.leaderboard[:5], 1):
        st.write(f"{i}. Score: {score} | Time: {time_taken}s")

    if st.button("Back to Options"):
        st.session_state.page = "options"
        st.rerun()