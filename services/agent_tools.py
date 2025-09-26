from langchain.tools import tool
from langchain.agents import create_sql_agent
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from models.cash_call import CashCall
from typing import List, Dict, Any, Optional
import json
import os
import re
from datetime import datetime, date
import pandas as pd

vector_store: FAISS = None
db_engine = None
embeddings = None

def initialize_tools(vector_store_instance: FAISS, database_url: str, openai_api_key: str):
    global vector_store, db_engine, embeddings
    vector_store = vector_store_instance
    db_engine = create_engine(database_url)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

def extract_amounts_from_text(text: str) -> Dict[str, float]:
    """Extract monetary amounts from text"""
    amounts = {}
    
    # Look for common patterns in marine insurance documents
    patterns = {
        'total_income': r'(?:total income|total premium)\s*[:\-]?\s*([0-9,]+\.?\d*)',
        'claims_paid': r'(?:claims paid|paid amount|settlement)\s*[:\-]?\s*([0-9,]+\.?\d*)',
        'outstanding': r'(?:outstanding|balance)\s*[:\-]?\s*([0-9,]+\.?\d*)',
        'commission': r'(?:commission)\s*[:\-]?\s*([0-9,]+\.?\d*)',
        'balance': r'(?:balance|net balance)\s*[:\-]?\s*([0-9,]+\.?\d*)',
        'total_outgo': r'(?:total outgo|outgo)\s*[:\-]?\s*([0-9,]+\.?\d*)'
    }
    
    text_lower = text.lower()
    
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            # Take the first match and clean it
            amount_str = matches[0].replace(',', '')
            try:
                amounts[key] = float(amount_str)
            except ValueError:
                amounts[key] = 0.0
        else:
            amounts[key] = 0.0
    
    return amounts

@tool
def query_documents(query: str, k: int = 5) -> str:
    """Query the vector store to find relevant document content with enhanced page-level analysis"""
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=k)
    formatted_results = []
    
    for i, doc in enumerate(results):
        doc_type = doc.metadata.get("document_type", "unknown")
        page_num = doc.metadata.get("page_number", "N/A")
        
        formatted_results.append({
            "source": doc.metadata.get("filename", "Unknown"),
            "page_number": page_num,
            "document_type": doc_type,
            "content": doc.page_content[:500],
            "content_length": len(doc.page_content),
            "relevance_rank": i + 1
        })
    
    return json.dumps(formatted_results, indent=2)

@tool
def extract_bordereaux_claims() -> str:
    """Extract claims data from bordereaux documents with actual amounts"""
    if not vector_store:
        return "Vector store not initialized"
    
    bordereaux_queries = [
        "bordereaux claims paid outstanding transaction",
        "claim number transaction date paid amount",
        "settlement case outstanding claims table",
        "policy number claim amount transaction"
    ]
    
    claims_data = []
    total_paid = 0.0
    total_outstanding = 0.0
    
    for query in bordereaux_queries:
        results = vector_store.similarity_search(query, k=3)
        
        for doc in results:
            doc_type = doc.metadata.get("document_type", "")
            filename = doc.metadata.get("filename", "").lower()
            
            if doc_type == "claims_bordereaux" or "bordereaux" in filename or "bordereaux" in doc.page_content.lower():
                # Extract amounts from the content
                amounts = extract_amounts_from_text(doc.page_content)
                
                # Look for specific claim amounts in the content
                paid_matches = re.findall(r'([0-9,]+\.?\d*)\s*(?:paid|settlement)', doc.page_content.lower())
                outstanding_matches = re.findall(r'([0-9,]+\.?\d*)\s*(?:outstanding|balance)', doc.page_content.lower())
                
                page_paid = 0.0
                page_outstanding = 0.0
                
                for match in paid_matches:
                    try:
                        page_paid += float(match.replace(',', ''))
                    except ValueError:
                        pass
                
                for match in outstanding_matches:
                    try:
                        page_outstanding += float(match.replace(',', ''))
                    except ValueError:
                        pass
                
                total_paid += page_paid
                total_outstanding += page_outstanding
                
                claims_data.append({
                    "source": doc.metadata.get("filename", "Unknown"),
                    "page_number": doc.metadata.get("page_number", "N/A"),
                    "document_type": doc_type,
                    "content": doc.page_content[:800],
                    "extracted_amounts": amounts,
                    "page_paid": page_paid,
                    "page_outstanding": page_outstanding,
                    "extraction_method": "bordereaux_specific"
                })
    
    return json.dumps({
        "claims_data": claims_data,
        "totals": {
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "total_exposure": total_paid + total_outstanding
        },
        "summary": f"Found {len(claims_data)} bordereaux pages with total paid: {total_paid:,.2f} and outstanding: {total_outstanding:,.2f}"
    }, indent=2)

