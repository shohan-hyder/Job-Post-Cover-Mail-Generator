import os
import uuid
import re
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from llama_parse import LlamaParse
from sentence_transformers import SentenceTransformer
import chromadb
import threading


# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatGroq(
    temperature=0.5,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="deepseek-r1-distill-llama-70b"
)

# Global variables
cv_path = None
cancel_flag = False

# Load embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Modern Colors
BG_COLOR = "#ffffff"
FG_COLOR = "#2d2d2d"
ACCENT_COLOR = "#6c63ff"
WARNING_COLOR = "#f7a440"
ERROR_COLOR = "#e74c3c"
BTN_COLOR = "#2ecc71"
BTN_HOVER = "#28b463"


# --- Helper Functions ---

def log(msg, tag="normal"):
    output_text.config(state=tk.NORMAL)
    output_text.insert(tk.END, msg + "\n", tag)
    output_text.config(state=tk.DISABLED)
    output_text.see(tk.END)


def is_valid_cv(pdf_path):
    if not pdf_path or not os.path.exists(pdf_path):
        return False, "Invalid file path."
    try:
        document = LlamaParse(result_type="markdown").load_data(pdf_path)
        if not document:
            return False, "Failed to parse the PDF."
        text = document[0].text
        if len(text.strip()) < 100:
            return False, "PDF appears to be empty or unreadable."
        return True, text
    except Exception as e:
        return False, f"Error parsing PDF: {e}"


def extract_keywords(job_data):
    keywords = set()
    for key in ['required skills', 'responsibilities', 'qualifications']:
        values = job_data.get(key, [])
        if isinstance(values, str):
            keywords.update(word.lower() for word in values.split() if len(word) > 3)
        elif isinstance(values, list):
            for v in values:
                if isinstance(v, str):
                    keywords.update(word.lower() for word in v.split() if len(word) > 3)
    return list(keywords)


def get_embeddings(text_list):
    return embedding_model.encode(text_list, convert_to_numpy=True)


def semantic_match_score(job_skills, cv_skills):
    if not job_skills or not cv_skills:
        return 0

    job_embeddings = get_embeddings(job_skills)
    cv_embeddings = get_embeddings(cv_skills)

    matched = 0
    for j_emb in job_embeddings:
        similarities = np.dot(cv_embeddings, j_emb) / (
                np.linalg.norm(cv_embeddings, axis=1) * np.linalg.norm(j_emb))
        if np.any(similarities >= 0.6):
            matched += 1

    return (matched / len(job_skills)) * 100


# --- Education & Experience Helpers ---

def extract_education_requirement(job_data):
    education_keywords = {
        "phd": ["phd", "doctorate"],
        "master": ["master", "msc", "m.s.", "m.tech"],
        "bachelor": ["bachelor", "bsc", "b.s.", "b.tech", "b.com", "b.a."],
        "diploma": ["diploma", "certificate"]
    }

    text = ""
    for key in ['qualifications', 'job description']:
        val = job_data.get(key, "")
        if isinstance(val, list):
            text += " ".join(val).lower()
        else:
            text += str(val).lower()

    for level, keywords in education_keywords.items():
        for word in keywords:
            if word in text:
                return level
    return None


def extract_candidate_education(cv_text):
    cv_lower = cv_text.lower()
    if any(word in cv_lower for word in ["phd", "doctorate"]):
        return "phd"
    elif any(word in cv_lower for word in ["master", "msc", "m.s.", "m.tech"]):
        return "master"
    elif any(word in cv_lower for word in ["bachelor", "bsc", "b.s.", "b.tech", "b.com", "b.a."]):
        return "bachelor"
    elif any(word in cv_lower for word in ["diploma", "certificate"]):
        return "diploma"
    return None


def meets_education_requirement(job_edu, cv_edu):
    edu_hierarchy = {
        "phd": 4,
        "master": 3,
        "bachelor": 2,
        "diploma": 1,
        None: 0
    }
    return edu_hierarchy.get(cv_edu, 0) >= edu_hierarchy.get(job_edu, 0)


