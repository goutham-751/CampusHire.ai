"""
CampusHire.ai Streamlit Frontend
Complete web interface for AI voice interview system
"""

import streamlit as st
import requests
import json
import time
from pathlib import Path
import io
import tempfile

# Configure Streamlit page
st.set_page_config(
    page_title="CampusHire.ai - AI Voice Interviews",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'interview_responses' not in st.session_state:
    st.session_state.interview_responses = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False

# API Helper Functions
def check_api_health():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def create_interview_session(candidate_name, job_description, num_questions, resume_file=None):
    """Create a new interview session"""
    try:
        files = {}
        if resume_file:
            files["resume"] = ("resume.pdf", resume_file, "application/pdf")
        
        data = {
            "candidate_name": candidate_name,
            "job_description": job_description,
            "num_questions": num_questions
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/interview/create",
            data=data,
            files=files,
            timeout=30
        )
        
        return response.status_code == 201, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def get_next_question(session_id):
    """Get the next question"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/interview/{session_id}/question")
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def submit_response(session_id, question_id, response_text):
    """Submit candidate response"""
    try:
        data = {
            "question_id": question_id,
            "response_text": response_text,
            "audio_duration": 0
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/interview/{session_id}/response",
            json=data
        )
        
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def get_interview_report(session_id):
    """Get final interview report"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/interview/{session_id}/report")
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

def get_session_status(session_id):
    """Get session status"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/interview/{session_id}/status")
        return response.status_code == 200, response.json()
    except Exception as e:
        return False, {"error": str(e)}

# Main Application
def main():
    # Header
    st.title("🎯 CampusHire.ai")
    st.subheader("AI-Powered Voice Interview Platform")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 System Status")
        
        # Check API health
        api_healthy, health_data = check_api_health()
        
        if api_healthy:
            st.success("✅ Backend Connected")
            if health_data:
                st.info(f"🎤 {health_data.get('active_sessions', 0)} Active Sessions")
        else:
            st.error("❌ Backend Offline")
            st.error("Please start your backend server:")
            st.code("cd backend/api && python main.py")
            return
        
        # Session info
        if st.session_state.session_id:
            success, status_data = get_session_status(st.session_state.session_id)
            if success:
                progress = status_data.get("progress", {})
                st.success(f"📋 Session Active")
                st.progress(progress.get("completion_percentage", 0) / 100)
                st.write(f"Question {progress.get('current_question', 0)} of {progress.get('total_questions', 5)}")
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Start New Interview"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content
    if not st.session_state.session_id:
        show_setup_page()
    elif not st.session_state.interview_started:
        show_interview_ready_page()
    else:
        show_interview_page()

def show_setup_page():
    """Setup page for new interviews"""
    st.header("🚀 Start New AI Interview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Interview Setup Form
        with st.form("interview_setup"):
            st.subheader("👤 Candidate Information")
            candidate_name = st.text_input(
                "Full Name *", 
                placeholder="Enter candidate's full name",
                help="Required field for interview session"
            )
            
            st.subheader("💼 Job Information")
            job_description = st.text_area(
                "Job Description & Requirements", 
                placeholder="Paste the job description here...\n\nThis helps generate personalized questions based on role requirements.",
                height=150,
                help="Detailed job description improves question relevance"
            )
            
            st.subheader("📄 Resume Upload")
            resume_file = st.file_uploader(
                "Upload Resume (PDF)", 
                type=['pdf'],
                help="Optional - Upload for personalized questions and resume-job matching"
            )
            
            st.subheader("⚙️ Interview Settings")
            num_questions = st.slider(
                "Number of Questions", 
                min_value=3, 
                max_value=10, 
                value=5,
                help="Recommended: 5-7 questions for comprehensive assessment"
            )
            
            # Submit button
            submitted = st.form_submit_button(
                "🎤 Create Interview Session", 
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if not candidate_name or not candidate_name.strip():
                    st.error("❌ Please enter the candidate's name")
                else:
                    with st.spinner("🔄 Creating interview session..."):
                        success, result = create_interview_session(
                            candidate_name.strip(),
                            job_description.strip(),
                            num_questions,
                            resume_file
                        )
                    
                    if success:
                        st.session_state.session_id = result['session_id']
                        st.session_state.candidate_name = candidate_name.strip()
                        st.session_state.total_questions = num_questions
                        st.success("✅ Interview session created successfully!")
                        
                        # Show resume processing results
                        if result.get('resume_processing_log', {}).get('extraction_successful'):
                            match_score = result.get('resume_match_score', 0)
                            st.info(f"📊 Resume processed! Job match score: {match_score:.1f}%")
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create session: {result.get('error', 'Unknown error')}")
    
    with col2:
        # Information panel
        st.subheader("📋 About CampusHire.ai")
        st.info("""
        **🎯 AI-Powered Interviews**
        - Intelligent question generation
        - Real-time response evaluation
        - Comprehensive candidate assessment
        
        **🔒 Privacy First**
        - Resume files processed temporarily
        - Secure data handling
        - GDPR compliant
        
        **📊 Advanced Analytics**
        - Technical competency scoring
        - Communication assessment
        - Detailed reporting
        """)
        
        st.subheader("💡 Interview Tips")
        st.success("""
        **For Best Results:**
        - Speak clearly and naturally
        - Provide specific examples
        - Take time to think before answering
        - Give detailed responses
        - Ask questions if unclear
        """)

def show_interview_ready_page():
    """Page shown when session is created but interview hasn't started"""
    st.header("🎤 Interview Session Ready")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.success(f"✅ Interview session created for **{st.session_state.get('candidate_name', 'Candidate')}**")
        
        # Session details
        st.subheader("📋 Session Details")
        success, status = get_session_status(st.session_state.session_id)
        if success:
            st.write(f"**Session ID:** {st.session_state.session_id[:16]}...")
            st.write(f"**Total Questions:** {status.get('progress', {}).get('total_questions', 5)}")
            
            # Show resume info if available
            candidate_info = status.get('candidate_info', {})
            if candidate_info.get('resume_processed'):
                st.write(f"**Resume Processed:** ✅ Yes (Match: {candidate_info.get('resume_match_score', 0):.1f}%)")
            else:
                st.write("**Resume Processed:** ❌ No")
        
        st.markdown("---")
        
        # Start interview button
        st.subheader("🚀 Ready to Begin?")
        st.write("Click below to start your AI-powered voice interview. Make sure you're in a quiet environment and ready to speak clearly.")
        
        if st.button("🎤 Start Interview Now", type="primary", use_container_width=True):
            st.session_state.interview_started = True
            st.rerun()
    
    with col2:
        st.subheader("🎯 What to Expect")
        st.info("""
        **Interview Process:**
        1. AI generates personalized questions
        2. You provide detailed responses
        3. Real-time evaluation and feedback
        4. Comprehensive final report
        
        **Question Types:**
        - Introduction & Background
        - Technical Skills
        - Behavioral Scenarios
        - Role-Specific Queries
        - Problem Solving
        """)

