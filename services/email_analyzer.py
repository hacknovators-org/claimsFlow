import json
import logging
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
import os

class DocumentType(Enum):
    CLAIMS_NOTIFICATION = "Claims Notification Document"
    CLAIMS_BORDEREAUX = "Claims Bordereaux" 
    CEDANT_STATEMENT = "Cedant/Insurer Statement"
    TREATY_SLIP = "Treaty Slip/Contract"
    SICS_TREATY_SLIP = "SICS Treaty Slip"

MANDATORY_DOCS = [
    DocumentType.CLAIMS_NOTIFICATION.value,
    DocumentType.CLAIMS_BORDEREAUX.value,
    DocumentType.CEDANT_STATEMENT.value,
]

@dataclass
class DocumentFound:
    filename: str
    document_type: DocumentType
    confidence: str
    key_identifiers: List[str]

@dataclass
class AnalysisReport:
    email_subject: str
    sender: str
    documents_found: List[DocumentFound]
    all_documents_present: bool
    missing_documents: List[str]
    completion_status: str
    summary: str

class SimpleEmailAnalyzer:
    
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not provided and not found in environment variables")
            
        self.client = OpenAI(api_key=api_key)

    def create_analysis_prompt(self, email_subject: str, email_body: str, attachments: List[str]) -> str:
        prompt = f"""
You are an insurance document expert. Analyze this email to determine which required documents are present.

EMAIL SUBJECT: {email_subject}

EMAIL BODY:
{email_body}

ATTACHMENT FILES:
{chr(10).join([f"- {filename}" for filename in attachments])}

MANDATORY DOCUMENTS (all 3 must be present for completeness):
1. Claims Notification Document - Contains claim reference, insured details, loss date
2. Claims Bordereaux - Tabular claims data with amounts, dates, policy numbers  
3. Cedant/Insurer Statement - Quarterly statement with totals and recoveries

IMPORTANT: A single PDF file may contain multiple document types on different pages. For example:
- Page 1: Claims Statement
- Page 2: Claims Bordereaux
This should count as having BOTH documents present.

ANALYSIS RULES:
- If a PDF contains tabular data AND statement information, mark BOTH bordereaux AND statement as present
- Look for keywords indicating multiple document types within single files
- Consider combined documents as complete submissions

Respond in this exact JSON format:
{{
    "analysis": {{
        "email_subject": "{email_subject}",
        "sender": "extracted from email",
        "documents_found": [
            {{
                "filename": "exact_filename.pdf",
                "document_type": "Claims Bordereaux",
                "confidence": "High",
                "key_identifiers": ["Table data", "Transaction dates"]
            }},
            {{
                "filename": "exact_filename.pdf",
                "document_type": "Cedant/Insurer Statement",
                "confidence": "High", 
                "key_identifiers": ["Account balance", "Total income"]
            }}
        ],
        "all_documents_present": true,
        "missing_documents": [],
        "completion_status": "Complete",
        "summary": "All mandatory documents found. Combined PDF contains both bordereaux and statement."
    }}
}}

Mark as "Complete" if all 3 mandatory document types are identified, even if in combined files.
"""
        return prompt

    def call_openai_api(self, prompt: str) -> Dict:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert insurance document analyst. Recognize that single files can contain multiple document types. Always respond with valid JSON in the exact format requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            return json.loads(content)

        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return {"error": str(e)}

    def analyze_email_content(self, email_subject: str, email_body: str, attachments: List[str]) -> AnalysisReport:
        try:
            prompt = self.create_analysis_prompt(email_subject, email_body, attachments)
            response = self.call_openai_api(prompt)

            if "error" in response:
                return AnalysisReport(
                    email_subject=email_subject,
                    sender="Unknown",
                    documents_found=[],
                    all_documents_present=False,
                    missing_documents=[doc for doc in MANDATORY_DOCS],
                    completion_status="Error",
                    summary=f"Analysis failed: {response['error']}"
                )

            analysis_data = response.get("analysis", {})

            documents_found = []
            for doc_data in analysis_data.get("documents_found", []):
                try:
                    doc_type = DocumentType(doc_data["document_type"])
                    document = DocumentFound(
                        filename=doc_data.get("filename", ""),
                        document_type=doc_type,
                        confidence=doc_data.get("confidence", "Low"),
                        key_identifiers=doc_data.get("key_identifiers", [])
                    )
                    documents_found.append(document)
                except (ValueError, KeyError) as e:
                    logging.warning(f"Error parsing document: {e}")

            found_doc_types = [doc.document_type.value for doc in documents_found]
            missing_docs = [doc_type for doc_type in MANDATORY_DOCS if doc_type not in found_doc_types]

            return AnalysisReport(
                email_subject=analysis_data.get("email_subject", email_subject),
                sender=analysis_data.get("sender", "Unknown"),
                documents_found=documents_found,
                all_documents_present=len(missing_docs) == 0,
                missing_documents=missing_docs,
                completion_status="Complete" if len(missing_docs) == 0 else "Incomplete",
                summary=analysis_data.get("summary", "No summary provided")
            )

        except Exception as e:
            logging.error(f"Email analysis error: {e}")
            return AnalysisReport(
                email_subject=email_subject,
                sender="Unknown", 
                documents_found=[],
                all_documents_present=False,
                missing_documents=[doc for doc in MANDATORY_DOCS],
                completion_status="Error",
                summary=f"Analysis error: {str(e)}"
            )

    def generate_report(self, analysis: AnalysisReport) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("CLAIMS EMAIL ANALYSIS REPORT")
        lines.append("=" * 60)

        lines.append(f"Subject: {analysis.email_subject}")
        lines.append(f"Sender: {analysis.sender}")
        lines.append(f"Status: {analysis.completion_status}")
        lines.append("")

        lines.append(f"DOCUMENTS FOUND ({len(analysis.documents_found)}):")
        if analysis.documents_found:
            for i, doc in enumerate(analysis.documents_found, 1):
                lines.append(f"{i}. {doc.filename}")
                lines.append(f"   Type: {doc.document_type.value}")
                lines.append(f"   Confidence: {doc.confidence}")
                if doc.key_identifiers:
                    lines.append(f"   Key Data: {', '.join(doc.key_identifiers)}")
                lines.append("")
        else:
            lines.append("   No documents identified")
            lines.append("")

        if analysis.all_documents_present:
            lines.append("✅ COMPLETENESS: ALL MANDATORY DOCUMENTS PRESENT")
        else:
            lines.append("❌ COMPLETENESS: MISSING DOCUMENTS")
            lines.append("")
            lines.append("Missing Documents:")
            for missing in analysis.missing_documents:
                lines.append(f"   - {missing}")

        lines.append("")
        lines.append("SUMMARY:")
        lines.append(analysis.summary)
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)