
# AI Job Email Assistant 🤖✉️

A smart assistant that analyzes job postings and your resume (PDF), checks for match criteria (education, experience, skills), and generates a personalized email if you qualify.

---

## 💡 Features

- ✅ **Job Description Scraping**
- 📄 **Resume Parsing (via LlamaParse)**
- 🎓 **Education Requirement Check**
- ⏳ **Experience Matching**
- 🧠 **Skill Set Matching (10% minimum required)**
- 📬 **Personalized Email Generation**
- 🎨 **Modern GUI with color-coded feedback**
- 🚫 **Blocks email generation if requirements not met**

---

## 📁 File Structure

```
AI-Job-Email-Assistant/
│
├── main.py              # Main application logic
├── .env                 # Stores sensitive API keys
├── README.md            # This file
├── requirements.txt     # Python dependencies
├── CONTRIBUTING.md      # Contribution guidelines
├── LICENSE              # MIT License
└── sample-resume.pdf    # Sample PDF resume (optional)
```

---

## 🧰 Requirements

Make sure you have the following installed:

### Python 3.8+
- [Download Python](https://www.python.org/downloads/)

### Required Packages:
Install via pip:
```bash
pip install langchain_groq langchain_community llama-parse chromadb sentence-transformers python-dotenv beautifulsoup4 lxml tk
```

> Note: `tk` comes pre-installed on Windows/macOS but may need manual installation on Linux:
```bash
sudo apt-get install python3-tk
```

---

## 🔐 Setup API Keys

Create a `.env` file in the root folder and add your API keys:

```env
GROQ_API_KEY=your-groq-api-key-here
LLAMA_CLOUD_API_KEY=your-llama-cloud-api-key-here
```

> 🔒 Never commit or share this file!

---

## 🚀 How to Run

1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/AI-Job-Email-Assistant.git
   cd AI-Job-Email-Assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file with your API keys

4. Run the app:
   ```bash
   python main.py
   ```

5. In the GUI:
   - Paste a job portal URL
   - Upload your resume (PDF)
   - Click "Generate Email"

---

## 🧪 Example Use Case

- Paste:  
  `https://jobs.bdjobs.com/jobdetails.asp?id=1374713&fcatId=8&ln=1`

- Upload:  
  Your CV as `Resume Sample.pdf`

- Result:  
  If your education, experience, and skill set meet the job requirements, it will generate a professional email.

---

## 📦 Optional: Build an Executable (.exe)

You can convert this into a standalone desktop app using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

This will create a `dist/main.exe` file that runs without needing Python installed.

---

## 🤝 Contributing

Contributions are welcome! Please read our [contributing guide](CONTRIBUTING.md) before submitting pull requests.

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE) — see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Known Limitations

- Requires internet connection (uses cloud APIs)
- Some job portals block scraping
- Llama Cloud has rate limits for free accounts

---

## 📬 Contact

If you have any questions, feel free to reach out at:

📧 your.email@example.com  
🔗 [GitHub Profile](https://github.com/yourusername)

---

🚀 Thank you for using the AI Job Email Assistant!
```

---

### 📌 Bonus Files You Should Also Add

#### 1. `requirements.txt`
```txt
langchain_groq
langchain_community
llama-parse
chromadb
sentence-transformers
python-dotenv
beautifulsoup4
lxml
tk
```

#### 2. `CONTRIBUTING.md`
```md
# Contributing

Thank you for considering contributing to AI Job Email Assistant!

Please follow these guidelines:
- Fork the repository
- Create a new branch (`git checkout -b feature/new-feature`)
- Commit changes (`git commit -m 'Add new feature'`)
- Push to the branch (`git push origin feature/new-feature`)
- Open a Pull Request
```

#### 3. `LICENSE` (MIT License)
```txt
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ✅ Done!
