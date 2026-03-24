"""
Intentionally vulnerable multi-site test victim for scanners.
Focuses on XSS and SQLi with lightweight pages and crawler-friendly links/forms.
"""
import os
import sqlite3
from flask import Flask, request, redirect

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "victim.db")
GUESTBOOK = []


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT, amount INTEGER)"
    )
    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM orders")
    cur.executemany(
        "INSERT INTO users (id, username, password, role) VALUES (?, ?, ?, ?)",
        [
            (1, "admin", "admin123", "admin"),
            (2, "alice", "alice123", "user"),
            (3, "bob", "bob123", "user"),
        ],
    )
    cur.executemany(
        "INSERT INTO products (id, name, category, price) VALUES (?, ?, ?, ?)",
        [
            (1, "Keyboard", "electronics", 50),
            (2, "Mouse", "electronics", 35),
            (3, "Mug", "home", 12),
            (4, "Notebook", "office", 7),
        ],
    )
    cur.executemany(
        "INSERT INTO orders (id, user_id, item, amount) VALUES (?, ?, ?, ?)",
        [
            (1, 1, "Keyboard", 50),
            (2, 2, "Notebook", 7),
            (3, 3, "Mug", 12),
        ],
    )
    conn.commit()
    conn.close()


def layout(title: str, body: str) -> str:
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h1>{title}</h1>
<p><a href="/">Home</a></p>
{body}
</body>
</html>"""


def run_query_unsafe(sql: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = []
    err = ""
    try:
        cur.execute(sql)
        rows = cur.fetchall()
    except Exception as ex:
        err = str(ex)
    conn.close()
    return rows, err


@app.get("/")
def index():
    links = [
        ("/mini1/search", "Mini1 - Reflected XSS search"),
        ("/mini2/profile", "Mini2 - Reflected XSS profile"),
        ("/mini3/guestbook", "Mini3 - Stored XSS guestbook"),
        ("/mini4/dom", "Mini4 - DOM XSS hash sink"),
        ("/mini5/login", "Mini5 - SQLi login"),
        ("/mini6/products", "Mini6 - SQLi products"),
        ("/mini7/order", "Mini7 - SQLi order lookup"),
        ("/mini8/post", "Mini8 - XSS + SQLi post view"),
        ("/mini9/echo", "Mini9 - Reflected XSS echo"),
        ("/mini10/api/user", "Mini10 - SQLi API"),
        ("/mini11/welcome", "Mini11 - JS context XSS"),
        ("/mini12/feedback", "Mini12 - Stored + reflected XSS"),
        ("/health", "Health"),
        ("/xss_r", "Legacy reflected XSS endpoint"),
    ]
    items = "".join([f'<li><a href="{u}">{t}</a></li>' for u, t in links])
    return layout("AWAST Test Victim Collection", f"<ul>{items}</ul>")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/xss_r")
def legacy_xss():
    name = request.args.get("name", "")
    body = f"""
<form method="get">
  <input name="name" placeholder="name">
  <button type="submit">Submit</button>
</form>
<div>Hello {name}</div>
"""
    return layout("Legacy Reflected XSS", body)


@app.get("/mini1/search")
def mini1_search():
    q = request.args.get("q", "")
    body = f"""
<form method="get">
  <input name="q" placeholder="search term">
  <button type="submit">Search</button>
</form>
<p>Results for: {q}</p>
<a href="/mini2/profile?name=test">next</a>
"""
    return layout("Mini1 Search", body)


@app.get("/mini2/profile")
def mini2_profile():
    name = request.args.get("name", "guest")
    body = f"""
<form method="get">
  <input name="name" value="{name}">
  <button type="submit">View</button>
</form>
<img src="/static/avatar.png" alt="{name}">
<a href="/mini3/guestbook">next</a>
"""
    return layout("Mini2 Profile", body)


@app.route("/mini3/guestbook", methods=["GET", "POST"])
def mini3_guestbook():
    if request.method == "POST":
        GUESTBOOK.append(request.form.get("message", ""))
        return redirect("/mini3/guestbook")
    posts = "".join([f"<li>{m}</li>" for m in GUESTBOOK[-20:]])
    body = f"""
<form method="post">
  <input name="message" placeholder="leave message">
  <button type="submit">Post</button>
</form>
<ul>{posts}</ul>
<a href="/mini4/dom#hello">next</a>
"""
    return layout("Mini3 Guestbook", body)


@app.get("/mini4/dom")
def mini4_dom():
    body = """
<p>DOM sink uses location.hash below.</p>
<div id="out"></div>
<script>
  var hash = window.location.hash.substring(1);
  if (hash) { document.getElementById("out").innerHTML = hash; }
