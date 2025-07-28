

from smart_resume_bot.tools import get_recent_jobs,tailor_resume,tailor_resume,compile_pdf,find_employees,infer_email,has_already_contacted,send_multiple_emails_same_person,log_contact
import hashlib
import ast
import PyPDF2
import os
from get_jd import get_job_description
import pandas as pd
# Example job row (from your find_jobs.py output)
jobs = get_recent_jobs()  # List[Dict]
jobs_df=pd.DataFrame(jobs)

jobs_df.to_csv("jobs.csv", index=False)
jobs_df = pd.read_csv("jobs.csv")
print("found jobs=",len(jobs))
# print(jobs.columns)

for job in jobs:

    company = job['company']
    role = job['title']
    job_url = job['job_url_direct'] or job['job_url']
    company_domain = job['company_url_direct'] or job['company_url']
    job_id = job['id']
    jd=job["description"]
    print(role,company)

    
    if(company in ["Bombardier","Servus Credit Union","vhr Professional Services","University of Alberta"]):
        continue

    # Filter out jobs not related to MLE, Data Scientist, or AI Engineer
    relevant_keywords = ["mle", "data scientist", "ai engineer", "machine learning engineer", "artificial intelligence engineer","ai","data science","mlops"]
    if not any(keyword in role.lower() for keyword in relevant_keywords):
        print(f"Skipping job '{role}' as it's not related to relevant keywords.")
        continue

    # 1. Extract description
    if isinstance(job_url, (float, type(None))):
        jd=""
    else:
        jd = get_job_description(job_url)
        print("jd length",len(jd))
    


    # 2. Tailor resume
    tailored_tex_path = f"resumes/{company}_{role}_resume.tex"
    tailored_tex_path=tailor_resume(jd, original_tex_file="resumes/base_resume.tex", output_file=tailored_tex_path)
    print("tailoring done")

    # 3. Compile PDF
    pdf_path = tailored_tex_path.replace(".tex", ".pdf")
    try:
        compile_pdf(tailored_tex_path)
        print("PDF compile attempted")
        
        # Validate PDF using PyPDF2
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            _ = reader.pages[0]  # Try accessing the first page
        print("PDF validated successfully")

    except Exception as e:
        print(f"[Error] PDF rendering or validation failed for {job_id}. Falling back to base_resume.pdf. Error: {e}")
        pdf_path = "resumes/base_resume.pdf"

    # 4. Employee search
    employee_names = find_employees(company)
    # print("Employees found",employee_names)
    print("employees found")
    
    # 5. Infer and dedupe emails
    for name in employee_names:
        email = infer_email(name, company)
        email=email.strip().removeprefix("```python").removesuffix("```").strip()
        t=ast.literal_eval(email)
        email=t["emails"]
        first_name=t["first_name"]
        #  print(type(job_url))
        if not email:
            continue
        if has_already_contacted(email=email, job_id=job_id):
            continue
        if not job_url or job_url=="" or job_url=='nan':
            print("No url found skipping")
            job_url=""
        if isinstance(job_url, (float, type(None))):
            print("Value is float or NoneType")
            job_url=""
        send_multiple_emails_same_person(email,first_name, job_url, pdf_path, "manthanmehta862@gmail.com", "Manthan Mehta", "zyei ogrp gnlf ojje") 
        log_contact(email=email, job_id=job_id)
