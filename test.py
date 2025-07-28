from smart_resume_bot.tools import tailor_resume,compile_pdf
from get_jd import get_job_description
import PyPDF2

job_url="https://click.appcast.io/t/ki_-iXGDzbJAQoK0USHy9UQvD8P9t4utLsQgbPIFoCHpxHcKeFUm0m8XVhQeVlkM?src=LinkedIn"

jd = get_job_description(job_url)
print("jd length",len(jd))


company="Shopify"
role="Machine Learning Engineer"
# 1. Get resume
  


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
        print(f"[Error] PDF rendering or validation failed. Falling back to base_resume.pdf. Error {e}")
        pdf_path = "resumes/base_resume.pdf"