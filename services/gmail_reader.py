import imaplib
import email
from email.message import Message   # ✅ Fix: import Message explicitly
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from email_analyzer import SimpleEmailAnalyzer


@dataclass
class EmailContent:
    """Container for extracted email content"""
    uid: str
    sender: str
    subject: str
    date: str
    body_text: str
    attachment_filenames: List[str]
    raw_email_content: str


class FocusedGmailConnector:
    """Gmail connector focused on reading emails from specific senders"""
    
    def __init__(self, email_address: str, password: str):
        self.email_address = email_address
        self.password = password
        self.imap_server = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """Connect to Gmail IMAP server"""
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
        """Disconnect from Gmail"""
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
        """Extract text body from email message"""
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
        """Extract attachment filenames from email"""
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


# Example usage
# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    gmail = FocusedGmailConnector("ephymucira9@gmail.com", "adtm hhjg iymh aqpo")
    analyzer = SimpleEmailAnalyzer(api_key="REMOVED_API_KEY")   # 👈 put your OpenAI key here
    
    with gmail:
        sender_email = "Maundu@kenyare.co.ke"
        print(f"Looking for emails from: {sender_email}")
        
        latest_email = gmail.read_latest_email_from_sender(sender_email)
        if latest_email:
            print(f"\n=== LATEST EMAIL FROM {sender_email} ===")
            print(f"UID: {latest_email.uid}")
            print(f"Subject: {latest_email.subject}")
            print(f"Date: {latest_email.date}")
            print(f"Attachments: {latest_email.attachment_filenames}")

            # 🔥 Pass into analyzer
            analysis = analyzer.analyze_email_content(
                latest_email.subject,
                latest_email.body_text,
                latest_email.attachment_filenames
            )
            report = analyzer.generate_report(analysis)
            print("\n" + report)
        else:
            print(f"No emails found from {sender_email}")
        
        print(f"\n=== UNREAD EMAILS FROM {sender_email} ===")
        unread_emails = gmail.read_unread_emails_from_sender(sender_email)
        print(f"Found {len(unread_emails)} unread emails")
        for i, email_content in enumerate(unread_emails, 1):
            print(f"\n{i}. {email_content.subject} - {len(email_content.attachment_filenames)} attachments")

            # 🔥 Analyze each unread email too
            analysis = analyzer.analyze_email_content(
                email_content.subject,
                email_content.body_text,
                email_content.attachment_filenames
            )
            report = analyzer.generate_report(analysis)
            print(report)
