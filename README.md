**📘 Automated Answer Sheet Evaluation System**

An AI-powered platform for evaluating student answer sheets automatically with NLP + ML + LLM support.

**🚀 Overview**

The Automated Answer Sheet Evaluation System is an AI-based solution that evaluates subjective and objective answers submitted by students.
It eliminates manual checking, improves accuracy, and provides instant feedback using NLP, Machine Learning, and LLM models.

This project supports:

Automated subjective answer scoring

Keyword matching & semantic similarity

LLM-based evaluation (optional)

Mis-spell correction

Detailed feedback generation

Marks calculation

Dashboard for students & teachers

**🎯 Key Features**

OCR Support – Extract answers from scanned sheets

Keyword-based Scoring

Semantic Similarity Scoring (Sentence Transformers)

LLM-based Evaluation (GPT/Llama/Gemma supported)

Automated Marks Calculation

Feedback Generator

Plagiarism Detection (Optional)

Web Interface (FastAPI / Streamlit)

Docker Support

MongoDB Logging

**🧱 Architecture**
Input Sheet → OCR → Text Extraction → Preprocessing → 
Model Evaluation (ML + LLM) → Scoring Engine → Feedback → Dashboard

🛠️ Tech Stack

Backend:

Python

FastAPI / Flask

Sentence Transformers

OpenAI / HuggingFace LLMs

NLTK / SpaCy

Frontend:

Streamlit / React (optional)

Database:

MongoDB (store answers, logs, scores)

Redis (cache model outputs)

Deployment:

Docker

Docker Compose

**📂 Project Structure**
project/
│── app.py                  # Main API
│── evaluator.py            # Scoring engine
│── llm_model.py            # LLM evaluation wrapper
│── ocr_module.py           # OCR processing
│── utils/                  # NLP utils
│── test_samples/           # Sample answer sheets
│── requirements.txt
│── Dockerfile
│── README.md

**🧪 How It Works**
1. Upload Answer Sheet

Accepts images (.jpg, .png) or PDFs

2. OCR Processing

Extracts text using Tesseract or EasyOCR

3. Preprocessing

Sentence cleaning

Stopword removal

Lemmatization

4. Evaluation Engine

Uses a mix of:

Method	Purpose
Keyword Matching	Basic scoring
Cosine Similarity	Semantic meaning match
LLM Evaluation	Open-ended subjective answer scoring
Rule-based checking	Must-include points
5. Score Calculation

Final score = weighted sum of all evaluation results.

6. Feedback Generation

LLM dynamically generates feedback for the student.

**🧰 Installation**
1️⃣ Clone the Repository
git clone https://github.com/your-username/answer-evaluation.git
cd answer-evaluation

2️⃣ Create Virtual Environment
python -m venv venv
.\venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Add LLM API Key

Create .env file:

OPENAI_API_KEY=your_key_here

🐳 Run with Docker
Build Image:
docker build -t answer-evaluator .

Run Container:
docker run -p 8000:8000 answer-evaluator

▶️ Run the Application (Without Docker)
uvicorn app:app --reload


Open in browser:

http://localhost:8000/docs

**🧪 API Endpoints**
Endpoint	Method	Description
/evaluate	POST	Upload answer sheet / text to evaluate
/feedback	GET	Get AI-generated feedback
/score	GET	Fetch score for student
/health	GET	Check API health
📊 Sample Response
{
  "question_id": "Q1",
  "score": 8.5,
  "max_score": 10,
  "similarity": 0.82,
  "keywords_matched": ["ecosystem", "interaction"],
  "feedback": "Good answer! You covered the key points but can include more examples."
}

🧩 Future Enhancements

Add multi-language support

Add handwriting recognition

Train custom evaluation model

Integrate with college ERP

Add grader dashboard

👨‍💻 Contributors

Your Name

Team Members
