from typing import List, Dict, Any
from services.email_analyzer import SimpleEmailAnalyzer
from services.gmail_reader import FocusedGmailConnector  # import your Gmail connector class
from schemas.emails import EmailAnalysisResponse
from dotenv import load_dotenv
import os
load_dotenv('../.env')


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

EMAIL_HOST = os.getenv("EMAIL_HOST")
if not EMAIL_HOST:
    raise ValueError("EMAIL_HOST environment variable not set")

EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
if not EMAIL_APP_PASSWORD:
    raise ValueError("EMAIL_APP_PASSWORD environment variable not set")


from dataclasses import asdict

async def analyze_emails_from_sender(sender_email: str) -> List[EmailAnalysisResponse]:
    """
    Fetch latest and unread emails from a specific sender,
    analyze with OpenAI, and return structured results.
    """
    results: List[EmailAnalysisResponse] = []

    gmail = FocusedGmailConnector(EMAIL_HOST, EMAIL_APP_PASSWORD)

    with gmail:
        analyzer = SimpleEmailAnalyzer(api_key=OPENAI_API_KEY)

        # Latest email
        latest_email = gmail.read_latest_email_from_sender(sender_email)
        if latest_email:
            files = gmail.download_attachments(latest_email, download_folder="downloads")
            print(f"Downloaded attachments: {files}")
            analysis = analyzer.analyze_email_content(
                latest_email.subject,
                latest_email.body_text,
                latest_email.attachment_filenames
            )
            results.append(
                EmailAnalysisResponse(
                    sender=latest_email.sender,
                    subject=latest_email.subject,
                    date=latest_email.date,
                    body_preview=latest_email.body_text[:200],
                    attachments=latest_email.attachment_filenames,
                    analysis=asdict(analysis),  # ✅ Convert to dict
                )
            )

        # Unread emails
        unread_emails = gmail.read_unread_emails_from_sender(sender_email)
        for email_content in unread_emails:
            analysis = analyzer.analyze_email_content(
                email_content.subject,
                email_content.body_text,
                email_content.attachment_filenames
            )
            results.append(
                EmailAnalysisResponse(
                    sender=email_content.sender,
                    subject=email_content.subject,
                    date=email_content.date,
                    body_preview=email_content.body_text[:200],
                    attachments=email_content.attachment_filenames,
                    analysis=asdict(analysis),  # ✅ Convert to dict
                )
            )

    return results