def show_interview_page():
    """Main interview interface"""
    st.header("🎤 Interview in Progress")
    
    # Get current question if needed
    if not st.session_state.current_question:
        with st.spinner("🔄 Loading next question..."):
            success, result = get_next_question(st.session_state.session_id)
        
        if success:
            if result.get('status') == 'interview_completed':
                show_completion_page()
                return
            else:
                st.session_state.current_question = result
        else:
            st.error(f"❌ Error loading question: {result.get('error', 'Unknown error')}")
            return
    
    # Display current question
    question_data = st.session_state.current_question
    
    # Progress indicator
    progress = question_data.get('progress_percentage', 0)
    st.progress(progress / 100)
    st.write(f"**Progress:** {progress:.1f}% Complete")
    
    # Question display
    st.subheader(f"Question {question_data.get('question_number', '?')} of {question_data.get('total_questions', 5)}")
    
    category = question_data.get('category', 'General').title()
    st.markdown(f"**Category:** {category}")
    
    # Question text in a nice container
    with st.container():
        st.markdown("### 💬 Interview Question")
        st.markdown(f"*{question_data.get('question_text', 'Loading...')}*")
    
    st.markdown("---")
    
    # Response input
    st.subheader("✍️ Your Response")
    
    response_text = st.text_area(
        "Type your response here:", 
        height=200,
        placeholder="Provide a detailed response with specific examples...",
        help="Take your time to provide a comprehensive answer with concrete examples."
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("📝 Submit Response", type="primary", use_container_width=True):
            if not response_text.strip():
                st.error("❌ Please provide a response before submitting")
            else:
                with st.spinner("🔄 Evaluating your response..."):
                    success, result = submit_response(
                        st.session_state.session_id,
                        question_data.get('question_id'),
                        response_text.strip()
                    )
                
                if success:
                    # Store response and show feedback
                    st.session_state.interview_responses.append({
                        "question": question_data.get('question_text'),
                        "response": response_text.strip(),
                        "evaluation": result.get('evaluation_score', 0),
                        "feedback": result.get('feedback', '')
                    })
                    
                    # Show evaluation results
                    score = result.get('evaluation_score', 0)
                    feedback = result.get('feedback', '')
                    
                    if score >= 8:
                        st.success(f"🎉 Excellent! Score: {score}/10")
                    elif score >= 6:
                        st.info(f"👍 Good response! Score: {score}/10")
                    else:
                        st.warning(f"💡 Score: {score}/10 - Room for improvement")
                    
                    st.info(f"💬 **Feedback:** {feedback}")
                    
                    # Clear current question
                    st.session_state.current_question = None
                    
                    # Check if interview is complete
                    if result.get('next_action') == 'complete':
                        time.sleep(2)
                        st.balloons()
                        show_completion_page()
                        return
                    
                    # Auto-advance to next question
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(f"❌ Failed to submit response: {result.get('error', 'Unknown error')}")
    
    # Show previous responses
    if st.session_state.interview_responses:
        st.markdown("---")
        st.subheader("📊 Previous Responses")
        
        for i, resp in enumerate(st.session_state.interview_responses[-3:], 1):  # Show last 3
            with st.expander(f"Response {len(st.session_state.interview_responses) - 3 + i}: Score {resp['evaluation']}/10"):
                st.write(f"**Q:** {resp['question'][:100]}...")
                st.write(f"**A:** {resp['response'][:200]}...")
                st.write(f"**Feedback:** {resp['feedback']}")

def show_completion_page():
    """Interview completion and report page"""
    st.header("🎉 Interview Completed!")
    
    st.success(f"Congratulations! You have successfully completed your CampusHire.ai interview.")
    
    # Show completion stats
    col1, col2, col3 = st.columns(3)
    
    responses_count = len(st.session_state.interview_responses)
    avg_score = sum(r['evaluation'] for r in st.session_state.interview_responses) / max(responses_count, 1)
    
    with col1:
        st.metric("Questions Answered", responses_count)
    with col2:
        st.metric("Average Score", f"{avg_score:.1f}/10")
    with col3:
        if avg_score >= 7:
            st.metric("Assessment", "Strong 💪")
        elif avg_score >= 5:
            st.metric("Assessment", "Good 👍")
        else:
            st.metric("Assessment", "Developing 📈")
    
    st.markdown("---")
    
    # Generate report button
    if st.button("📊 Generate Detailed Report", type="primary", use_container_width=True):
        with st.spinner("🔄 Generating comprehensive assessment report..."):
            success, report_data = get_interview_report(st.session_state.session_id)
        
        if success:
            st.subheader("📋 Interview Assessment Report")
            
            # Display key metrics
            performance = report_data.get('performance_metrics', {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Overall Score", f"{performance.get('overall_score', 0):.1f}/10")
            with col2:
                st.metric("Technical Skills", f"{performance.get('technical_competency', 0):.1f}/5")
            with col3:
                st.metric("Communication", f"{performance.get('communication_skills', 0):.1f}/5")
            with col4:
                recommendation = performance.get('recommendation', 'Under Review')
                st.metric("Recommendation", recommendation)
            
            # Detailed analysis
            st.subheader("📈 Detailed Analysis")
            
            # Strengths and improvements
            qualitative = report_data.get('qualitative_assessment', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**💪 Key Strengths:**")
                strengths = qualitative.get('top_strengths', [])
                for strength in strengths[:5]:
                    st.write(f"• {strength}")
            
            with col2:
                st.markdown("**📈 Development Areas:**")
                improvements = qualitative.get('key_improvement_areas', [])
                for improvement in improvements[:3]:
                    st.write(f"• {improvement}")
            
            # Response breakdown
            st.subheader("📝 Response Analysis")
            responses = report_data.get('detailed_responses', [])
            
            for i, response in enumerate(responses, 1):
                with st.expander(f"Question {i}: {response.get('category', 'General').title()} (Score: {response.get('evaluation', {}).get('overall_score', 0)}/10)"):
                    st.write(f"**Question:** {response.get('question', 'N/A')}")
                    st.write(f"**Your Response:** {response.get('response_text', 'N/A')[:300]}...")
                    
                    eval_data = response.get('evaluation', {})
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Strengths:**")
                        for strength in eval_data.get('strengths', [])[:2]:
                            st.write(f"• {strength}")
                    with col2:
                        st.write("**Improvements:**")
                        for improvement in eval_data.get('improvements', [])[:2]:
                            st.write(f"• {improvement}")
            
            # Download report
            st.markdown("---")
            report_json = json.dumps(report_data, indent=2)
            st.download_button(
                label="📥 Download Full Report (JSON)",
                data=report_json,
                file_name=f"campushireai_report_{st.session_state.session_id[:8]}.json",
                mime="application/json"
            )
        
        else:
            st.error(f"❌ Failed to generate report: {report_data.get('error', 'Unknown error')}")
    
    # New interview button
    st.markdown("---")
    if st.button("🔄 Start New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Run the application
if __name__ == "__main__":
    main()
