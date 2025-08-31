from sentence_transformer import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
semantic_model=SentenceTransformer('all-MiniLM-L6-v2')
def create_profile(resume_data:dict)->str:
    skills="".join(resume_data.get("skills",[]))
    orgs="".join(resume_data.get("organizations",[]))
    profile = f"Skills: {skills}. Experience at: {orgs}."
    return profile
def calculate_similarity(resume_profile:str,job_description:str)->float:
    """Calculate cosine similarity between resume and job description."""
    profile_embeddings=semantic_model.encode(resume_profile, convert_to_tensor=True)
    job_embeddings=semantic_model.encode(job_description, convert_to_tensor=True)
    profile_embeddings = profile_embeddings.reshape(1, -1)
    job_embeddings= job_embeddings.reshape(1, -1)
    similarity=cosine_similarity(profile_embeddings, job_embeddings)[0][0]
    return float(similarity*100)
if __name__=='__main__':
    sample_resume_data={
        "name": "Goutham",
        "email": "goutham@gmail.com",
        "skills": ["python", "fastapi", "machine learning", "aws"],
        "organizations": ["Google", "Microsoft","IBM"]
    }
    sample_job_description="""
    We are looking for a Senior Machine Learning Engineer to join our team.
    The ideal candidate will have strong experience in Python and building ML models.
    Knowledge of cloud platforms like AWS or GCP is a must. 
    Experience with containerization using Docker and building APIs with FastAPI is a huge plus.
    """
    resume_profile_info=create_profile(sample_resume_data)
    print("--- Generated Resume Profile ---")
    print(resume_profile_info)
    print("-" * 30)
    
    #Matching score
    score=calculate_similarity(resume_profile_info,sample_job_description)
    print(f"Matching Score: {score:.2f}%")
    print("-" * 30)
    