def extract_required_experience(job_data):
    text = ""
    for key in ['experience', 'responsibilities', 'qualifications']:
        val = job_data.get(key, "")
        if isinstance(val, list):
            text += " ".join(val).lower()
        else:
            text += str(val).lower()

    match = re.search(r'(\d+)\s*(?:\+|plus)?\s*years?\s*of\s*experience', text)
    if match:
        return int(match.group(1))
    return 0


def extract_candidate_experience(cv_text):
    exp_years = []
    matches = re.findall(r'\b\d{1,2}\s*(?:\+|plus)?\s*years?\s*(?:of|in)\s*\w+', cv_text.lower())
    for m in matches:
        num_match = re.search(r'\d+', m)
        if num_match:
            exp_years.append(int(num_match.group()))
    return max(exp_years) if exp_years else 0


# --- Main Processing Function ---

def process_and_generate(job_url):
    try:
        log("🔍 Scraping job description...", "info")
        loader = WebBaseLoader(job_url)
        page_data = loader.load().pop().page_content

        if cancel_flag:
            return

        log("\n📑 Extracting job details...", "info")
        prompt_extract = PromptTemplate.from_template("""
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career page of a website.
            Your job is to extract the job postings and return them in JSON format containing the
            following keys: `job title`,`company name`,`location`,`required skills`,`responsibilities`,`qualifications` & `job description`.
            Only return valid JSON.
            ### VALID JSON (NO PREAMBLE):
        """)
        chain_extract = prompt_extract | llm
        res = chain_extract.invoke(input={'page_data': page_data})

        json_parser = JsonOutputParser()
        json_match = re.search(r'{.*}', res.content, re.DOTALL)
        if json_match:
            job_data = json_parser.parse(json_match.group(0))
        else:
            raise ValueError("Could not find JSON in LLM output")

        log("\n💼 Job Details Extracted:")
        for key, value in job_data.items():
            log(f"{key}: {value}")

        log("\n📄 Validating CV...", "info")
        is_valid, cv_result = is_valid_cv(cv_path)
        if not is_valid:
            log(f"\n❌ Invalid CV: {cv_result}", "error")
            return
        cv_text = cv_result

        # Education check
        job_edu = extract_education_requirement(job_data)
        cv_edu = extract_candidate_education(cv_text)

        if job_edu:
            log(f"\n🎓 Job requires: {job_edu.capitalize()} degree")
            log(f"✅ You have: {cv_edu.capitalize() if cv_edu else 'Not found'}")
            if not meets_education_requirement(job_edu, cv_edu):
                log(f"\n🛑 Your education ({cv_edu}) does not meet job requirement ({job_edu}).", "error")
                log("\n🚫 Cannot generate email: Education mismatch.", "error")
                log("Thanks for using this assistant!", "success")
                return

        # Experience check
        req_exp = extract_required_experience(job_data)
        cv_exp = extract_candidate_experience(cv_text)

        if req_exp > 0:
            log(f"\n📅 Job requires: {req_exp}+ years of experience")
            log(f"✅ You have: {cv_exp} years of experience")
            if cv_exp < req_exp:
                log(f"\n🛑 Required experience: {req_exp}+ years. You have: {cv_exp} years.", "error")
                log("\n🚫 Cannot generate email: Not enough experience.", "error")
                log("Thanks for using this assistant!", "success")
                return

        # Skill Match Analysis
        log("\n🧮 Analyzing CV-job match...")

        job_skills = extract_keywords(job_data)
        if not job_skills:
            log("\nℹ️ No clear skills found in job data.", "warning")
            match_percentage = 0
        else:
            cv_skill_sections = re.split(r'\n\s*\n', cv_text.lower())
            cv_skills = [s for s in cv_skill_sections if any(k in s for k in ['skill', 'experience', 'project'])]
            cv_skills_str = ' '.join(cv_skills)
            cv_skills_words = cv_skills_str.split()

            job_skills_set = set(s.lower() for s in job_skills)
            matched_skills = [s for s in job_skills_set if s in cv_skills_str]

            match_percentage = (len(matched_skills) / len(job_skills_set)) * 100 if job_skills_set else 0

            semantic_score = semantic_match_score(job_skills, cv_skills_words)
            final_score = (match_percentage + semantic_score) / 2

            log(f"Keyword Match: {len(matched_skills)} out of {len(job_skills_set)} required skills.")
            log(f"Semantic Match Score: {semantic_score:.1f}%")
            log(f"Final Match Score: {final_score:.1f}%")

        if final_score < 10:
            log("\n⚠️ CV does not meet at least 10% of the job requirements.", "warning")
            log("\n🚫 Cannot generate email: Low skill match.", "error")
            log("Thanks for using this assistant!", "success")
            return

        log("\n✅ CV matches job requirements.", "success")
        log("\n📧 Generating personalized email...", "info")

        # Step: Create Vector Store
        log("\n📚 Creating vector store...", "info")
        client = chromadb.PersistentClient('vectorstore_temp')
        try:
            client.delete_collection(name="portfolio")
        except:
            pass
        collection = client.get_or_create_collection(name="portfolio")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        chunks = [chunk.strip() for chunk in cv_text.split("\n\n") if len(chunk.strip()) > 40]
        log(f"Added {len(chunks)} text chunks to the vector store.")

        for chunk in chunks:
            embedding = model.encode(chunk).tolist()
            collection.add(
                ids=[str(uuid.uuid4())],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": "cv", "length": len(chunk)}]
            )

        # Step: Retrieve Relevant CV Parts
        log("\n🔍 Retrieving relevant CV parts...")
        relevant_parts = []
        unique_texts = set()

        for value in job_data.values():
            if isinstance(value, str) and value.strip():
                queries = [value.strip()]
            elif isinstance(value, list):
                queries = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            else:
                queries = []

            for query_text in queries:
                if len(query_text) > 10:
                    result = collection.query(query_texts=[query_text], n_results=2)
                    retrieved_docs = result.get('documents')
                    if retrieved_docs and retrieved_docs[0]:
                        for doc in retrieved_docs[0]:
                            if doc not in unique_texts:
                                relevant_parts.append(doc)
                                unique_texts.add(doc)

        if not relevant_parts:
            log("\n⚠️ No relevant CV parts found.", "warning")
            return

        cv_context = "\n".join(relevant_parts)

        # Step: Generate Email
        log("\n✉️ Generating personalized email...", "info")
        prompt_email = PromptTemplate.from_template("""
            ### JOB DESCRIPTION SUMMARY:
            Job Title: {job_title}
            Company: {company_name}
            Location: {location}
            Skills: {required_skills}
            Responsibilities: {responsibilities}
            Qualifications: {qualifications}

            ### RELEVANT CONTEXT (from my CV):
            {cv_context}

            ### INSTRUCTION:
            Write a concise, professional cover email for the HR person who posted the job above.
            Address it to "Hiring Manager".
            The subject line should be "Application for [Job Title]".
            In the body, reference the role you are applying for.
            Use the relevant CV context to subtly highlight your fit for this role based on the listed skills, responsibilities, and qualifications.
            Avoid direct quotes from your CV.
            The goal is to briefly connect your background to the job requirements and express enthusiasm.
            Maintain a confident and professional tone.
            Sign off with "Sincerely," followed by "Your Name".
            The output should be only the email content (Subject and Body), formatted as a standard email.

            ### EMAIL:
        """)

        chain_email = prompt_email | llm
        email_res = chain_email.invoke({
            "job_title": job_data.get('job title', 'the position'),
            "company_name": job_data.get('company name', 'the company'),
            "location": job_data.get('location', ''),
            "required_skills": ', '.join(job_data.get('required skills', [])),
            "responsibilities": ', '.join(job_data.get('responsibilities', [])),
            "qualifications": ', '.join(job_data.get('qualifications', [])),
            "cv_context": cv_context
        })

        log("\n" + "=" * 30)
        log("📬 Generated Email:", "success")
        log("=" * 30)
        log(email_res.content)
        log("=" * 30)
        log("✅ Successfully generated email based on your resume.", "success")
        log("Thanks for using this assistant!", "success")

    except Exception as e:
        if not cancel_flag:
            log(f"\n❌ An error occurred: {e}", "error")