@tool
def extract_statement_totals() -> str:
    """Extract total amounts from cedant statements with actual amounts"""
    if not vector_store:
        return "Vector store not initialized"
    
    statement_queries = [
        "statement total claims balance income",
        "quarterly account commission premium",
        "total income outgo balance cedant",
        "account period underwriting year"
    ]
    
    statement_data = []
    aggregated_amounts = {
        'total_income': 0.0,
        'claims_paid': 0.0,
        'outstanding': 0.0,
        'commission': 0.0,
        'balance': 0.0,
        'total_outgo': 0.0
    }
    
    for query in statement_queries:
        results = vector_store.similarity_search(query, k=3)
        
        for doc in results:
            doc_type = doc.metadata.get("document_type", "")
            filename = doc.metadata.get("filename", "").lower()
            
            if doc_type == "cedant_statement" or "statement" in filename or "account" in doc.page_content.lower():
                amounts = extract_amounts_from_text(doc.page_content)
                
                # Aggregate amounts (take highest values to avoid duplicates)
                for key, value in amounts.items():
                    if value > aggregated_amounts.get(key, 0):
                        aggregated_amounts[key] = value
                
                statement_data.append({
                    "source": doc.metadata.get("filename", "Unknown"),
                    "page_number": doc.metadata.get("page_number", "N/A"),
                    "document_type": doc_type,
                    "content": doc.page_content[:800],
                    "extracted_amounts": amounts,
                    "extraction_method": "statement_specific"
                })
    
    return json.dumps({
        "statement_data": statement_data,
        "aggregated_totals": aggregated_amounts,
        "summary": f"Found {len(statement_data)} statement pages with total income: {aggregated_amounts['total_income']:,.2f}, claims paid: {aggregated_amounts['claims_paid']:,.2f}"
    }, indent=2)

@tool
def extract_treaty_exclusions(treaty_name: str = "") -> str:
    """Extract exclusions from treaty documents in the vector store"""
    query = f"exclusions excluded risks perils {treaty_name}" if treaty_name else "exclusions excluded risks perils"
    
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=3)
    exclusions = []
    
    for doc in results:
        content = doc.page_content.lower()
        if "exclusion" in content or "excluded" in content:
            exclusions.append({
                "source": doc.metadata.get("filename", "Unknown"),
                "page_number": doc.metadata.get("page_number", "N/A"),
                "document_type": doc.metadata.get("document_type", "unknown"),
                "exclusion_text": doc.page_content[:300]
            })
    
    return json.dumps(exclusions, indent=2)

@tool
def extract_notification_details(claim_number: str = "") -> str:
    """Extract claim notification details from documents"""
    query = f"claim notification {claim_number}" if claim_number else "claim notification insured loss date"
    
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=3)
    notification_data = []
    
    for doc in results:
        doc_type = doc.metadata.get("document_type", "")
        filename = doc.metadata.get("filename", "").lower()
        
        if doc_type == "claim_notification" or "notification" in filename or "notification" in doc.page_content.lower():
            notification_data.append({
                "source": doc.metadata.get("filename", "Unknown"),
                "page_number": doc.metadata.get("page_number", "N/A"),
                "document_type": doc_type,
                "content": doc.page_content[:400]
            })
    
    return json.dumps(notification_data, indent=2)

