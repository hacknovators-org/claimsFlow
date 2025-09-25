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
from datetime import datetime, date
import pandas as pd

# Global variables for vector store and database
vector_store: FAISS = None
db_engine = None
embeddings = None

def initialize_tools(vector_store_instance: FAISS, database_url: str, openai_api_key: str):
    global vector_store, db_engine, embeddings
    vector_store = vector_store_instance
    db_engine = create_engine(database_url)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

@tool
def query_documents(query: str, k: int = 5) -> str:
    """Query the vector store to find relevant document content"""
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=k)
    formatted_results = []
    
    for i, doc in enumerate(results):
        formatted_results.append({
            "source": doc.metadata.get("filename", "Unknown"),
            "content": doc.page_content[:500],
            "relevance_rank": i + 1
        })
    
    return json.dumps(formatted_results, indent=2)

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
                "exclusion_text": doc.page_content[:300]
            })
    
    return json.dumps(exclusions, indent=2)

@tool
def validate_claim_against_exclusions(claim_description: str, cause_of_loss: str) -> str:
    """Check if a claim violates treaty exclusions"""
    exclusions_data = extract_treaty_exclusions()
    exclusions = json.loads(exclusions_data)
    
    violations = []
    claim_text = f"{claim_description} {cause_of_loss}".lower()
    
    # Comprehensive exclusions based on actual treaty terms
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
def extract_bordereaux_claims() -> str:
    """Extract claims data from bordereaux documents"""
    query = "bordereaux claims paid outstanding transaction settlement"
    
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=5)
    claims_data = []
    
    for doc in results:
        if "bordereaux" in doc.metadata.get("filename", "").lower():
            claims_data.append({
                "source": doc.metadata.get("filename", "Unknown"),
                "content": doc.page_content[:400],
                "document_type": "bordereaux"
            })
    
    return json.dumps(claims_data, indent=2)

@tool
def extract_statement_totals() -> str:
    """Extract total amounts from cedant statements"""
    query = "statement total claims paid outstanding balance"
    
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=3)
    statement_data = []
    
    for doc in results:
        if "statement" in doc.metadata.get("filename", "").lower():
            statement_data.append({
                "source": doc.metadata.get("filename", "Unknown"),
                "content": doc.page_content[:400],
                "document_type": "statement"
            })
    
    return json.dumps(statement_data, indent=2)

@tool
def compare_bordereaux_vs_statement(underwriting_year: int) -> str:
    """Compare bordereaux totals against statement totals for specific year"""
    bordereaux_data = json.loads(extract_bordereaux_claims())
    statement_data = json.loads(extract_statement_totals())
    
    comparison = {
        "underwriting_year": underwriting_year,
        "bordereaux_sources": [item["source"] for item in bordereaux_data],
        "statement_sources": [item["source"] for item in statement_data],
        "data_available": len(bordereaux_data) > 0 and len(statement_data) > 0,
        "requires_manual_verification": True,
        "recommendation": "Manual review required for amount reconciliation"
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
            # Check by claim_id
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
def extract_notification_details(claim_number: str = "") -> str:
    """Extract claim notification details from documents"""
    query = f"claim notification {claim_number}" if claim_number else "claim notification insured loss date"
    
    if not vector_store:
        return "Vector store not initialized"
    
    results = vector_store.similarity_search(query, k=3)
    notification_data = []
    
    for doc in results:
        if "notification" in doc.metadata.get("filename", "").lower():
            notification_data.append({
                "source": doc.metadata.get("filename", "Unknown"),
                "content": doc.page_content[:400],
                "document_type": "notification"
            })
    
    return json.dumps(notification_data, indent=2)

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