# --- GUI Functions ---

def upload_cv():
    global cv_path
    cv_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if cv_path:
        cv_label.config(text=f"📄 CV uploaded: {os.path.basename(cv_path)}")
    else:
        cv_label.config(text="No CV uploaded")


def generate_email():
    job_url = url_entry.get()
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.config(state=tk.DISABLED)

    if not job_url:
        messagebox.showwarning("Input Error", "Please enter the job portal URL.")
        return
    if not cv_path:
        messagebox.showwarning("Input Error", "Please upload your CV first.")
        return

    global cancel_flag
    cancel_flag = False
    threading.Thread(target=process_and_generate, args=(job_url,)).start()


def cancel_operation():
    global cancel_flag
    cancel_flag = True
    log("\n⚠️ Operation canceled by user.", "warning")


def exit_app():
    if messagebox.askokcancel("Quit", "Do you really want to quit?"):
        root.destroy()


# --- GUI Setup ---
root = tk.Tk()
root.title("AI Job Email Assistant")
root.geometry("950x750")
root.configure(bg=BG_COLOR)
root.protocol("WM_DELETE_WINDOW", exit_app)

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6, relief="flat")
style.map("TButton",
          background=[('active', BTN_HOVER)],
          foreground=[('pressed', 'white'), ('active', 'white')])

