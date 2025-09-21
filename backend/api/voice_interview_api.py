"""
CampusHire.ai Voice Interview API - Complete Integration
Enhanced with advanced scoring and reporting capabilities
"""

import os
import sys
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import tempfile
import time

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import CampusHire modules
MODULES_STATUS = {
    "parser": False,
    "matcher": False,
    "reporter": False,
    "evaluator": False
}

# Try importing core modules
try:
    from backend.parser.extract_resume import extract_text_from_pdf, extract_entities
    MODULES_STATUS["parser"] = True
    print("✅ Resume parser imported successfully")
except ImportError as e:
    print(f"⚠️ Resume parser unavailable: {e}")

try:
    from backend.matcher.semantic_ranker import create_resume_profile, calculate_match_score
    MODULES_STATUS["matcher"] = True
    print("✅ Semantic matcher imported successfully")
except ImportError as e:
    print(f"⚠️ Semantic matcher unavailable: {e}")

try:
    from backend.report.report_generator import InterviewReportGenerator
    MODULES_STATUS["reporter"] = True
    print(" Report generator imported successfully")
except ImportError as e:
    print(f"⚠️ Report generator unavailable: {e}")

# Replace the evaluator import section with this:
try:
    from backend.scoring.evaluator import InterviewEvaluator  # Fixed import path
    MODULES_STATUS["evaluator"] = True
    print(" Advanced evaluator imported successfully")
except ImportError as e:
    print(f" Advanced evaluator unavailable: {e}")


# Load environment variables
load_dotenv()
gemini_api_key = os.getenv('GEMINI_API_KEY')

if gemini_api_key:
    genai.configure(api_key="GEMINI_API_KEY")
    print("✅ Gemini AI configured successfully")
else:
    print("⚠️ Warning: GEMINI_API_KEY not found in .env file")

# Pydantic Models
class InterviewSessionCreate(BaseModel):
    job_description: Optional[str] = ""
    candidate_name: Optional[str] = ""
    num_questions: Optional[int] = 5

class QuestionRequest(BaseModel):
    session_id: str
    category: Optional[str] = "general"

class ResponseSubmission(BaseModel):
    session_id: str
    question_id: str
    response_text: str
    audio_duration: Optional[float] = 0

# Global storage
active_sessions: Dict[str, Dict] = {}
session_storage: Dict[str, Dict] = {}