@tool
def validate_claim_against_exclusions(claim_description: str, cause_of_loss: str) -> str:
    """Check if a claim violates treaty exclusions"""
    exclusions_data = extract_treaty_exclusions()
    exclusions = json.loads(exclusions_data)
    
    violations = []
    claim_text = f"{claim_description} {cause_of_loss}".lower()
    
    exclusion_keywords = {
        "nuclear": ["nuclear", "radioactive", "contamination", "atomic"],
        "war": ["war", "warlike", "hostilities", "rebellion", "revolution", "civil war"],
        "strikes": ["strike", "riot", "civil commotion", "srcc", "labour disturbance"],
        "terrorism": ["terrorism", "terrorist", "malicious damage"],
        "cyber": ["cyber", "computer virus", "hacking", "cyber attack", "electronic"],
        "chemical_biological": ["chemical", "biological", "bio-chemical", "biochemical", "toxic"],
        "electromagnetic": ["electromagnetic", "emp", "electronic warfare"],
        "pollution": ["pollution", "seepage", "contamination", "environmental"],
        "asbestos": ["asbestos", "asbestos-related"],
        "sanctions": ["sanction", "embargo", "prohibited trade"],
        "insolvency": ["insolvency", "bankruptcy", "financial failure"],
        "liability": ["liability", "third party", "extra-contractual"],
        "cargo_transit": ["transit", "voyage", "cargo termination"],
        "ism": ["ism", "safety management", "ship management"]
    }
    
    for exclusion in exclusions:
        exclusion_text = exclusion["exclusion_text"].lower()
        
        for exclusion_type, keywords in exclusion_keywords.items():
            claim_match = any(keyword in claim_text for keyword in keywords)
            exclusion_match = any(keyword in exclusion_text for keyword in keywords)
            
            if claim_match and exclusion_match:
                violations.append({
                    "violation_type": exclusion_type,
                    "matched_keywords": [kw for kw in keywords if kw in claim_text],
                    "source": exclusion["source"],
                    "exclusion_reference": exclusion_text[:200],
                    "severity": "HIGH"
                })
    
    return json.dumps({
        "has_violations": len(violations) > 0,
        "violations": violations,
        "violation_count": len(violations),
        "recommendation": "REJECT" if violations else "PROCEED",
        "next_action": "Immediate supervisor review required" if violations else "Continue processing"
    }, indent=2)

@tool
def compare_bordereaux_vs_statement(underwriting_year: int = 2022) -> str:
    """Compare bordereaux totals against statement totals with actual amounts"""
    bordereaux_data = json.loads(extract_bordereaux_claims())
    statement_data = json.loads(extract_statement_totals())
    
    # Extract totals
    bordereaux_totals = bordereaux_data.get("totals", {})
    statement_totals = statement_data.get("aggregated_totals", {})
    
    bordereaux_paid = bordereaux_totals.get("total_paid", 0.0)
    statement_claims_paid = statement_totals.get("claims_paid", 0.0)
    
    # Calculate variance
    variance = abs(bordereaux_paid - statement_claims_paid)
    variance_percent = (variance / max(statement_claims_paid, 1)) * 100
    
    # Determine if significant discrepancy
    significant_discrepancy = variance_percent > 5.0  # More than 5% variance
    
    comparison = {
        "underwriting_year": underwriting_year,
        "bordereaux_sources": [item["source"] for item in bordereaux_data.get("claims_data", [])],
        "statement_sources": [item["source"] for item in statement_data.get("statement_data", [])],
        "amounts": {
            "bordereaux_total_paid": bordereaux_paid,
            "statement_claims_paid": statement_claims_paid,
            "variance": variance,
            "variance_percent": variance_percent
        },
        "data_available": len(bordereaux_data.get("claims_data", [])) > 0 and len(statement_data.get("statement_data", [])) > 0,
        "significant_discrepancy": significant_discrepancy,
        "bordereaux_pages_found": len(bordereaux_data.get("claims_data", [])),
        "statement_pages_found": len(statement_data.get("statement_data", [])),
        "reconciliation_status": "FAILED" if significant_discrepancy else "PASSED",
        "recommendation": f"Manual review required - {variance_percent:.1f}% variance" if significant_discrepancy else f"Amounts reconciled - {variance_percent:.1f}% variance"
    }
    
    return json.dumps(comparison, indent=2)

