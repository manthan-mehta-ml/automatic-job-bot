import subprocess
import os
import requests
import time
import csv
import re
from jobspy import scrape_jobs
API_KEY = os.getenv("google_api_key")
CX_ID = os.getenv("cx_id")

def get_unique_word_diff(text1, text2):
    # Basic word tokenization (case-insensitive, alphanumeric)
    tokenize = lambda t: set(re.findall(r"\b\w+\b", t.lower()))

    words1 = tokenize(text1)
    words2 = tokenize(text2)

    only_in_1 = words1 - words2
    only_in_2 = words2 - words1
    in_both = words1 & words2

    return {
        "only_in_text1": len(sorted(only_in_1)),
        "only_in_text2": len(sorted(only_in_2)),
        "common_words": len(sorted(in_both))
    }

def get_recent_jobs():
    jobs = scrape_jobs(
        # site_name=["linkedin", "google"],
        site_names=["linkedin"],
        search_term="Data Scientist",
        google_search_term="Data Scientist jobs Canada since yesterday",
        location="Canada",
        results_wanted=40,
        hours_old=24,
        country_indeed="canada",
    )
    return jobs.to_dict(orient='records')  # list of dicts

def tailor_resume(jd_text, original_tex_file,output_file):
    # print("jd text",jd_text)
    with open(original_tex_file, "r") as f:
        resume_text = f.read().replace("\\", "\\\\")  # Escape LaTeX backslashes
    response = client.chat.completions.create(model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a resume optimizer..."},
        {"role": "user", "content": 

f"""You are given a LaTeX resume file. Your task is to tailor it to the job description below.

Only modify the following sections: **Experience**, **Skills**, and **Summary**.

Guidelines:
- First extract keywords from the jd, and remove irrelevant sections.
- Do no cut any sections including education or the name of the person to whom the resume belongs to.
- Dont add full forms of whatever is mentioned in the resume.
- Add or modify bullet points between job description, and the resume to ensure **at least 95% keyword match** with the job description.
- For a ML Engineer role important key words would be [GenAI, Modeling, S3, AWS, docker, Software developent, SQL, Snowflake], and similar.
- Make sure the new compiled resume has as many key words from job description as possible, but make sure the sentence that you compile should make sense.
- You **must** increase the number of relevant, impactful sentences if the original resume is missing key qualifications.
- Introduce new bullet points that reflect the responsibilities, technologies, and qualifications in the job description—even if they weren't originally listed.
- Ensure that the resume fits in 1 page when compiled over a pdf, and any section is not cut.
- Emphasize **measurable impact** (e.g., "reduced cost by 20%", "improved model AUC to 0.92").
- Ensure valid LaTeX syntax: special characters like `$`, `%`, `_`, `&`, `#`, braces must be **escaped with a backslash** (`\`) so the file compiles without error.
- Do **not** include any extra explanation, commentary, or formatting wrappers like ```latex or triple backticks.
- Only return the final, complete LaTeX file as output.
- Ensure that the number of sentences are not lesser in the new resume than the original resume.
- After compiling make sure that the page length is not more than 1 page.

Job Description:
{jd_text}

Resume:
{resume_text}

"""},
    ])
    tailored_latex = response.choices[0].message.content
    tailored_latex = tailored_latex.strip().removeprefix("```latex").removesuffix("```").strip()
    diff=get_unique_word_diff(tailored_latex,jd_text)
    print(diff)
    with open(f"{output_file}", "w") as f:
        f.write(tailored_latex)



def compile_pdf(tex_file_path, cleanup_aux_files=True):
    """
    Compiles a LaTeX .tex file into a .pdf using pdflatex.

    Args:
        tex_file_path (str): Path to the .tex file
        cleanup_aux_files (bool): Whether to delete .aux/.log files

    Returns:
        str: Path to the compiled PDF, or None if failed
    """
    tex_dir = "/home/manthan/portfolio/job_search/resumes"
    tex_filename = os.path.join("/home/manthan/portfolio/job_search/", tex_file_path)
    pdf_filename = tex_file_path.replace(".tex", ".pdf")
    pdf_path = os.path.join("/home/manthan/portfolio/job_search", pdf_filename)
    print(pdf_path)
    try:
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_filename],
            cwd=tex_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )

        if result.returncode != 0:
            print("❌ LaTeX compilation failed:")
            print(result.stdout.decode())
            return None

        if cleanup_aux_files:
            for ext in [".aux", ".log", ".out"]:
                aux_path = tex_file_path.replace(".tex", ext)
                if os.path.exists(aux_path):
                    os.remove(aux_path)

        return pdf_path

    except subprocess.TimeoutExpired:
        print("❌ LaTeX compilation timed out.")
        return None