</script>
<a href="/mini5/login">next</a>
"""
    return layout("Mini4 DOM Page", body)


@app.route("/mini5/login", methods=["GET", "POST"])
def mini5_login():
    result = ""
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        sql = f"SELECT id, username, role FROM users WHERE username = '{u}' AND password = '{p}'"
        rows, err = run_query_unsafe(sql)
        result = f"<pre>{rows or err or 'No rows'}</pre><p>Query: {sql}</p>"
    body = f"""
<form method="post">
  <input name="username" placeholder="username">
  <input name="password" placeholder="password">
  <button type="submit">Login</button>
</form>
{result}
<a href="/mini6/products?category=electronics">next</a>
"""
    return layout("Mini5 Login", body)


@app.get("/mini6/products")
def mini6_products():
    category = request.args.get("category", "electronics")
    sql = f"SELECT id, name, price FROM products WHERE category = '{category}'"
    rows, err = run_query_unsafe(sql)
    rows_html = "".join([f"<li>{r}</li>" for r in rows])
    body = f"""
<form method="get">
  <input name="category" value="{category}">
  <button type="submit">Filter</button>
</form>
<ul>{rows_html}</ul>
<p>Error: {err}</p>
<p>Query: {sql}</p>
<a href="/mini7/order?id=1">next</a>
"""
    return layout("Mini6 Products", body)


@app.get("/mini7/order")
def mini7_order():
    oid = request.args.get("id", "1")
    sql = f"SELECT id, user_id, item, amount FROM orders WHERE id = {oid}"
    rows, err = run_query_unsafe(sql)
    body = f"""
<form method="get">
  <input name="id" value="{oid}">
  <button type="submit">Lookup</button>
</form>
<pre>{rows}</pre>
<p>Error: {err}</p>
<p>Query: {sql}</p>
<a href="/mini8/post?id=1&comment=hello">next</a>
"""
    return layout("Mini7 Order Lookup", body)


@app.get("/mini8/post")
def mini8_post():
    post_id = request.args.get("id", "1")
    comment = request.args.get("comment", "")
    sql = f"SELECT id, username, role FROM users WHERE id = {post_id}"
    rows, err = run_query_unsafe(sql)
    body = f"""
<form method="get">
  <input name="id" value="{post_id}">
  <input name="comment" value="{comment}">
  <button type="submit">View</button>
</form>
<p>User row: {rows}</p>
<p>Comment preview: {comment}</p>
<p>Error: {err}</p>
<a href="/mini9/echo?msg=test">next</a>
"""
    return layout("Mini8 Post Viewer", body)


@app.get("/mini9/echo")
def mini9_echo():
    msg = request.args.get("msg", "")
    body = f"""
<form method="get">
  <input name="msg" value="{msg}">
  <button type="submit">Echo</button>
</form>
<div class="notice">Debug: {msg}</div>
<a href="/mini10/api/user?id=1">next</a>
"""
    return layout("Mini9 Echo", body)


@app.get("/mini10/api/user")
def mini10_api_user():
    uid = request.args.get("id", "1")
    sql = f"SELECT id, username, role FROM users WHERE id = {uid}"
    rows, err = run_query_unsafe(sql)
    body = f"""
<p>Unsafe SQL API style endpoint.</p>
<form method="get">
  <input name="id" value="{uid}">
  <button type="submit">Fetch</button>
</form>
<pre>{rows}</pre>
<p>Error: {err}</p>
<p>Query: {sql}</p>
<a href="/mini11/welcome?user=guest">next</a>
"""
    return layout("Mini10 API User", body)


@app.get("/mini11/welcome")
def mini11_welcome():
    user = request.args.get("user", "guest")
    body = f"""
<form method="get">
  <input name="user" value="{user}">
  <button type="submit">Render</button>
</form>
<script>
  var userName = "{user}";
  document.write("<p>Welcome " + userName + "</p>");
</script>
<a href="/mini12/feedback">next</a>
"""
    return layout("Mini11 Welcome", body)


@app.route("/mini12/feedback", methods=["GET", "POST"])
def mini12_feedback():
    if request.method == "POST":
        GUESTBOOK.append(request.form.get("fb", ""))
        return redirect("/mini12/feedback")
    preview = request.args.get("preview", "")
    items = "".join([f"<li>{m}</li>" for m in GUESTBOOK[-10:]])
    body = f"""
<form method="post">
  <input name="fb" placeholder="feedback">
  <button type="submit">Save</button>
</form>
<form method="get">
  <input name="preview" value="{preview}" placeholder="preview text">
  <button type="submit">Preview</button>
</form>
<p>Preview: {preview}</p>
<ul>{items}</ul>
<a href="/">back to home</a>
"""
    return layout("Mini12 Feedback", body)


@app.errorhandler(Exception)
def fallback_error(_):
    # Keep scanner/spider stable and avoid hard failures.
    return layout("Victim Error Handler", "<p>An internal error occurred.</p><a href='/'>home</a>"), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=9999, debug=False)
