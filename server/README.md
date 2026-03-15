# AWAST Diploma Server

**Automated Web App Security Testing (AWAST)** is a comprehensive backend system designed to automate security vulnerability detection and exploitation verification. It integrates **OWASP ZAP** for scanning and utilizes **Large Language Models (LLMs)** to generate and verify exploit payloads, providing a robust solution for securing web applications.

## 🚀 Features

*   **🛡️ Automated Scanning**: Full integration with OWASP ZAP to perform Spidering and Active Attacks.
*   **🤖 AI-Powered Exploitation Engine**: Uses LLMs (Ollama + external providers via `LLMService`) to generate context-aware payloads and parse complex server responses for zero-day-like exploitation. Includes 6 advanced techniques:
    *   **Context-Aware XSS**: Extracts reflection scopes from HTML and generates breakout payloads dynamically.
    *   **WAF Bypassing**: Analyzes HTTP `403/401` blocks and recursively mutates payloads using advanced encoding/obfuscation.
    *   **SSTI Engine Identification**: Reads HTML error stack traces to detect the template engine and craft an RCE payload.
    *   **API Parameter Guessing (IDOR/Mass Assignment)**: Deeply inspects JSON structures to hallucinate and inject hidden privilege parameters (e.g., `"role": "admin"`).
    *   **Prompt Injection / AI Jailbreak**: Red-teams underlying AI targets by generating adaptive jailbreak prompts.
    *   **Error-Based SQL Analysis**: Parses complex DBMS error messages directly to construct the exact SQL payload required.
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
*   **XSS Detection**: [XSStrike](https://github.com/s0md3v/XSStrike) (Dockerized, API on port 5000)
*   **SQL Injection**: [sqlmap](https://github.com/sqlmapproject/sqlmap) (Dockerized, API on port 8775)
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

# XSStrike (XSS scanner) – optional; used for XSS detection
XSSTRIKE_API_URL=http://localhost:5000 # Use 'http://xsstrike:5000' when all services run in Docker

# SQLMap (SQL injection) – optional; used for SQLi detection
SQLMAP_API_URL=http://localhost:8775 # Use 'http://sqlmap:8775' when all services run in Docker

# LLM Configuration (for AI Exploitation)
OPENAI_API_KEY=your_api_key_here # Or other LLM provider keys
```

### 3. Run with Docker (Recommended)

Start the entire stack (FastAPI server + ZAP + XSStrike + SQLMap) using Docker Compose:

```bash
docker-compose up -d --build
```

The server will be available at `http://localhost:8000` (or the port defined in your configuration).

| Service   | Port | Description                    |
|----------|------|--------------------------------|
| OWASP ZAP| 8080 | Web app scanner                |
| XSStrike | 5000 | XSS detection (wrapped API)    |
| SQLMap   | 8775 | SQL injection (sqlmapapi)      |

### 4. Run Locally (Development)

If you prefer to run the FastAPI server locally while keeping ZAP, XSStrike, and SQLMap in Docker:

1.  **Start ZAP** (required for spider/active scan):
    ```bash
    docker-compose up -d zap
    ```
    *Ensure `ZAP_API_URL` in `.env` is set to `http://localhost:8080`.*

2.  **Start XSStrike** (optional; for XSS detection in scans):
    ```bash
    docker-compose up -d xsstrike
    ```
    *Ensure `XSSTRIKE_API_URL` in `.env` is set to `http://localhost:5000`.*

3.  **Start SQLMap** (optional; for SQL injection detection in scans):
    ```bash
    docker-compose up -d sqlmap
    ```
    *Ensure `SQLMAP_API_URL` in `.env` is set to `http://localhost:8775`.*

4.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

5.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

6.  **Run the Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

### Starting XSStrike and SQLMap

*   **With full stack** (recommended): `docker-compose up -d --build` starts ZAP, XSStrike, and SQLMap together. Use `XSSTRIKE_API_URL=http://xsstrike:5000` and `SQLMAP_API_URL=http://sqlmap:8775` when the app runs inside the same Docker network.
*   **Individually** (e.g. for local dev): start only the tools you need:
    *   **XSStrike**: `docker-compose up -d xsstrike` → API at `http://localhost:5000`
    *   **SQLMap**: `docker-compose up -d sqlmap` → API at `http://localhost:8775`
    Set `XSSTRIKE_API_URL=http://localhost:5000` and `SQLMAP_API_URL=http://localhost:8775` in `.env` when the server runs on the host.

## 📖 API Documentation

Once the server is running, you can access the interactive Swagger UI to explore and test the endpoints:

*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

*   **`POST /zap/spider`**: Start a ZAP Spider scan on a target.
*   **`POST /zap/scan`**: Start an Active Scan (Attack) on a target.
*   **`POST /exploiter/run`**: specific vulnerability verification using AI payloads.
*   **`POST /report/new`**: Generate a PDF report for a completed scan.
*   **`POST /report/download`**: Download a generated report by `report_id`.
*   **`GET /api/users/me`**: Get current user information.

### Additional API docs

*   **Report API (create & download PDF):** [docs/REPORT.md](docs/REPORT.md)
*   **WebSocket (scan progress):** [docs/WEBSOCKET_API.md](docs/WEBSOCKET_API.md)

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
