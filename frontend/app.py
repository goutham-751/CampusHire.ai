"""
CampusHire.ai Streamlit Frontend
Complete web interface for AI voice interview system
"""

import streamlit as st
import requests
import json
import time
import uuid
from pathlib import Path
import base64
import speech_recognition as sr
import pyttsx3
from io import BytesIO
import threading
import queue
import tempfile
import os

# Configure Streamlit page
st.set_page_config(
    page_title="CampusHire.ai - Voice Interview",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Your FastAPI server

# Initialize session state variables
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'interview_responses' not in st.session_state:
    st.session_state.interview_responses = []
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'current_question_number' not in st.session_state:
    st.session_state.current_question_number = 0
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 5

# Audio recording helper functions
class AudioRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        
    def record_audio(self, timeout=15, phrase_limit=60):
        """Record audio and convert to text"""
        try:
            with self.microphone as source:
                # Calibrate for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                st.info("🎤 Listening... Please speak clearly")
                
                # Record audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_limit
                )
                
                st.info("🔄 Processing your response...")
                
                # Convert to text
                text = self.recognizer.recognize_google(audio)
                return text, "success"
                
        except sr.WaitTimeoutError:
            return None, "timeout"
        except sr.UnknownValueError:
            return None, "unclear"
        except sr.RequestError as e:
            return None, f"error: {e}"

# API Helper Functions
def create_interview_session(job_description, candidate_name, num_questions, resume_file=None):
    """Create new interview session via API"""
    try:
        files = {}
        if resume_file:
            files["resume"] = ("resume.pdf", resume_file, "application/pdf")
        
        data = {
            "job_description": job_description,
            "candidate_name": candidate_name,
            "num_questions": num_questions
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/interview/create",
            data=data,
            files=files
        )
        
        if response.status_code == 200:
            return response.json(), True
        else:
            return {"error": f"HTTP {response.status_code}"}, False
            
    except Exception as e:
        return {"error": str(e)}, False

def get_next_question(session_id):
    """Get next question from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/interview/{session_id}/question")
        if response.status_code == 200:
            return response.json(), True
        else:
            return {"error": f"HTTP {response.status_code}"}, False
    except Exception as e:
        return {"error": str(e)}, False

def submit_response(session_id, question_id, response_text):
    """Submit candidate response to API"""
    try:
        data = {
            "question_id": question_id,
            "response_text": response_text
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/interview/{session_id}/response",
            json=data
        )
        
        if response.status_code == 200:
            return response.json(), True
        else:
            return {"error": f"HTTP {response.status_code}"}, False
    except Exception as e:
        return {"error": str(e)}, False

def get_interview_report(session_id):
    """Get final interview report"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/interview/{session_id}/report")
        if response.status_code == 200:
            return response.json(), True
        else:
            return {"error": f"HTTP {response.status_code}"}, False
    except Exception as e:
        return {"error": str(e)}, False

# Text-to-Speech for questions
@st.cache_resource
def get_tts_engine():
    """Initialize TTS engine"""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 0.9)
        return engine
    except:
        return None

def speak_text(text):
    """Convert text to speech"""
    tts_engine = get_tts_engine()
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except:
            st.warning("Text-to-speech not available")

# Main Application Layout
def main():
    st.title("🎯 CampusHire.ai - AI Voice Interview System")
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("📋 Interview Navigation")
        
        if st.session_state.session_id:
            st.success(f"Active Session: {st.session_state.session_id[:8]}...")
            st.progress(st.session_state.current_question_number / st.session_state.total_questions)
            st.write(f"Question {st.session_state.current_question_number} of {st.session_state.total_questions}")
        
        st.markdown("---")
        st.header("🔧 System Status")
        
        # Check API connection
        try:
            response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend Connected")
            else:
                st.error("❌ Backend Error")
        except:
            st.error("❌ Backend Offline")
            st.error("Please start your FastAPI server:")
            st.code("python backend/api/main.py")
    
    # Main content area
    if not st.session_state.session_id:
        show_setup_page()
    else:
        show_interview_page()

