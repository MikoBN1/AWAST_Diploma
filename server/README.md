# AWAST Diploma Server

**Automated Web App Security Testing (AWAST)** is a comprehensive backend system designed to automate security vulnerability detection and exploitation verification. It integrates **OWASP ZAP** for scanning and utilizes **Large Language Models (LLMs)** to generate and verify exploit payloads, providing a robust solution for securing web applications.

## 🚀 Features

*   **🛡️ Automated Scanning**: Full integration with OWASP ZAP to perform Spidering and Active Attacks.
*   **🤖 AI-Powered Exploitation**: Uses LLMs (via `LLMService`) to generate context-aware payloads for verified vulnerabilities.
*   **🕵️ Attack Verification**: Automated `ExploiterService` that uses `Playwright` to test generated payloads against the target, confirming real-world risk.
*   **🔌 Plugin System**: Modular architecture supporting specific vulnerability checks:
    *   Cross-Site Scripting (XSS)
    *   SQL Injection (SQLi)
    *   Server-Side Request Forgery (SSRF)
    *   Insecure Direct Object References (IDOR)
*   **📑 Automated Reporting**: Generates detailed PDF reports of scan results and confirmed vulnerabilities.
*   **👤 User Management**: Built-in authentication and user management system.

## 🛠️ Tech Stack

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Database**: SQLAlchemy (Async)
*   **Scanner Engine**: [OWASP ZAP](https://www.zaproxy.org/) (Dockerized)
*   **Browser Automation**: Playwright
*   **Deployment**: Docker & Docker Compose

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

*   **Docker** and **Docker Compose**
*   **Python 3.10+** (if running locally without Docker)

## ⚡ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository_url>
cd server
```

### 2. Configure Environment

Create a `.env` file in the root directory. You can use the provided `.env.example` as a template (if available) or configure the following keys:

```ini
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./session.db # Or your DB connection string

# ZAP Configuration
ZAP_API_KEY=changeme
ZAP_API_URL=http://zap:8080 # Use 'http://localhost:8080' if running locally outside Docker

# LLM Configuration (for AI Exploitation)
OPENAI_API_KEY=your_api_key_here # Or other LLM provider keys
```

### 3. Run with Docker (Recommended)

Start the entire stack (FastAPI server + ZAP) using Docker Compose:

```bash
docker-compose up -d --build
```

The server will be available at `http://localhost:8000` (or the port defined in your configuration).
OWASP ZAP will be running on port `8080`.

### 4. Run Locally (Development)

If you prefer to run the FastAPI server locally while keeping ZAP in Docker:

1.  **Start ZAP**:
    ```bash
    docker-compose up -d zap
    ```
    *Ensure `ZAP_API_URL` in `.env` is set to `http://localhost:8080`.*

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## 📖 API Documentation

Once the server is running, you can access the interactive Swagger UI to explore and test the endpoints:

*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

*   **`POST /zap/spider`**: Start a ZAP Spider scan on a target.
*   **`POST /zap/scan`**: Start an Active Scan (Attack) on a target.
*   **`POST /exploiter/run`**: specific vulnerability verification using AI payloads.
*   **`POST /report/new`**: Generate a PDF report for a completed scan.
*   **`GET /api/users/me`**: Get current user information.

## 📂 Project Structure

```
server/
├── app/
│   ├── core/           # Core configurations (Database, Security)
│   ├── models/         # Database models (User, Scan, Vulnerability)
│   ├── schemas/        # Pydantic schemas for Request/Response validation
│   ├── services/       # Business logic (LLM, Exploiter, Report, Database)
│   ├── controllers/    # API Route handlers
│   ├── plugins/        # Vulnerability-specific detection logic
│   └── main.py         # Application entry point
├── zap/                # ZAP configuration and volume data
├── docker-compose.yml  # Docker orchestration
├── Dockerfile          # Server Dockerfile
└── requirements.txt    # Python dependencies
```
