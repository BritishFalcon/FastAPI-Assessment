import asyncio
from http.client import HTTPException

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from email.message import EmailMessage
import aiosmtplib
from jinja2 import Template

from templates import *

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM")


class NotifyRequest(BaseModel):
    to: EmailStr
    notification_type: NotificationType
    params: dict


app = FastAPI(root_path="/notification")


async def send_email(to: str, subject: str, html: str):
    email = EmailMessage()
    email["From"] = SMTP_FROM
    email["To"] = to
    email["Subject"] = subject
    email.set_content(html, subtype="html")

    try:
        await aiosmtplib.send(
            email,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e


@app.post("/internal/notify", status_code=202)
async def notify(request: NotifyRequest):
    template = TEMPLATES.get(request.notification_type)
    if not template:
        raise HTTPException(status_code=400, detail="Invalid notification type!")

    # Format issues https://stackoverflow.com/questions/54166647/formatting-html-with-python
    try:
        subject = template["subject"]
        template = Template(template["html"])
        body = template.render(**request.params)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter(s) used: {e}")

    asyncio.create_task(send_email(request.to, subject, body))

    return {"message": "Notification queued!"}