def show_setup_page():
    """Setup page for new interviews"""
    st.header("🚀 Start New Interview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Candidate Information
        st.subheader("👤 Candidate Information")
        candidate_name = st.text_input("Full Name", placeholder="Enter candidate's name")
        
        # Job Description
        st.subheader("💼 Job Description")
        job_description = st.text_area(
            "Job Requirements", 
            placeholder="Paste the job description here...",
            height=150
        )
        
        # Resume Upload
        st.subheader("📄 Resume Upload (Optional)")
        resume_file = st.file_uploader(
            "Upload Resume (PDF)", 
            type=['pdf'],
            help="Upload candidate's resume for personalized questions"
        )
        
        # Interview Settings
        st.subheader("⚙️ Interview Settings")
        num_questions = st.slider("Number of Questions", 3, 10, 5)
        
        # Start Interview Button
        if st.button("🎤 Start Voice Interview", type="primary", use_container_width=True):
            if candidate_name and job_description:
                with st.spinner("Creating interview session..."):
                    result, success = create_interview_session(
                        job_description, 
                        candidate_name, 
                        num_questions, 
                        resume_file
                    )
                
                if success:
                    st.session_state.session_id = result['session_id']
                    st.session_state.total_questions = num_questions
                    st.session_state.current_question_number = 0
                    st.success("✅ Interview session created!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create session: {result.get('error', 'Unknown error')}")
            else:
                st.error("Please fill in candidate name and job description")
    
    with col2:
        st.subheader("📋 Interview Overview")
        st.info("""
        **This AI Interview System:**
        
        🎤 **Voice Recognition**: Speaks questions and listens to responses
        
        🧠 **AI-Powered**: Uses Gemini AI for intelligent questions and evaluation
        
        📊 **Real-time Scoring**: Evaluates responses as you go
        
        📈 **Detailed Reports**: Generates comprehensive assessment reports
        
        🔄 **Adaptive**: Questions adjust based on previous responses
        """)
        
        st.subheader("🎯 Tips for Success")
        st.success("""
        • Speak clearly and at normal pace
        • Take time to think before responding
        • Provide specific examples
        • Use the microphone button to record
        • Review your responses before submitting
        """)

def show_interview_page():
    """Main interview interface"""
    st.header("🎤 Voice Interview in Progress")
    
    # Get current question if none exists
    if not st.session_state.current_question:
        with st.spinner("Loading next question..."):
            result, success = get_next_question(st.session_state.session_id)
        
        if success and "question_text" in result:
            st.session_state.current_question = result
            st.session_state.current_question_number = result.get('question_number', 1)
        elif success and result.get('status') == 'interview_completed':
            show_completion_page()
            return
        else:
            st.error(f"❌ Error loading question: {result.get('error', 'Unknown error')}")
            return
    
    # Display current question
    question_data = st.session_state.current_question
    
    st.subheader(f"Question {question_data.get('question_number', '?')} of {st.session_state.total_questions}")
    
    # Question display with TTS
    question_text = question_data.get('question_text', '')
    st.markdown(f"### 💬 {question_text}")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🔊 Read Question Aloud"):
            with st.spinner("Speaking question..."):
                speak_text(question_text)
    
    # Response Collection
    st.markdown("---")
    st.subheader("🎤 Your Response")
    
    # Audio recording interface
    col1, col2, col3 = st.columns([2, 2, 2])
    
    # Initialize audio recorder
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()
    
    response_text = ""
    
    with col1:
        if st.button("🎤 Start Recording", type="primary", use_container_width=True):
            if not st.session_state.is_recording:
                st.session_state.is_recording = True
                
                with st.spinner("Recording your response..."):
                    recorded_text, status = st.session_state.audio_recorder.record_audio()
                
                st.session_state.is_recording = False
                
                if status == "success" and recorded_text:
                    st.session_state.recorded_response = recorded_text
                    st.success("✅ Recording completed!")
                elif status == "timeout":
                    st.warning("⏱️ Recording timeout - please try again")
                elif status == "unclear":
                    st.warning("🔇 Could not understand audio - please speak more clearly")
                else:
                    st.error(f"❌ Recording error: {status}")
    
    with col2:
        # Manual text input as alternative
        response_text = st.text_area(
            "Or type your response:", 
            value=st.session_state.get('recorded_response', ''),
            height=150,
            key="manual_response"
        )
    
    with col3:
        if st.button("📝 Submit Response", type="secondary", use_container_width=True):
            if response_text.strip():
                with st.spinner("Submitting and evaluating response..."):
                    result, success = submit_response(
                        st.session_state.session_id,
                        question_data.get('question_id'),
                        response_text
                    )
                
                if success:
                    # Store response
                    st.session_state.interview_responses.append({
                        "question": question_text,
                        "response": response_text,
                        "evaluation": result.get('evaluation_score', 0),
                        "feedback": result.get('feedback', '')
                    })
                    
                    # Show immediate feedback
                    score = result.get('evaluation_score', 0)
                    feedback = result.get('feedback', 'Thank you for your response.')
                    
                    if score >= 8:
                        st.success(f"🎉 Excellent response! Score: {score}/10")
                    elif score >= 6:
                        st.info(f"👍 Good response! Score: {score}/10")
                    else:
                        st.warning(f"💡 Room for improvement. Score: {score}/10")
                    
                    st.info(f"💬 Feedback: {feedback}")
                    
                    # Clear current question to load next one
                    st.session_state.current_question = None
                    st.session_state.recorded_response = ""
                    
                    # Check if interview is complete
                    if result.get('next_action') == 'complete':
                        st.balloons()
                        time.sleep(2)
                        show_completion_page()
                        return
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Failed to submit response: {result.get('error', 'Unknown error')}")
            else:
                st.error("Please provide a response before submitting")
    
    # Show interview progress
    st.markdown("---")
    st.subheader("📊 Interview Progress")
    
    if st.session_state.interview_responses:
        for i, resp in enumerate(st.session_state.interview_responses, 1):
            with st.expander(f"Question {i}: {resp['question'][:50]}..."):
                st.write(f"**Your Response:** {resp['response'][:200]}...")
                st.write(f"**Score:** {resp['evaluation']}/10")
                st.write(f"**Feedback:** {resp['feedback']}")
    
    # Emergency controls
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⏸️ End Interview Early"):
            show_completion_page()
    
    with col2:
        if st.button("🔄 Restart Interview"):
            # Clear session state
            for key in ['session_id', 'current_question', 'interview_responses', 'recorded_response']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def show_completion_page():
    """Interview completion and report page"""
    st.header("🎉 Interview Completed!")
    
    st.success("Congratulations! You have successfully completed your voice interview.")
    
    # Generate final report
    if st.button("📊 Generate Final Report", type="primary"):
        with st.spinner("Generating comprehensive interview report..."):
            result, success = get_interview_report(st.session_state.session_id)
        
        if success:
            st.subheader("📋 Interview Assessment Report")
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Questions Answered", result.get('questions_answered', 0))
            with col2:
                st.metric("Average Score", f"{result.get('average_score', 0)}/10")
            with col3:
                st.metric("Resume Match", f"{result.get('resume_match_score', 0):.1f}%")
            with col4:
                recommendation = result.get('recommendation', 'Under Review')
                st.metric("Recommendation", recommendation)
            
            # Display detailed responses
            st.subheader("📝 Detailed Responses")
            
            if 'detailed_responses' in result:
                for i, response in enumerate(result['detailed_responses'], 1):
                    with st.expander(f"Question {i}: {response.get('category', 'General').title()} Question"):
                        st.write(f"**Question:** {response.get('question', 'N/A')}")
                        st.write(f"**Response:** {response.get('response_text', 'N/A')}")
                        
                        eval_data = response.get('evaluation', {})
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Overall Score", f"{eval_data.get('overall_score', 0)}/10")
                        with col2:
                            st.metric("Technical Depth", f"{eval_data.get('technical_depth', 0)}/5")
                        with col3:
                            st.metric("Communication", f"{eval_data.get('communication_clarity', 0)}/5")
                        
                        if eval_data.get('strengths'):
                            st.write("**Strengths:**")
                            for strength in eval_data['strengths']:
                                st.write(f"• {strength}")
                        
                        if eval_data.get('improvements'):
                            st.write("**Areas for Improvement:**")
                            for improvement in eval_data['improvements']:
                                st.write(f"• {improvement}")
            
            # Download report as JSON
            report_json = json.dumps(result, indent=2)
            st.download_button(
                label="📥 Download Full Report (JSON)",
                data=report_json,
                file_name=f"interview_report_{st.session_state.session_id}.json",
                mime="application/json"
            )
        
        else:
            st.error(f"❌ Failed to generate report: {result.get('error', 'Unknown error')}")
    
    # Start new interview button
    if st.button("🔄 Start New Interview"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            if key != 'audio_recorder':  # Keep the audio recorder
                del st.session_state[key]
        st.rerun()

# Run the application
if __name__ == "__main__":
    main()
