"""
Semantic Ranker for Resume-Job Description Matching

This module provides functionality to calculate semantic similarity between
resume content and job descriptions using sentence transformers and caching.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Optional, Tuple
import hashlib
import json
import os
from pathlib import Path
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CACHE_DIR = Path(".cache/embeddings")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_NAME = 'all-MiniLM-L6-v2'  # Lightweight but effective model

class SemanticRanker:
    """
    A class to handle semantic similarity calculations between resumes and job descriptions.
    Implements caching for embeddings to improve performance.
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        """Initialize the semantic ranker with a pre-trained model."""
        self.model_name = model_name
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def _get_cache_path(self, text: str) -> Path:
        """Generate a cache file path for the given text."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return CACHE_DIR / f"{self.model_name}_{text_hash}.npy"
    
    @lru_cache(maxsize=1000)
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for the given text, using cache if available.
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy.ndarray: Text embedding vector
        """
        cache_path = self._get_cache_path(text)
        
        # Try to load from cache
        if cache_path.exists():
            try:
                embedding = np.load(cache_path)
                logger.debug(f"Loaded embedding from cache: {cache_path}")
                return embedding
            except Exception as e:
                logger.warning(f"Error loading cached embedding: {e}")
        
        # Generate and cache the embedding
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # Save to cache
            np.save(cache_path, embedding)
            logger.debug(f"Cached embedding to {cache_path}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def calculate_match_score(self, resume_data: Dict, job_description: str) -> Dict[str, float]:
        """
        Calculate matching score between resume and job description.
        
        Args:
            resume_data: Dictionary containing resume information
            job_description: Job description text
            
        Returns:
            Dict with detailed matching scores
        """
        try:
            # Create a comprehensive profile from resume data
            profile_sections = []
            
            # Add skills section
            skills = resume_data.get('skills', [])
            if skills:
                profile_sections.append(f"Skills: {', '.join(skills)}.")
            
            # Add experience section
            orgs = resume_data.get('organizations', [])
            if orgs:
                profile_sections.append(f"Worked at: {', '.join(orgs)}.")
            
            # Add any additional text if available
            if 'raw_text' in resume_data:
                profile_sections.append(resume_data['raw_text'])
            
            # Join all sections
            resume_profile = ' '.join(profile_sections)
            
            # Calculate similarity
            resume_embedding = self.get_embedding(resume_profile).reshape(1, -1)
            job_embedding = self.get_embedding(job_description).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = float(cosine_similarity(resume_embedding, job_embedding)[0][0])
            
            # Calculate skill match percentage
            job_desc_lower = job_description.lower()
            matched_skills = [skill for skill in skills 
                            if skill.lower() in job_desc_lower]
            
            skill_match = (len(matched_skills) / len(skills)) * 100 if skills else 0
            
            # Calculate overall score (weighted average)
            overall_score = (similarity * 70) + (skill_match * 30)
            
            return {
                'overall_score': min(100, max(0, overall_score)),  # Clamp between 0-100
                'semantic_similarity': similarity * 100,
                'skill_match_percentage': skill_match,
                'matched_skills': matched_skills,
                'total_skills': len(skills),
                'matched_skills_count': len(matched_skills)
            }
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            raise

# Singleton instance
semantic_ranker = SemanticRanker()

def calculate_match_score(resume_data: Dict, job_description: str) -> Dict[str, float]:
    """
    Calculate matching score between resume and job description.
    
    This is a convenience function that uses the singleton instance.
    
    Args:
        resume_data: Dictionary containing resume information
        job_description: Job description text
        
    Returns:
        Dict with detailed matching scores
    """
    return semantic_ranker.calculate_match_score(resume_data, job_description)

def create_resume_profile(resume_data: Dict) -> str:
    """
    Create a text profile from resume data.
    
    Args:
        resume_data: Dictionary containing resume information
        
    Returns:
        str: Formatted profile text
    """
    profile_sections = []
    
    # Add name and contact info if available
    if 'name' in resume_data:
        profile_sections.append(f"Candidate: {resume_data['name']}")
    if 'email' in resume_data:
        profile_sections.append(f"Contact: {resume_data['email']}")
    
    # Add skills section
    skills = resume_data.get('skills', [])
    if skills:
        profile_sections.append(f"Skills: {', '.join(skills)}.")
    
    # Add experience section
    orgs = resume_data.get('organizations', [])
    if orgs:
        profile_sections.append(f"Professional Experience: Worked at {', '.join(orgs)}.")
    
    # Add any additional text if available
    if 'raw_text' in resume_data:
        profile_sections.append(resume_data['raw_text'])
    
    return '\n'.join(profile_sections)

if __name__ == '__main__':
    # Example usage
    sample_resume_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "skills": ["python", "machine learning", "data analysis", "aws", "docker"],
        "organizations": ["Tech Corp", "Data Insights Inc"],
        "raw_text": "Experienced data scientist with 5+ years of experience in building ML models..."
    }
    
    sample_job_description = """
    We are looking for a Senior Data Scientist with strong Python skills 
    and experience in machine learning. The ideal candidate should have 
    experience with AWS and data analysis. Knowledge of Docker is a plus.
    """
    
    # Create profile and calculate match
    profile = create_resume_profile(sample_resume_data)
    print("--- Generated Resume Profile ---")
    print(profile)
    print("-" * 50)
    
    # Calculate matching score
    match_result = calculate_match_score(sample_resume_data, sample_job_description)
    print("\n--- Matching Results ---")
    print(f"Overall Match Score: {match_result['overall_score']:.1f}%")
    print(f"Semantic Similarity: {match_result['semantic_similarity']:.1f}%")
    print(f"Skill Match: {match_result['skill_match_percentage']:.1f}%")
    print(f"Matched Skills: {', '.join(match_result['matched_skills'])}")
    print("-" * 50)