# Header Frame
header_frame = tk.Frame(root, bg=BG_COLOR)
header_frame.pack(pady=15)

tk.Label(header_frame, text="🤖 AI Job Email Assistant", font=("Segoe UI", 20, "bold"), fg=FG_COLOR, bg=BG_COLOR).pack()

# Input Frame
input_frame = tk.Frame(root, bg=BG_COLOR)
input_frame.pack(pady=10)

tk.Label(input_frame, text="🔗 Enter Job Portal URL:", font=("Segoe UI", 12), fg=FG_COLOR, bg=BG_COLOR).grid(row=0, column=0, sticky='w')
url_entry = tk.Entry(input_frame, width=60, font=("Segoe UI", 11))
url_entry.grid(row=1, column=0, padx=10, pady=5)

upload_btn = tk.Button(input_frame, text="📁 Upload CV PDF", command=upload_cv, width=20, bg=BTN_COLOR, fg="white", bd=0, padx=10, pady=5)
upload_btn.grid(row=1, column=1, padx=10)
upload_btn.bind("<Enter>", lambda e: upload_btn.config(bg=BTN_HOVER))
upload_btn.bind("<Leave>", lambda e: upload_btn.config(bg=BTN_COLOR))

cv_label = tk.Label(root, text="No CV uploaded", fg=FG_COLOR, bg=BG_COLOR, font=("Segoe UI", 10))
cv_label.pack(pady=5)

# Button Frame
btn_frame = tk.Frame(root, bg=BG_COLOR)
btn_frame.pack(pady=10)

generate_btn = tk.Button(btn_frame, text="📧 Generate Email", command=generate_email, width=20, bg=ACCENT_COLOR, fg="white", bd=0, padx=10, pady=5)
generate_btn.grid(row=0, column=0, padx=5)
generate_btn.bind("<Enter>", lambda e: generate_btn.config(bg="#5a51dd"))
generate_btn.bind("<Leave>", lambda e: generate_btn.config(bg=ACCENT_COLOR))

cancel_btn = tk.Button(btn_frame, text="🛑 Cancel", command=cancel_operation, width=20, bg=WARNING_COLOR, fg="white", bd=0, padx=10, pady=5)
cancel_btn.grid(row=0, column=1, padx=5)
cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg="#df8f2d"))
cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg=WARNING_COLOR))

exit_btn = tk.Button(btn_frame, text="🚪 Exit", command=exit_app, width=20, bg=ERROR_COLOR, fg="white", bd=0, padx=10, pady=5)
exit_btn.grid(row=0, column=2, padx=5)
exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg="#c0392b"))
exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg=ERROR_COLOR))

# Output Frame
output_frame = tk.Frame(root)
output_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

output_text = tk.Text(output_frame, wrap=tk.WORD, height=22, width=100, state=tk.DISABLED, bg="#f9f9f9", fg=FG_COLOR, font=("Segoe UI", 11), bd=1, relief="sunken")
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(output_frame, command=output_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
output_text.config(yscrollcommand=scrollbar.set)

# Tag styles
output_text.tag_config("info", foreground=FG_COLOR)
output_text.tag_config("success", foreground=ACCENT_COLOR)
output_text.tag_config("warning", foreground=WARNING_COLOR)
output_text.tag_config("error", foreground=ERROR_COLOR)

root.mainloop()