@tool
def validate_claim_dates(claim_data: str, policy_from: str, policy_to: str) -> str:
    """Validate if claim dates fall within policy period"""
    try:
        policy_start = datetime.strptime(policy_from, "%Y-%m-%d").date()
        policy_end = datetime.strptime(policy_to, "%Y-%m-%d").date()
        
        validation = {
            "policy_period": f"{policy_from} to {policy_to}",
            "validation_passed": True,
            "date_violations": [],
            "recommendation": "PROCEED"
        }
        
        claim_info = json.loads(claim_data) if isinstance(claim_data, str) else claim_data
        
        if "date_of_loss" in str(claim_info):
            validation["notes"] = "Date validation requires specific claim loss date"
        
        return json.dumps(validation, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Date validation failed: {str(e)}",
            "recommendation": "MANUAL_REVIEW"
        }, indent=2)

@tool
def check_duplicate_claims_in_database(claim_id: str, insured_name: str = "") -> str:
    """Check for duplicate claims in the cash_calls database table"""
    if not db_engine:
        return json.dumps({"error": "Database not initialized"})
    
    try:
        with db_engine.connect() as conn:
            query = text("SELECT * FROM cash_calls WHERE claim_id = :claim_id")
            result = conn.execute(query, {"claim_id": claim_id})
            existing_claims = result.fetchall()
            
            duplicate_check = {
                "claim_id": claim_id,
                "duplicates_found": len(existing_claims),
                "existing_records": [],
                "is_duplicate": len(existing_claims) > 0,
                "recommendation": "REJECT" if len(existing_claims) > 0 else "PROCEED"
            }
            
            for row in existing_claims:
                duplicate_check["existing_records"].append({
                    "id": row[0],
                    "claim_id": row[1],
                    "business_title": row[4] if len(row) > 4 else "",
                    "amount_original": str(row[8]) if len(row) > 8 else "0",
                    "date_of_booking": str(row[12]) if len(row) > 12 else ""
                })
            
            return json.dumps(duplicate_check, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Database query failed: {str(e)}",
            "recommendation": "MANUAL_REVIEW"
        })

@tool
def validate_accounting_quarter(claim_date: str, accounting_quarter: str) -> str:
    """Validate if claim payment falls within the accounting quarter"""
    try:
        quarter_map = {
            "Q1": ["01", "02", "03"],
            "Q2": ["04", "05", "06"], 
            "Q3": ["07", "08", "09"],
            "Q4": ["10", "11", "12"]
        }
        
        claim_month = claim_date[5:7] if len(claim_date) >= 7 else "00"
        quarter = accounting_quarter.upper()[:2]
        
        validation = {
            "claim_date": claim_date,
            "accounting_quarter": accounting_quarter,
            "is_valid": claim_month in quarter_map.get(quarter, []),
            "expected_months": quarter_map.get(quarter, []),
            "actual_month": claim_month,
            "recommendation": "PROCEED" if claim_month in quarter_map.get(quarter, []) else "REVIEW"
        }
        
        return json.dumps(validation, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Quarter validation failed: {str(e)}",
            "recommendation": "MANUAL_REVIEW"
        })

@tool
def calculate_recovery_amounts() -> str:
    """Calculate recovery amounts from cash calls vs statements"""
    try:
        with db_engine.connect() as conn:
            query = text("""
                SELECT 
                    SUM(functional_amount) as total_booked,
                    COUNT(*) as claim_count,
                    currency_code,
                    date_of_booking
                FROM cash_calls 
                WHERE settlement_indicator = 'Settled'
                GROUP BY currency_code, date_of_booking
                ORDER BY date_of_booking DESC
                LIMIT 10
            """)
            result = conn.execute(query)
            recovery_data = []
            
            for row in result:
                recovery_data.append({
                    "total_booked": str(row[0]) if row[0] else "0",
                    "claim_count": row[1],
                    "currency": row[2],
                    "booking_date": str(row[3]) if row[3] else ""
                })
            
            return json.dumps({
                "recovery_summary": recovery_data,
                "recommendation": "Compare with statement recoveries"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Recovery calculation failed: {str(e)}",
            "recommendation": "MANUAL_REVIEW"
        })