class VoiceInterviewAPI:
    """
    Complete Voice Interview API for CampusHire.ai
    Integrates all modules for comprehensive interview processing
    """
    
    def __init__(self):
        # Initialize AI model
        try:
            self.model = genai.GenerativeModel('gemini-pro')
            self.ai_available = True
            print("✅ Gemini Pro model initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini model: {e}")
            self.model = None
            self.ai_available = False
        
        # Initialize advanced modules
        self.evaluator = None
        self.report_generator = None
        
        if MODULES_STATUS["evaluator"]:
            try:
                self.evaluator = InterviewEvaluator()
                print("✅ Advanced evaluator initialized")
            except Exception as e:
                print(f"❌ Evaluator initialization failed: {e}")
        
        if MODULES_STATUS["reporter"]:
            try:
                self.report_generator = InterviewReportGenerator()
                print("✅ Report generator initialized")
            except Exception as e:
                print(f"❌ Report generator initialization failed: {e}")
        
        # Enhanced question categories
        self.question_categories = {
            "introduction": [
                "Tell me about yourself and your background in software development.",
                "Walk me through your resume and highlight your most significant experiences.",
                "What motivated you to pursue a career in technology?",
                "Describe your journey from learning to code to where you are today."
            ],
            "technical": [
                "Describe the most complex technical problem you've solved recently.",
                "How do you approach system design for scalable applications?",
                "Explain your experience with different programming paradigms.",
                "Walk me through your debugging process when facing a critical issue.",
                "How do you ensure code quality and maintainability in your projects?",
                "Describe your experience with database design and optimization.",
                "What's your approach to API design and integration?"
            ],
            "behavioral": [
                "Tell me about a time when you had to work under extreme pressure.",
                "Describe a situation where you had to collaborate with a challenging team member.",
                "How do you handle technical disagreements with colleagues?",
                "Give me an example of when you had to learn a completely new technology quickly.",
                "Describe a project failure and what you learned from it.",
                "How do you balance technical debt with feature development?",
                "Tell me about a time when you mentored or helped a junior developer."
            ],
            "role_specific": [
                "What specific aspects of this role excite you the most?",
                "How would you contribute to our team's technical culture?",
                "Where do you see the future of software development heading?",
                "What's your approach to staying current with technology trends?",
                "How do you balance innovation with practical business needs?",
                "Describe your ideal working environment and team dynamics."
            ],
            "problem_solving": [
                "Walk me through how you would architect a real-time chat application.",
                "How would you optimize a slow-performing database query?",
                "Describe your approach to handling a production system outage.",
                "How would you design a system to handle millions of concurrent users?"
            ]
        }

    async def create_session(self, session_data: InterviewSessionCreate, resume_file: Optional[UploadFile] = None) -> Dict:
        """Create comprehensive interview session with full integration"""
        
        session_id = str(uuid.uuid4())
        print(f"🎯 Creating interview session: {session_id}")
        
        # Process resume with enhanced analysis
        candidate_data = None
        resume_match_score = 0
        processing_log = {
            "resume_uploaded": resume_file is not None,
            "processing_status": "no_resume",
            "extraction_successful": False,
            "match_calculation": False,
            "secure_deletion": False
        }
        
        if resume_file and MODULES_STATUS["parser"]:
            try:
                print(f"📄 Processing resume: {resume_file.filename}")
                processing_log["processing_status"] = "processing"
                
                # Secure temporary processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="secure_interview_") as temp_file:
                    content = await resume_file.read()
                    temp_file.write(content)
                    temp_path = temp_file.name
                
                print(f"📝 Extracting text from resume...")
                resume_text = extract_text_from_pdf(temp_path)
                
                if resume_text:
                    print(f"🔍 Analyzing resume content...")
                    candidate_data = extract_entities(resume_text)
                    processing_log["extraction_successful"] = True
                    
                    skills_count = len(candidate_data.get('skills', []))
                    orgs_count = len(candidate_data.get('organizations', []))
                    print(f"✅ Extracted: {skills_count} skills, {orgs_count} organizations")
                    
                    # Calculate semantic match with job description
                    if session_data.job_description and candidate_data and MODULES_STATUS["matcher"]:
                        print(f"🎯 Calculating resume-job match...")
                        resume_profile = create_resume_profile(candidate_data)
                        resume_match_score = calculate_match_score(
                            resume_profile, session_data.job_description
                        )
                        processing_log["match_calculation"] = True
                        print(f"📊 Match score: {resume_match_score:.1f}%")
                else:
                    processing_log["processing_status"] = "extraction_failed"
                
                # Secure file deletion with overwrite
                if os.path.exists(temp_path):
                    file_size = os.path.getsize(temp_path)
                    with open(temp_path, "r+b") as f:
                        f.write(os.urandom(file_size))
                        f.flush()
                        os.fsync(f.fileno())
                    os.unlink(temp_path)
                    processing_log["secure_deletion"] = True
                    print("🔒 Resume file securely deleted")
                
            except Exception as e:
                print(f"❌ Resume processing error: {e}")
                processing_log["processing_status"] = f"error: {str(e)}"
                # Ensure cleanup on error
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        # Create enhanced session object
        session = {
            "session_id": session_id,
            "candidate_name": session_data.candidate_name or "Anonymous Candidate",
            "job_description": session_data.job_description,
            "created_at": datetime.now(),
            "status": "active",
            "current_question": 0,
            "total_questions": session_data.num_questions,
            
            # Resume analysis
            "candidate_data": candidate_data,
            "resume_match_score": resume_match_score,
            "resume_processing_log": processing_log,
            
            # Interview data
            "questions_asked": [],
            "responses": [],
            "question_flow": ['introduction', 'technical', 'behavioral', 'problem_solving', 'role_specific'] * 2,
            
            # System metadata
            "modules_available": MODULES_STATUS.copy(),
            "ai_model_available": self.ai_available,
            "privacy_compliant": True,
            "data_retention_policy": "structured_data_only"
        }
        
        # Store session
        active_sessions[session_id] = session
        session_storage[session_id] = session
        
        print(f"✅ Session created for {session['candidate_name']}")
        
        return {
            "session_id": session_id,
            "status": "created",
            "candidate_data": candidate_data,
            "resume_match_score": resume_match_score,
            "resume_processing_log": processing_log,
            "total_questions": session_data.num_questions,
            "privacy_compliance": {
                "gdpr_compliant": True,
                "data_retention": "structured_metadata_only",
                "file_storage": "temporary_processing_only",
                "secure_deletion": processing_log.get("secure_deletion", False)
            },
            "system_capabilities": MODULES_STATUS,
            "message": f"Interview session ready for {session['candidate_name']}"
        }

    async def generate_question(self, session_id: str, category: Optional[str] = None) -> Dict:
        """Generate intelligent, personalized interview questions"""
        
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        session = active_sessions[session_id]
        
        if session["status"] != "active":
            raise HTTPException(status_code=400, detail="Interview session is not active")
        
        current_q_num = session["current_question"]
        
        # Check completion
        if current_q_num >= session["total_questions"]:
            session["status"] = "completed"
            return {
                "status": "interview_completed",
                "session_id": session_id,
                "message": "Interview completed successfully! Ready for comprehensive analysis.",
                "summary": {
                    "total_questions": session["total_questions"],
                    "responses_collected": len(session.get("responses", [])),
                    "candidate": session["candidate_name"]
                }
            }
        
        # Determine question category intelligently
        if not category:
            flow = session["question_flow"]
            if current_q_num < len(flow):
                category = flow[current_q_num]
            else:
                # Fallback for extra questions
                category = "technical" if current_q_num % 2 == 0 else "behavioral"
        
        # Generate question
        if current_q_num == 0:
            question_text = "Hello! Thank you for taking the time to interview with us today. To start, please tell me about yourself, your background, and what brings you to this opportunity."
        else:
            question_text = await self._generate_intelligent_question(
                category,
                session["job_description"],
                session["candidate_data"],
                session.get("responses", [])
            )
        
        # Create question object with metadata
        question_id = str(uuid.uuid4())
        question_obj = {
            "question_id": question_id,
            "question_text": question_text,
            "category": category,
            "question_number": current_q_num + 1,
            "generated_at": datetime.now().isoformat(),
            "personalization_used": session["candidate_data"] is not None,
            "ai_generated": self.ai_available
        }
        
        # Update session
        session["questions_asked"].append(question_obj)
        session["current_question"] = current_q_num + 1
        
        print(f"❓ Q{current_q_num + 1}/{session['total_questions']} ({category}) for {session_id[:8]}...")
        
        return {
            "question_id": question_id,
            "question_text": question_text,
            "category": category,
            "question_number": current_q_num + 1,
            "remaining_questions": session["total_questions"] - (current_q_num + 1),
            "total_questions": session["total_questions"],
            "progress_percentage": round(((current_q_num + 1) / session["total_questions"]) * 100, 1),
            "personalized": session["candidate_data"] is not None
        }

    async def _generate_intelligent_question(self, category: str, job_description: str,
                                           candidate_data: Dict, previous_responses: List) -> str:
        """Generate AI-powered intelligent questions with context awareness"""
        
        if not self.ai_available:
            import random
            return random.choice(self.question_categories.get(category, self.question_categories["introduction"]))
        
        # Build comprehensive context
        context_parts = []
        
        if job_description:
            context_parts.append(f"Job Requirements: {job_description[:600]}")
        
        if candidate_data:
            skills = candidate_data.get('skills', [])[:15]  # Top 15 skills
            orgs = candidate_data.get('organizations', [])[:8]  # Top 8 organizations
            
            if skills:
                context_parts.append(f"Candidate Skills: {', '.join(skills)}")
            if orgs:
                context_parts.append(f"Work Experience: {', '.join(orgs)}")
        
        if previous_responses:
            recent_topics = []
            for response in previous_responses[-3:]:  # Last 3 responses
                resp_preview = response.get('response_text', '')[:150]
                if resp_preview:
                    recent_topics.append(f"- {response.get('category', 'General')}: {resp_preview}")
            
            if recent_topics:
                context_parts.append(f"Recent Discussion:\n{chr(10).join(recent_topics)}")
        
        context = "\n\n".join(context_parts)
        
        # Create intelligent prompt
        prompt = f"""
        You are conducting a {category} interview for a software engineering position.
        Generate ONE specific, insightful interview question.

        Context:
        {context}

        Requirements for the question:
        1. Category: {category.title()} focus
        2. Encourage specific examples and detailed responses
        3. Build naturally on the candidate's background
        4. Be conversational yet professional
        5. Avoid repetition of recent topics
        6. Probe for technical depth and real experience
        7. Allow candidate to showcase their strengths

        Generate only the question text - no explanations or additional content.
        """

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=150,
                    temperature=0.7
                )
            )
            
            generated_question = response.text.strip()
            
            # Clean and validate
            if generated_question.startswith('"') and generated_question.endswith('"'):
                generated_question = generated_question[1:-1]
            
            if len(generated_question) < 15 or '?' not in generated_question:
                raise ValueError("Generated question too short or invalid format")
            
            return generated_question
            
        except Exception as e:
            print(f"❌ AI question generation failed: {e}")
            # Fallback to curated questions
            import random
            return random.choice(self.question_categories.get(category, self.question_categories["introduction"]))

    async def submit_response(self, response_data: ResponseSubmission) -> Dict:
        """Process response with advanced evaluation and analysis"""
        
        if response_data.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        session = active_sessions[response_data.session_id]
        
        # Find corresponding question
        question = None
        for q in session["questions_asked"]:
            if q["question_id"] == response_data.question_id:
                question = q
                break
        
        if not question:
            raise HTTPException(status_code=400, detail="Question not found for this response")
        
        print(f"📝 Processing response for Q{question['question_number']} ({question['category']})")
        
        # AI-powered evaluation
        ai_evaluation = await self._evaluate_with_ai(
            question["question_text"],
            response_data.response_text,
            question["category"]
        )
        
        # Advanced evaluation if available
        comprehensive_evaluation = ai_evaluation
        if self.evaluator and MODULES_STATUS["evaluator"]:
            try:
                comprehensive_evaluation = self.evaluator.evaluate_response_comprehensively(
                    question["question_text"],
                    response_data.response_text,
                    question["category"],
                    ai_evaluation
                )
                print("✅ Advanced evaluation completed")
            except Exception as e:
                print(f"⚠️ Advanced evaluation failed, using AI evaluation: {e}")
        
        # Create comprehensive response object
        response_obj = {
            "question_id": response_data.question_id,
            "response_text": response_data.response_text,
            "audio_duration": response_data.audio_duration,
            "submitted_at": datetime.now().isoformat(),
            
            # Question context
            "question": question["question_text"],
            "category": question["category"],
            "question_number": question["question_number"],
            
            # Evaluations
            "evaluation": comprehensive_evaluation,
            "ai_evaluation": ai_evaluation,
            
            # Response analytics
            "response_analytics": {
                "word_count": len(response_data.response_text.split()),
                "character_count": len(response_data.response_text),
                "estimated_speaking_time": len(response_data.response_text.split()) * 0.5,  # Rough estimate
                "response_completeness": min(1.0, len(response_data.response_text.split()) / 50)  # Based on 50 words as "complete"
            }
        }
        
        session["responses"].append(response_obj)
        
        # Generate intelligent feedback
        score = comprehensive_evaluation.get("final_overall_score", comprehensive_evaluation.get("overall_score", 5))
        
        feedback_messages = {
            "excellent": [
                "Excellent response! Your detailed explanation and specific examples really demonstrate strong experience in this area.",
                "Outstanding answer! The technical depth and practical examples you provided show impressive expertise.",
                "Fantastic response! Your approach shows both technical competence and strategic thinking."
            ],
            "good": [
                "Great response! You provided good insights and relevant examples that show your experience clearly.",
                "Nice answer! Your explanation demonstrates solid understanding and practical knowledge.",
                "Good response! The examples you shared effectively illustrate your capabilities."
            ],
            "average": [
                "Thank you for that response. Consider adding more specific examples to strengthen your answer.",
                "I appreciate your answer. Adding more technical details or metrics would make it even stronger.",
                "Good start on that response. More concrete examples would help demonstrate your experience better."
            ],
            "below_average": [
                "Thank you for sharing that. In future responses, try to include specific examples and more detailed explanations.",
                "I appreciate your input. Consider providing more depth and concrete examples to showcase your experience.",
                "Thanks for your response. Adding specific situations and outcomes would strengthen your answers."
            ]
        }
        
        if score >= 8:
            feedback_category = "excellent"
        elif score >= 6:
            feedback_category = "good"
        elif score >= 4:
            feedback_category = "average"
        else:
            feedback_category = "below_average"
        
        import random
        feedback = random.choice(feedback_messages[feedback_category])
        
        print(f"📊 Response scored: {score:.1f}/10")
        
        return {
            "status": "response_recorded",
            "evaluation_score": round(score, 1),
            "feedback": feedback,
            "detailed_evaluation": {
                "overall_score": score,
                "technical_depth": comprehensive_evaluation.get("technical_depth", 3),
                "communication_clarity": comprehensive_evaluation.get("communication_clarity", 3),
                "key_strengths": comprehensive_evaluation.get("strengths", [])[:2],
                "improvement_suggestions": comprehensive_evaluation.get("improvements", [])[:2]
            },
            "response_analytics": response_obj["response_analytics"],
            "next_action": "continue" if session["current_question"] < session["total_questions"] else "complete",
            "progress": {
                "current": session["current_question"],
                "total": session["total_questions"],
                "percentage": round((session["current_question"] / session["total_questions"]) * 100, 1)
            }
        }

    async def _evaluate_with_ai(self, question: str, response: str, category: str) -> Dict:
        """Enhanced AI-powered response evaluation"""
        
        if not self.ai_available:
            # Basic fallback evaluation
            word_count = len(response.split())
            return {
                "overall_score": min(7, max(3, 3 + word_count // 20)),
                "technical_depth": 3,
                "communication_clarity": 3,
                "relevance_to_role": 3,
                "specific_examples": 2 if "example" in response.lower() or "project" in response.lower() else 1,
                "strengths": ["Provided response"],
                "improvements": ["Could provide more detail"],
                "brief_feedback": "Thank you for your response."
            }
        
        evaluation_prompt = f"""
        You are an expert technical interviewer evaluating this candidate response.

        Interview Context:
        - Category: {category}
        - Question: "{question}"
        - Candidate Response: "{response}"

        Evaluate across these dimensions and provide valid JSON only:

        {{
            "overall_score": [1-10 integer],
            "technical_depth": [1-5 integer],
            "communication_clarity": [1-5 integer],
            "relevance_to_role": [1-5 integer],
            "specific_examples": [1-5 integer],
            "problem_solving_approach": [1-5 integer],
            "strengths": ["strength1", "strength2", "strength3"],
            "improvements": ["improvement1", "improvement2"],
            "technical_keywords_used": ["keyword1", "keyword2"],
            "demonstrates_experience": [true/false],
            "shows_leadership": [true/false],
            "mentions_metrics": [true/false],
            "brief_feedback": "Constructive feedback for candidate (2-3 sentences)"
        }}

        Scoring Guidelines:
        - Overall: 8-10 (exceptional), 6-7 (good), 4-5 (average), 1-3 (poor)
        - Consider depth, clarity, examples, and relevance
        - Be objective but constructive
        - Look for specific experiences and concrete examples
        """

        try:
            response_obj = self.model.generate_content(
                evaluation_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=400,
                    temperature=0.3
                )
            )
            
            response_text = response_obj.text.strip()
            
            # Extract and validate JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                evaluation = json.loads(json_str)
                
                # Validate and constrain scores
                evaluation["overall_score"] = max(1, min(10, evaluation.get("overall_score", 5)))
                evaluation["technical_depth"] = max(1, min(5, evaluation.get("technical_depth", 3)))
                evaluation["communication_clarity"] = max(1, min(5, evaluation.get("communication_clarity", 3)))
                evaluation["relevance_to_role"] = max(1, min(5, evaluation.get("relevance_to_role", 3)))
                evaluation["specific_examples"] = max(1, min(5, evaluation.get("specific_examples", 2)))
                evaluation["problem_solving_approach"] = max(1, min(5, evaluation.get("problem_solving_approach", 3)))
                
                # Ensure required fields exist
                evaluation["strengths"] = evaluation.get("strengths", ["Provided response"])[:3]
                evaluation["improvements"] = evaluation.get("improvements", ["Could provide more detail"])[:3]
                evaluation["technical_keywords_used"] = evaluation.get("technical_keywords_used", [])[:5]
                evaluation["brief_feedback"] = evaluation.get("brief_feedback", "Thank you for your response.")
                
                return evaluation
            else:
                raise ValueError("Invalid JSON format in AI response")
                
        except Exception as e:
            print(f"❌ AI evaluation failed: {e}")
            # Enhanced fallback evaluation
            word_count = len(response.split())
            has_examples = any(word in response.lower() for word in ['example', 'project', 'experience', 'when i', 'i worked'])
            has_technical_terms = any(word in response.lower() for word in ['algorithm', 'database', 'api', 'framework', 'architecture'])
            
            return {
                "overall_score": min(8, max(3, 4 + (word_count // 30) + (2 if has_examples else 0) + (1 if has_technical_terms else 0))),
                "technical_depth": 4 if has_technical_terms else 3,
                "communication_clarity": 4 if word_count > 50 else 3,
                "relevance_to_role": 4 if word_count > 40 else 3,
                "specific_examples": 4 if has_examples else 2,
                "problem_solving_approach": 3,
                "strengths": ["Provided detailed response" if word_count > 50 else "Addressed the question"],
                "improvements": ["Could include more specific examples" if not has_examples else "Could provide more technical depth"],
                "technical_keywords_used": [],
                "demonstrates_experience": has_examples,
                "shows_leadership": "lead" in response.lower() or "manage" in response.lower(),
                "mentions_metrics": any(char.isdigit() for char in response),
                "brief_feedback": "Thank you for sharing your experience. Consider providing more specific examples and technical details."
            }

    async def generate_final_report(self, session_id: str) -> Dict:
        """Generate comprehensive final interview report with all analytics"""
        
        if session_id not in session_storage:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        session = session_storage[session_id]
        
        if not session.get("responses"):
            return {
                "error": "No interview responses available for analysis",
                "session_id": session_id,
                "status": "insufficient_data"
            }
        
        print(f"📊 Generating comprehensive report for {session_id[:8]}...")
        
        responses = session["responses"]
        
        # Calculate comprehensive metrics
        performance_metrics = self._calculate_performance_metrics(responses)
        
        # Advanced analytics if evaluator available
        advanced_analytics = {}
        if self.evaluator and MODULES_STATUS["evaluator"]:
            try:
                advanced_analytics = self.evaluator.calculate_interview_aggregate_scores(responses)
                insights = self.evaluator.generate_scoring_insights(advanced_analytics)
                advanced_analytics["insights"] = insights
                print("✅ Advanced analytics generated")
            except Exception as e:
                print(f"⚠️ Advanced analytics failed: {e}")
        
        # Calculate session duration
        start_time = session["created_at"]
        end_time = datetime.now()
        duration_minutes = (end_time - start_time).total_seconds() / 60
        
        # Compile comprehensive report
        comprehensive_report = {
            "session_metadata": {
                "session_id": session_id,
                "candidate_name": session["candidate_name"],
                "interview_date": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "completion_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_minutes": round(duration_minutes, 1),
                "questions_answered": len(responses),
                "total_questions_planned": session["total_questions"],
                "completion_rate": round((len(responses) / session["total_questions"]) * 100, 1),
                "interview_type": "AI-Powered Voice Interview"
            },
            
            "performance_metrics": performance_metrics,
            
            "resume_analysis": {
                "resume_uploaded": session.get("candidate_data") is not None,
                "resume_match_score": session.get("resume_match_score", 0),
                "processing_status": session.get("resume_processing_log", {}).get("processing_status", "no_resume"),
                "extracted_skills": session.get("candidate_data", {}).get("skills", [])[:15] if session.get("candidate_data") else [],
                "work_experience": session.get("candidate_data", {}).get("organizations", [])[:8] if session.get("candidate_data") else [],
                "privacy_compliant": session.get("privacy_compliant", True)
            },
            
            "response_analysis": {
                "category_breakdown": self._analyze_responses_by_category(responses),
                "communication_patterns": self._analyze_communication_patterns(responses),
                "technical_assessment": self._analyze_technical_competence(responses),
                "behavioral_insights": self._analyze_behavioral_responses(responses)
            },
            
            "qualitative_assessment": self._generate_qualitative_assessment(responses, performance_metrics),
            
            "final_assessment": self._generate_final_assessment(performance_metrics, session),
            
            "detailed_responses": responses,  # Complete response data
            
            "system_metadata": {
                "evaluation_engine": "CampusHire.ai Advanced Analytics",
                "ai_model": "Google Gemini Pro" if self.ai_available else "Rule-based fallback",
                "modules_used": [name for name, available in MODULES_STATUS.items() if available],
                "privacy_policy": "Structured data only - original files securely deleted",
                "report_generated_at": datetime.now().isoformat()
            }
        }
        
        # Add advanced analytics if available
        if advanced_analytics:
            comprehensive_report["advanced_analytics"] = advanced_analytics
        
        # Generate formatted reports if report generator available
        if self.report_generator and MODULES_STATUS["reporter"]:
            try:
                saved_reports = self.report_generator.save_report(comprehensive_report, "all")
                comprehensive_report["saved_reports"] = saved_reports
                print(f"✅ Formatted reports saved: {list(saved_reports.keys())}")
            except Exception as e:
                print(f"⚠️ Report generation failed: {e}")
        
        print(f"🎯 Report generated: {performance_metrics.get('recommendation', 'Under Review')}")
        
        return comprehensive_report

    # Helper methods for comprehensive analysis
    
    def _calculate_performance_metrics(self, responses: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        if not responses:
            return {"error": "No responses to analyze"}
        
        # Extract scores
        overall_scores = []
        technical_scores = []
        communication_scores = []
        
        for response in responses:
            eval_data = response.get("evaluation", {})
            overall_scores.append(eval_data.get("overall_score", 5))
            technical_scores.append(eval_data.get("technical_depth", 3))
            communication_scores.append(eval_data.get("communication_clarity", 3))
        
        # Calculate averages and statistics
        avg_overall = sum(overall_scores) / len(overall_scores)
        avg_technical = sum(technical_scores) / len(technical_scores)
        avg_communication = sum(communication_scores) / len(communication_scores)
        
        # Score distribution
        excellent_responses = len([s for s in overall_scores if s >= 8])
        good_responses = len([s for s in overall_scores if 6 <= s < 8])
        average_responses = len([s for s in overall_scores if 4 <= s < 6])
        weak_responses = len([s for s in overall_scores if s < 4])
        
        # Determine recommendation
        if avg_overall >= 8:
            recommendation = "Strong Hire"
            confidence = "High"
        elif avg_overall >= 7:
            recommendation = "Hire"
            confidence = "High"
        elif avg_overall >= 6:
            recommendation = "Hire"
            confidence = "Medium"
        elif avg_overall >= 5:
            recommendation = "Maybe"
            confidence = "Medium"
        else:
            recommendation = "Pass"
            confidence = "High"
        
        return {
            "overall_score": round(avg_overall, 1),
            "technical_competency": round(avg_technical, 1),
            "communication_skills": round(avg_communication, 1),
            "consistency_score": round(1 - (max(overall_scores) - min(overall_scores)) / 10, 2),
            "score_distribution": {
                "excellent_responses": excellent_responses,
                "good_responses": good_responses,
                "average_responses": average_responses,
                "weak_responses": weak_responses
            },
            "recommendation": recommendation,
            "confidence_level": confidence,
            "hire_probability": round(min(100, max(0, (avg_overall - 3) * 20)), 1)
        }
    
    def _analyze_responses_by_category(self, responses: List[Dict]) -> Dict:
        """Analyze performance by question category"""
        
        category_analysis = {}
        
        for response in responses:
            category = response.get("category", "general")
            score = response.get("evaluation", {}).get("overall_score", 5)
            
            if category not in category_analysis:
                category_analysis[category] = {"scores": [], "count": 0}
            
            category_analysis[category]["scores"].append(score)
            category_analysis[category]["count"] += 1
        
        # Calculate averages per category
        for category, data in category_analysis.items():
            data["average_score"] = sum(data["scores"]) / len(data["scores"])
            data["performance_level"] = (
                "Excellent" if data["average_score"] >= 8 else
                "Good" if data["average_score"] >= 6 else
                "Average" if data["average_score"] >= 4 else
                "Needs Improvement"
            )
        
        return category_analysis
    
    def _analyze_communication_patterns(self, responses: List[Dict]) -> Dict:
        """Analyze communication patterns and style"""
        
        total_words = 0
        total_responses = len(responses)
        response_lengths = []
        
        for response in responses:
            word_count = response.get("response_analytics", {}).get("word_count", 0)
            total_words += word_count
            response_lengths.append(word_count)
        
        avg_response_length = total_words / max(total_responses, 1)
        
        return {
            "average_response_length": round(avg_response_length, 1),
            "total_words": total_words,
            "response_consistency": round(1 - (max(response_lengths) - min(response_lengths)) / max(max(response_lengths), 1), 2),
            "communication_style": (
                "Detailed and thorough" if avg_response_length > 80 else
                "Balanced and clear" if avg_response_length > 40 else
                "Concise" if avg_response_length > 20 else
                "Brief responses"
            )
        }
    
    def _analyze_technical_competence(self, responses: List[Dict]) -> Dict:
        """Analyze technical competence across responses"""
        
        technical_responses = [r for r in responses if r.get("category") == "technical"]
        
        if not technical_responses:
            return {"technical_questions_answered": 0, "assessment": "No technical questions answered"}
        
        technical_scores = [r.get("evaluation", {}).get("technical_depth", 3) for r in technical_responses]
        avg_technical_depth = sum(technical_scores) / len(technical_scores)
        
        # Count technical keywords mentioned
        all_keywords = []
        for response in technical_responses:
            keywords = response.get("evaluation", {}).get("technical_keywords_used", [])
            all_keywords.extend(keywords)
        
        return {
            "technical_questions_answered": len(technical_responses),
            "average_technical_depth": round(avg_technical_depth, 1),
            "technical_keywords_mentioned": len(set(all_keywords)),
            "technical_competency_level": (
                "Expert" if avg_technical_depth >= 4.5 else
                "Advanced" if avg_technical_depth >= 3.5 else
                "Intermediate" if avg_technical_depth >= 2.5 else
                "Beginner"
            )
        }
    
    def _analyze_behavioral_responses(self, responses: List[Dict]) -> Dict:
        """Analyze behavioral and soft skills"""
        
        behavioral_responses = [r for r in responses if r.get("category") in ["behavioral", "role_specific"]]
        
        if not behavioral_responses:
            return {"behavioral_assessment": "Limited behavioral data"}
        
        shows_leadership = sum(1 for r in behavioral_responses 
                             if r.get("evaluation", {}).get("shows_leadership", False))
        
        demonstrates_experience = sum(1 for r in behavioral_responses 
                                    if r.get("evaluation", {}).get("demonstrates_experience", False))
        
        return {
            "behavioral_responses": len(behavioral_responses),
            "leadership_indicators": shows_leadership,
            "experience_demonstrated": demonstrates_experience,
            "soft_skills_assessment": (
                "Strong leadership and experience" if shows_leadership >= 2 and demonstrates_experience >= 2 else
                "Good interpersonal skills" if demonstrates_experience >= 1 else
                "Basic soft skills demonstrated"
            )
        }
    
    def _generate_qualitative_assessment(self, responses: List[Dict], performance_metrics: Dict) -> Dict:
        """Generate qualitative assessment summary"""
        
        # Collect all strengths and improvements
        all_strengths = []
        all_improvements = []
        
        for response in responses:
            eval_data = response.get("evaluation", {})
            all_strengths.extend(eval_data.get("strengths", []))
            all_improvements.extend(eval_data.get("improvements", []))
        
        # Get unique top items
        top_strengths = list(dict.fromkeys(all_strengths))[:5]
        key_improvements = list(dict.fromkeys(all_improvements))[:3]
        
        # Find standout responses
        standout_responses = [
            {
                "question_number": r["question_number"],
                "category": r["category"],
                "score": r["evaluation"]["overall_score"],
                "highlight": r["question"][:100] + "..."
            }
            for r in responses if r.get("evaluation", {}).get("overall_score", 0) >= 8
        ][:3]
        
        return {
            "top_strengths": top_strengths,
            "key_improvement_areas": key_improvements,
            "standout_responses": standout_responses,
            "overall_impression": self._generate_overall_impression(performance_metrics)
        }
    
    def _generate_overall_impression(self, performance_metrics: Dict) -> str:
        """Generate overall impression summary"""
        
        score = performance_metrics.get("overall_score", 5)
        consistency = performance_metrics.get("consistency_score", 0.5)
        
        if score >= 8 and consistency >= 0.8:
            return "Exceptional candidate with consistently high performance across all areas. Demonstrates strong technical skills and excellent communication."
        elif score >= 7 and consistency >= 0.7:
            return "Strong candidate with solid performance. Shows good technical competency and effective communication skills."
        elif score >= 6:
            return "Competent candidate with decent performance. Has potential but may need some development in key areas."
        elif score >= 4:
            return "Average candidate with mixed performance. Shows some promise but requires significant development."
        else:
            return "Candidate performance below expectations. Would need substantial development to meet role requirements."
    
    def _generate_final_assessment(self, performance_metrics: Dict, session: Dict) -> Dict:
        """Generate final hiring assessment and recommendations"""
        
        overall_score = performance_metrics.get("overall_score", 5)
        recommendation = performance_metrics.get("recommendation", "Under Review")
        
        # Generate key decision factors
        decision_factors = [
            f"Overall interview performance: {overall_score:.1f}/10",
            f"Technical competency level: {performance_metrics.get('technical_competency', 3):.1f}/5",
            f"Communication effectiveness: {performance_metrics.get('communication_skills', 3):.1f}/5"
        ]
        
        if session.get("resume_match_score", 0) > 0:
            decision_factors.append(f"Resume-job alignment: {session['resume_match_score']:.1f}%")
        
        # Generate next steps
        if recommendation in ["Strong Hire", "Hire"]:
            next_steps = [
                "Proceed with reference checks",
                "Schedule final interview round",
                "Prepare job offer discussion"
            ]
        elif recommendation == "Maybe":
            next_steps = [
                "Conduct additional technical assessment",
                "Schedule follow-up interview",
                "Discuss with hiring team for consensus"
            ]
        else:
            next_steps = [
                "Provide constructive feedback to candidate",
                "Consider for future opportunities with development",
                "Update candidate tracking system"
            ]
        
        return {
            "final_recommendation": recommendation,
            "confidence_level": performance_metrics.get("confidence_level", "Medium"),
            "hire_probability": performance_metrics.get("hire_probability", 50),
            "key_decision_factors": decision_factors,
            "recommended_next_steps": next_steps,
            "salary_band_recommendation": self._suggest_salary_band(overall_score),
            "onboarding_focus_areas": self._suggest_onboarding_focus(performance_metrics)
        }
    
    def _suggest_salary_band(self, overall_score: float) -> str:
        """Suggest salary band based on performance"""
        
        if overall_score >= 8.5:
            return "Top of band - exceptional candidate"
        elif overall_score >= 7.5:
            return "Upper band - strong performer"
        elif overall_score >= 6.5:
            return "Mid band - solid contributor"
        elif overall_score >= 5.5:
            return "Lower-mid band - growth potential"
        else:
            return "Entry level - requires development"
    
    def _suggest_onboarding_focus(self, performance_metrics: Dict) -> List[str]:
        """Suggest onboarding focus areas"""
        
        focus_areas = []
        
        technical_score = performance_metrics.get("technical_competency", 3)
        communication_score = performance_metrics.get("communication_skills", 3)
        
        if technical_score < 3.5:
            focus_areas.append("Technical skills development and mentoring")
        
        if communication_score < 3.5:
            focus_areas.append("Communication and presentation skills")
        
        if performance_metrics.get("consistency_score", 1) < 0.6:
            focus_areas.append("Building confidence and consistency")
        
        if not focus_areas:
            focus_areas.append("Standard onboarding - candidate shows strong readiness")
        
        return focus_areas

# Initialize the enhanced API
interview_api = VoiceInterviewAPI()
