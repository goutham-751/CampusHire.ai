import pymupdf
import os
import re
import spacy

nlp_model=spacy.load("en_core_web_sm")
SKILLS_KEYWORDS = [
    'python', 'java', 'c++', 'javascript', 'html', 'css', 'react', 'angular', 
    'vue', 'node.js', 'django', 'flask', 'fastapi', 'sql', 'nosql', 'mongodb', 
    'postgresql', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
    'pandas', 'numpy', 'data analysis', 'data science','excel','team-management','leadership','communication','problem-solving','time management','adaptability','critical thinking','creativity','collaboration','project management','public speaking','writing','research','customer service','sales','marketing','negotiation','strategic planning','financial analysis','budgeting','risk management','quality assurance','networking','cloud computing','cybersecurity','devops','agile methodologies'
]
def extract_text_from_pdf(file_path):
    try:
        doc=pymupdf.open(file_path)
        for page in doc: # iterate the document pages
            text += page.get_text() 
        doc.close()
        return text
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
def extract_entities(text):
    #Extract name 
    doc=nlp_model(text)
    name="NOT FOUND"
    for ent in doc.ents:
        if ent.label_=="PERSON":
            name=ent.text
            break
    #Extract email using regex in python (re module)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    email = match.group(0) if match else "NOT FOUND"
    skills=set()
    for skill in SKILLS_KEYWORDS:
        if re.search(r'\b'+ re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.add(skill)
    organizations=[]
    exp_pattern=r'(?i)^\s*(work experience|experience|internships|professional history|employment history)\s*$'   
    lines=text.split('\n')
    in_experience_section=False
    for line in lines:
        # Check if the line is an experience header
        if re.search(exp_pattern, line):
            in_experience_section = True
            continue
        
        # Check for other major headers that would end the experience section
        if in_experience_section and re.search(r'(?i)^\s*(education|skills|projects|awards|publications)\s*$', line):
            in_experience_section = False
            break # Stop processing once we hit the next section
            
        # If we are in the experience section, process the line
        if in_experience_section and line.strip():
            line_doc = nlp_model(line)
            for ent in line_doc.ents:
                if ent.label_ == 'ORG':
                    organizations.append(ent.text.strip()) 

    return {
        "name": name,
        "email": email,
        "skills": list(skills),
        "organizations": list(set(organizations))
    }

    
