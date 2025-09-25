import imaplib
import email
from email.message import Message   
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import os

@dataclass
class EmailContent:
    uid: str
    sender: str
    subject: str
    date: str
    body_text: str
    attachment_filenames: List[str]
    raw_email_content: str

class FocusedGmailConnector:
    
    def __init__(self, email_address: str, password: str):
        self.email_address = email_address
        self.password = password
        self.imap_server = None
        self.is_connected = False
        
    def connect(self) -> bool:
        try:
            self.imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
            self.imap_server.login(self.email_address, self.password)
            self.imap_server.select('INBOX')
            self.is_connected = True
            logging.info(f"Connected to Gmail for {self.email_address}")
            return True
        except Exception as e:
            logging.error(f"Gmail connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        if self.imap_server and self.is_connected:
            try:
                self.imap_server.close()
                self.imap_server.logout()
                self.is_connected = False
                logging.info("Disconnected from Gmail")
            except Exception as e:
                logging.error(f"Error during disconnect: {e}")
    
    def get_emails_from_sender(self, sender_email: str, limit: int = 10) -> List[bytes]:
        if not self.is_connected:
            logging.error("Not connected to Gmail")
            return []
        try:
            status, messages = self.imap_server.search(None, f'FROM "{sender_email}"')
            if status == 'OK' and messages[0]:
                uids = messages[0].split()
                return uids[-limit:] if limit else uids
            return []
        except Exception as e:
            logging.error(f"Error searching emails from {sender_email}: {e}")
            return []
    
    def get_unread_emails_from_sender(self, sender_email: str, limit: int = 10) -> List[bytes]:
        if not self.is_connected:
            logging.error("Not connected to Gmail")
            return []
        try:
            status, messages = self.imap_server.search(None, f'FROM "{sender_email}" UNSEEN')
            if status == 'OK' and messages[0]:
                uids = messages[0].split()
                return uids[-limit:] if limit else uids
            return []
        except Exception as e:
            logging.error(f"Error searching unread emails from {sender_email}: {e}")
            return []
    
    def extract_email_content(self, uid: bytes) -> Optional[EmailContent]:
        if not self.is_connected:
            logging.error("Not connected to Gmail")
            return None
        try:
            status, msg_data = self.imap_server.fetch(uid, '(RFC822)')
            if status != 'OK' or not msg_data[0]:
                return None
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)
            sender = msg.get('From', '')
            subject = msg.get('Subject', '')
            date = msg.get('Date', '')
            body_text = self._extract_body_text(msg)
            attachment_filenames = self._extract_attachment_filenames(msg)
            raw_content = email_body.decode('utf-8', errors='ignore')
            return EmailContent(
                uid=uid.decode('utf-8'),
                sender=sender,
                subject=subject,
                date=date,
                body_text=body_text,
                attachment_filenames=attachment_filenames,
                raw_email_content=raw_content
            )
        except Exception as e:
            logging.error(f"Error extracting email content {uid}: {e}")
            return None
    
    def _extract_body_text(self, msg: Message) -> str:
        body_text = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get_content_disposition()
                    if content_disposition == 'attachment':
                        continue
                    if content_type == 'text/plain':
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text += payload.decode('utf-8', errors='ignore') + "\n"
                    elif content_type == 'text/html' and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            import re
                            html_content = payload.decode('utf-8', errors='ignore')
                            clean_text = re.sub(r'<[^>]+>', '', html_content)
                            body_text += clean_text + "\n"
            else:
                if msg.get_content_type() == 'text/plain':
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode('utf-8', errors='ignore')
        except Exception as e:
            logging.error(f"Error extracting body text: {e}")
        return body_text.strip()
    
    def _extract_attachment_filenames(self, msg: Message) -> List[str]:
        filenames = []
        try:
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        filenames.append(filename)
        except Exception as e:
            logging.error(f"Error extracting attachment filenames: {e}")
        return filenames
    
    def read_latest_email_from_sender(self, sender_email: str) -> Optional[EmailContent]:
        uids = self.get_emails_from_sender(sender_email, limit=1)
        if not uids:
            logging.info(f"No emails found from {sender_email}")
            return None
        return self.extract_email_content(uids[-1])
    
    def read_unread_emails_from_sender(self, sender_email: str, limit: int = 5) -> List[EmailContent]:
        uids = self.get_unread_emails_from_sender(sender_email, limit)
        if not uids:
            logging.info(f"No unread emails found from {sender_email}")
            return []
        results = []
        for uid in uids:
            content = self.extract_email_content(uid)
            if content:
                results.append(content)
        return results
    
    def download_attachments(self, email_content: EmailContent, download_folder: str = "downloads") -> List[str]:
        if not self.is_connected:
            logging.error("Not connected to Gmail")
            return []

        os.makedirs(download_folder, exist_ok=True)
        saved_files = []

        try:
            status, msg_data = self.imap_server.fetch(email_content.uid.encode(), '(RFC822)')
            if status != 'OK' or not msg_data[0]:
                logging.error(f"Failed to fetch email UID {email_content.uid} for attachments")
                return []

            msg = email.message_from_bytes(msg_data[0][1])

            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        filepath = os.path.join(download_folder, filename)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        saved_files.append(filepath)
                        logging.info(f"Saved attachment: {filepath}")

        except Exception as e:
            logging.error(f"Error downloading attachments: {e}")

        return saved_files
    
    def mark_as_read(self, uid: str):
        if not self.is_connected:
            return
        try:
            self.imap_server.store(uid.encode(), '+FLAGS', '\\Seen')
        except Exception as e:
            logging.error(f"Error marking email as read: {e}")
    
    def __enter__(self):
        if not self.is_connected:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()