"""
HTTP Honeypot Trap - Fake admin panel

A FastAPI sub-application that mimics a network management system login.
"""
import logging
import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse

from app.deception.event_logger import event_logger

logger = logging.getLogger(__name__)

# Create separate FastAPI app for the HTTP trap
http_trap_app = FastAPI(title="Network Management System", version="3.2.1")

# HTML template for the fake login page
LOGIN_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Management System v3.2.1</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: #0f0f23;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
            border: 1px solid #2d2d4e;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            color: #4a9eff;
            font-size: 24px;
            margin-bottom: 8px;
        }
        .logo p {
            color: #6b7280;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            color: #9ca3af;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            background: #1a1a2e;
            border: 1px solid #2d2d4e;
            border-radius: 6px;
            color: #e5e7eb;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #4a9eff;
        }
        .submit-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #4a9eff 0%, #2563eb 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .submit-btn:hover {
            opacity: 0.9;
        }
        .error-msg {
            background: #dc2626;
            color: white;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
            text-align: center;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
        }
        .footer .version {
            color: #4a9eff;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>⚡ NetManage Pro</h1>
            <p>Enterprise Network Management System</p>
        </div>
        
        {error_message}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" placeholder="admin" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit" class="submit-btn">Sign In</button>
        </form>
        
        <div class="footer">
            <p>Version <span class="version">3.2.1</span> | © 2024 NetManage Pro</p>
        </div>
    </div>
</body>
</html>
"""


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


async def log_http_event(
    request: Request,
    event_type: str,
    data: dict
):
    """Log HTTP trap event"""
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")

    await event_logger.log_event(
        trap_type="http",
        attacker_ip=client_ip,
        event_type=event_type,
        data={
            **data,
            "path": request.url.path,
            "user_agent": user_agent,
            "method": request.method
        }
    )


@http_trap_app.get("/", response_class=HTMLResponse)
async def root_get(request: Request):
    """GET / - Serve login page"""
    await log_http_event(request, "page_visit", {})
    return LOGIN_PAGE_HTML.format(error_message="")


@http_trap_app.get("/admin", response_class=HTMLResponse)
async def admin_get(request: Request):
    """GET /admin - Serve login page"""
    await log_http_event(request, "page_visit", {"page": "admin"})
    return LOGIN_PAGE_HTML.format(error_message="")


@http_trap_app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    """GET /login - Serve login page"""
    await log_http_event(request, "page_visit", {"page": "login"})
    return LOGIN_PAGE_HTML.format(error_message="")


@http_trap_app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """POST /login - Log credentials and show error"""
    await log_http_event(
        request,
        "credential_attempt",
        {"username": username, "password": password}
    )

    logger.info(f"HTTP trap credential attempt: {username}/{password}")

    # Return same page with error message
    error_html = '<div class="error-msg">Invalid credentials. Please try again.</div>'
    return LOGIN_PAGE_HTML.format(error_message=error_html)