def find_employees(company):


    
    query = f'site:linkedin.com/in/ "{company}" ("machine learning engineer" OR "data scientist" OR "AI engineer")'
    ld=[]
    MAX_PAGES = 1  # Each page = 10 results
    for i in range(MAX_PAGES):
        start = 1 + (i * 10)
        print(f"Fetching page {i+1} (start={start})...")
        data = search_google(query,API_KEY,CX_ID, start)
        leads = parse_results(data)
        if len(leads)==0:
            ld=ld+[]
        else:
            ld=ld+[l["name"] for l in leads]
        # save_to_csv(leads)
        time.sleep(5)  # prevent rate limit
    return ld


def search_google(query,API_KEY,CX_ID, start_index=1):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX_ID,
        "q": query,
        "start": start_index,
    }
    response = requests.get(url, params=params)
    return response.json()

def parse_results(results):
    parsed = []
    for item in results.get("items", []):
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")
        parsed.append({
            "name": title,
            "link": link,
            "snippet": snippet
        })
    return parsed

def save_to_csv(data, filename="linkedin_leads.csv"):
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "link", "snippet"])
        if file.tell() == 0:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

# Main loop
from openai import OpenAI

client = OpenAI()

def get_company_domain(company_name):
    query = f"{company_name} official site"
    try:
        for url in search_google(query,API_KEY,CX_ID):
            domain = extract_domain(url)
            if domain and not any(x in domain for x in ["linkedin", "glassdoor", "wikipedia", "facebook"]):
                return domain
    except Exception as e:
        print(f"❌ Error fetching domain for {company_name}: {e}")
    return None

def extract_domain(url):
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if match:
        return match.group(1)
    return None

def infer_email(name, company_name):
    # domain = get_company_domain(company_name)
    # print(domain)
    # if not domain:
    #     print(f"❌ Could not resolve domain for: {company_name}")
    #     return None

    prompt = f"""
You are an assistant that infers corporate email formats.
Given a full name (which may include titles or descriptors) and a company name, infer the most likely corporate email formats.

- Extract and clean the person's **first name**.
- Return only a **Python dictionary** with two keys:
  - `"first_name"`: cleaned first name in lowercase
  - `"emails"`: a list of up to 4 inferred valid email addresses as strings
- The domain must be the most likely domain for the given company.
- Only include lowercase, valid formats like: "firstname.lastname@company.com", "flastname@company.com"
- Do NOT include any explanation or extra text.

Name: {name}
Company Name: {company_name}
    
    """

    try:
        response = client.chat.completions.create(model="gpt-4o",
        messages=[{"role": "user", "content": prompt}])
        email = response.choices[0].message.content.strip()
        if "@" in email and "." in email:
            return email
    except Exception as e:
        print(f"❌ Error generating email for {name} @ {domain}: {e}")

    return None

import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from email_validator import validate_email, EmailNotValidError
import os

def send_multiple_emails_same_person(email_list,first_name,job_url, pdf_path, sender_email, sender_name, app_password):
    for email in email_list:
        send_email(email,first_name,job_url, pdf_path, sender_email, sender_name, app_password)

def send_email(to_email,first_name, job_url, pdf_path, sender_email, sender_name, app_password):
    # Validate recipient email
    try:
        validate_email(to_email)
    except EmailNotValidError as e:
        print(f"❌ Invalid email: {to_email} - {e}")
        return False
    subject = "Excited about the opportunity at your company"
    if job_url!="":
        body = f"""
    Hi {first_name.capitalize()},

    I came across an opening in your company,({job_url}) and I believe my background in data science and machine learning is a strong fit.

    I've attached a tailored resume — I’d love to contribute to your team. Let me know if there's a good time to connect.

    Best,
    {sender_name}
            """
    else:
        body = f"""
    Hi {first_name.capitalize()},

    I came across an opening in your company, and I believe my background in data science and machine learning is a strong fit.

    I've attached a tailored resume — I’d love to contribute to your team. Let me know if there's a good time to connect.

    Best,
    {sender_name}
            """


    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr((sender_name, sender_email))
    msg['To'] = to_email
    msg.set_content(body)

    # Attach PDF
    try:
        with open(pdf_path, 'rb') as f:
            resume_data = f.read()
        msg.add_attachment(resume_data, maintype='application', subtype='pdf', filename=os.path.basename(pdf_path))
    except Exception as e:
        print(f"❌ Failed to attach resume: {e}")
        return False

    # Send
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print(f"✅ Sent email to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

import csv
import os

LOG_FILE = "contact_log.csv"

def log_contact(email, job_id):
    """
    Log that an email was sent for a given job ID.
    Creates log file if it doesn't exist.
    """
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["email", "job_id"])

    with open(LOG_FILE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([email, job_id])

def has_already_contacted(email, job_id):
    """
    Returns True if the email-job_id pair has already been logged.
    """
    if not os.path.exists(LOG_FILE):
        return False

    with open(LOG_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"] == email and row["job_id"] == job_id:
                return True
    return False