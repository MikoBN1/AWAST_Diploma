"""
Thin Flask wrapper around XSStrike CLI.
Receives scan requests via HTTP, runs XSStrike, and returns results as JSON.
"""

import json
import subprocess
import sys
import uuid
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

_tasks: dict = {}
_lock = threading.Lock()

XSSTRIKE_PATH = "/app/xsstrike/xsstrike.py"


def _run_xsstrike(task_id: str, target_url: str, cookies: str | None, headers: dict | None):
    """Run XSStrike in a background thread and store results."""
    cmd = [
        sys.executable, XSSTRIKE_PATH,
        "-u", target_url,
        "--json",
        "--skip",
    ]

    if cookies:
        cmd.extend(["--cookie", cookies])

    if headers:
        for key, value in headers.items():
            cmd.extend(["--headers", f"{key}: {value}"])

    with _lock:
        _tasks[task_id]["status"] = "running"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd="/app/xsstrike",
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        vulnerabilities = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                vulnerabilities.append(json.loads(line))
            except json.JSONDecodeError:
                vulnerabilities.append({"raw": line})

        with _lock:
            _tasks[task_id].update({
                "status": "completed",
                "vulnerabilities": vulnerabilities,
                "stderr": stderr,
                "return_code": result.returncode,
            })

    except subprocess.TimeoutExpired:
        with _lock:
            _tasks[task_id].update({
                "status": "error",
                "error": "Scan timed out after 600s",
            })
    except Exception as e:
        with _lock:
            _tasks[task_id].update({
                "status": "error",
                "error": str(e),
            })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "tool": "xsstrike"})


@app.route("/scan", methods=["POST"])
def start_scan():
    data = request.get_json(force=True)
    target_url = data.get("url")
    if not target_url:
        return jsonify({"error": "url is required"}), 400

    cookies = data.get("cookies")
    headers = data.get("headers")

    task_id = str(uuid.uuid4())
    with _lock:
        _tasks[task_id] = {"status": "queued", "url": target_url}

    thread = threading.Thread(
        target=_run_xsstrike,
        args=(task_id, target_url, cookies, headers),
        daemon=True,
    )
    thread.start()

    return jsonify({"task_id": task_id}), 202


@app.route("/scan/<task_id>", methods=["GET"])
def get_scan_status(task_id: str):
    with _lock:
        task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
