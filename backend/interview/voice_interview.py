import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv
import json
import time
import random
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
try:
    from backend.parser.extract_resume import extract_text_from_pdf, extract_entities
    from backend.matcher.semantic_ranker import create_profile, calculate_similarity
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import CampusHire modules: {e}")
    MODULES_AVAILABLE = False
load_dotenv()
genai.configure(api_key)=os.getenv("GOOGLE_API_KEY")
class campus_hire_voice_interviewer:
    """A class to conduct voice interviews using speech recognition, text-to-speech, and generative AI.
    """
    def __init__(self,candidate_reusme_path=None,job_description_path=None):
        self.model=genai.GenerativeModel('gemini-pro')
        self.recognizer=sr.Recognizer()
        self.microphone=sr.Microphone()
        self.tts_engine=pyttsx3.init()
        self.tts_engine.setProperty('rate',160)
        self.tts_engine.setProperty('volume',0.9)
        voices=self.tts_engine.getProperty('voices')
        if(len(voices)>1):
            self.tts_engine.setProperty('voice',voices[1].id)#For female voice
        self.candidate_data=None
        self.job_description=None
        self.resume_match_score=0
        if MODULES_AVAILABLE:
            if candidate_reusme_path and job_description_path:
                self.load_candidate_data(candidate_reusme_path)
                self.load_job_description(job_description_path)
        self.interview_session={
            "session_id":int(time.time()),
            "start_time":time.ctime(),
            "questions_asked":[],
            "responses":[],
            "candidate_data": self.candidate_data,
            "job_description": self.job_description,
            "resume_match_score": self.resume_match_score
        }
        self.question_categories={
            "introduction":[
                "Tell me about yourself and your background.",
                "Walk me through your resume and highlight your key experiences.",
                "What motivated you to apply for this position?"
            ]
            ,"technical":[
                "Can you explain a challenging technical problem you faced and how you solved it?",
                "Describe a project where you had to learn a new technology quickly.",
                "How do you stay updated with the latest developments in your field?"
            ]
            ,"behavioral":[
                "Describe a situation where you had to work in a team. What was your role?",
                "Tell me about a time when you faced a conflict at work. How did you handle it?",
                "Give an example of a goal you set and how you achieved it."
            ]
            ,"situational":[
                "How would you handle a situation where you have multiple high-priority tasks to complete?",
                "What would you do if you were given a project with a tight deadline and limited resources?",
                "How would you approach a situation where you disagree with your manager's decision?"
            ]
            ,"closing":[
                "Do you have any questions for me about the role or the company?",]
        }
        def load_candidate_data(self,resume_path):
            try:
                print(f"Loading candidate data from {resume_path}")
                resume_text = extract_text_from_pdf(resume_path)
                if not resume_text:
                    print("Could not extract text from resume...")
                    return 
                self.candidate_data = extract_entities(resume_text)
                if self.job_description and self.candidate_data:
                    resume_profile=create_profile(self.candidate_data) 
                    self.resume_match_score=calculate_similarity(self.job_description['profile'],resume_profile)   
                print(f"Resume loaded successfully. Candidate Name: {self.candidate_data.get('name','N/A')}, Email: {self.candidate_data.get('email','N/A')}")
                print(f"Match Score with Job Description: {self.resume_match_score:.2f}")
            except Exception as e:
                print(f"Error loading candidate data: {e}")
        def load_job_description(self, job_path):
            """Load job description from file"""
            try:
                with open(job_path, 'r', encoding='utf-8') as f:
                    self.job_description = f.read()
                    print(f"✅ Job description loaded from: {job_path}")
            except Exception as e:
                    print(f"❌ Error loading job description: {e}")
        def speak(self, text):
            """Convert text to speech with enhanced output"""
            print(f"\n🤖 AI Interviewer: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        def listen(self, timeout=15, phrase_time_limit=60):
            """Listen to user's speech and convert it to text"""
            print("\nListening to user's speach...")
            try:
                with self.microphone as source:
                    print(f"\n🎤 Listening... (speak clearly, up to {phrase_time_limit} seconds)")
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio=self.recognizer.listen(source,timeout=timeout,phrase_time_limit=phrase_time_limit)
                    print("Processing your response....")
                    text=self.recognizer.recognize_google(audio)
                    print(f"Candidate:{text}")
                    return text
                
            except sr.WaitTimeoutError:
                return "TIMEOUT"
            except sr.UnknownValueError:
                return "UNCLEAR"
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
            return "ERROR"
        def generate_personlized_question(self,category, previous_responses=None):
            context = f"Job Requirements: {self.job_description[:500]}\n"
        
            if self.candidate_data:
                context += f"Candidate Skills: {', '.join(self.candidate_data.get('skills', []))}\n"
                context += f"Candidate Experience: {', '.join(self.candidate_data.get('organizations', []))}\n"
        
            if previous_responses:
                recent_responses = previous_responses[-2:]  # Last 2 responses
                context += f"Previous Responses: {[r['response'][:100] for r in recent_responses]}\n"
        
            prompt = f"""
            You are conducting a {category} interview question for a software engineering role.
        
            Context:
            {context}
            Generate ONE specific, insightful question that:
            1. Relates to the job requirements
            2. Builds on the candidate's background
            3. Explores {category} aspects
            4. Encourages detailed responses
        
            Return only the question, nothing else.
            """
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"❌ Error generating personalized question: {e}")
                # Fallback to predefined questions
                return random.choice(self.question_categories.get(category, self.question_categories["introduction"]))
        