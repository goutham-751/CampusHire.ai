import pymupdf
import os
import re
import spacy
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
    # Add custom pipeline components
    if 'sentencizer' not in nlp.pipe_names:
        nlp.add_pipe('sentencizer')
    
    # Load skills from external file for better maintainability
    with open(Path(__file__).parent / 'skills.json', 'r') as f:
        SKILLS_KEYWORDS = json.load(f).get('skills', [])
    
    logger.info("Successfully loaded NLP model and skills database")
except Exception as e:
    logger.error(f"Failed to initialize NLP model: {e}")
    raise

class ResumeParser:
    """Enhanced resume parser with improved entity recognition and error handling."""
    
    def __init__(self, nlp_model):
        """Initialize the resume parser with an NLP model."""
        self.nlp = nlp_model
        self.skills = set(SKILLS_KEYWORDS)
        self.known_orgs = set(["Google", "Microsoft", "Amazon", "Facebook", "Apple", "IBM"])  # Can be loaded from a file
        
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from a PDF file with error handling."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            doc = pymupdf.open(file_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
                
            if not text.strip():
                raise ValueError("Extracted text is empty. The PDF might be scanned or corrupted.")
                
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
            
        finally:
            if 'doc' in locals():
                doc.close()
    
    def extract_name(self, text: str) -> str:
        """Extract candidate name from resume text."""
        try:
            # Look for common resume header patterns
            name_patterns = [
                r'^(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+[A-Z]\.?)?$',  # Name at start of line
                r'\b(?:Name|Full Name|Candidate)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Labeled name
            ]
            
            for line in text.split('\n'):
                line = line.strip()
                for pattern in name_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(1) if 'group' in dir(match) else match.group(0)
            
            # Fallback to NER if pattern matching fails
            doc = self.nlp(text[:1000])  # Only process first 1000 chars for performance
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text
                    
            return "Name Not Found"
            
        except Exception as e:
            logger.warning(f"Error extracting name: {e}")
            return "Name Not Found"
    
    def extract_email(self, text: str) -> str:
        """Extract email address from text."""
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            match = re.search(email_pattern, text)
            return match.group(0) if match else "Email Not Found"
        except Exception as e:
            logger.warning(f"Error extracting email: {e}")
            return "Email Not Found"
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills using both keyword matching and NLP."""
        try:
            # Convert to lowercase for case-insensitive matching
            text_lower = text.lower()
            found_skills = set()
            
            # Exact match for known skills
            for skill in self.skills:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                    found_skills.add(skill)
            
            # NER for skills
            doc = self.nlp(text)
            for token in doc:
                if token.text in self.skills and token.text not in found_skills:
                    found_skills.add(token.text)
            
            return sorted(list(found_skills))
            
        except Exception as e:
            logger.warning(f"Error extracting skills: {e}")
            return []
    
    def extract_organizations(self, text: str) -> List[str]:
        """Extract organizations from experience section."""
        try:
            orgs = set()
            
            # Look for experience section
            exp_section = self._extract_section(text, ["experience", "work history", "employment"])
            if not exp_section:
                return []
            
            # Extract organizations using NER
            doc = self.nlp(exp_section)
            for ent in doc.ents:
                if ent.label_ == "ORG" and len(ent.text.strip()) > 2:  # Filter out very short org names
                    orgs.add(ent.text.strip())
            
            return sorted(list(orgs))
            
        except Exception as e:
            logger.warning(f"Error extracting organizations: {e}")
            return []
    
    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Helper to extract a specific section from resume text."""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            # Check if this line is a section header
            if any(re.search(rf'^\s*{name}\s*$', line, re.IGNORECASE) for name in section_names):
                in_section = True
                continue
                
            # Check for next section
            if in_section and re.match(r'^\s*[A-Z][A-Z\s]+\s*$', line.strip()):
                break
                
            if in_section and line.strip():
                section_lines.append(line.strip())
        
        return '\n'.join(section_lines)
    
    def parse_resume(self, file_path: str) -> Dict:
        """Main method to parse a resume file."""
        try:
            start_time = datetime.now()
            logger.info(f"Starting resume parsing for: {file_path}")
            
            # Extract text
            text = self.extract_text_from_pdf(file_path)
            if not text:
                raise ValueError("No text could be extracted from the resume")
            
            # Extract information
            result = {
                "name": self.extract_name(text),
                "email": self.extract_email(text),
                "skills": self.extract_skills(text),
                "organizations": self.extract_organizations(text),
                "raw_text": text[:1000] + "..." if len(text) > 1000 else text,  # Store first 1000 chars
                "parse_success": True,
                "parse_time_seconds": (datetime.now() - start_time).total_seconds()
            }
            
            logger.info(f"Successfully parsed resume for: {result.get('name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing resume {file_path}: {e}")
            return {
                "parse_success": False,
                "error": str(e),
                "parse_time_seconds": (datetime.now() - start_time).total_seconds()
            }

# For backward compatibility
def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Legacy function for backward compatibility."""
    return ResumeParser(nlp).extract_text_from_pdf(file_path)

def extract_entities(text: str) -> Dict:
    """Legacy function for backward compatibility."""
    parser = ResumeParser(nlp)
    return {
        "name": parser.extract_name(text),
        "email": parser.extract_email(text),
        "skills": parser.extract_skills(text),
        "organizations": parser.extract_organizations(text)
    }
