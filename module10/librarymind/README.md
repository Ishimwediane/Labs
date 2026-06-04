# LibraryMind - AI-Powered Library Backend

## Project Overview
LibraryMind is an AI-powered backend service designed for modern public libraries. It integrates multiple AI providers, vector databases for semantic search, and robust caching mechanisms to provide an intelligent assistant experience.

## Part 0: Foundation and Environment Setup
This initial phase (Part 0) focuses on establishing a clean project structure, dependency management, and a robust configuration system.

### Purpose of Part 0
- Set up the project scaffold and directory structure.
- Define necessary dependencies for the full project lifecycle.
- Implement typed configuration using Pydantic Settings with validation.
- Create a minimal FastAPI entry point.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher.

### 2. Create and Activate Virtual Environment
Navigate to the `librarymind` directory and run:

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements
With the virtual environment activated, run:
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the template environment file to a local `.env` file:
```bash
cp .env.example .env
```

**IMPORTANT:** You must edit the `.env` file and provide at least one AI provider API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY`). The application will fail to start if no provider key is set.

### 5. Running the Application
Start the FastAPI development server using Uvicorn:
```bash
uvicorn app.main:app --reload
```
The application will be available at `http://127.0.0.1:8000`.

---

## Project Structure
```text
librarymind/
├── app/
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```
