from typing import List, Type, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import Document
from pydantic import BaseModel, Field
from datetime import datetime
import os

class ClaimNotificationSchema(BaseModel):
    claim_number: str = Field(description="Unique claim identification number")
    policy_number: str = Field(description="Policy number associated with the claim")
    insured_name: str = Field(description="Name of the insured party")
    date_of_loss: str = Field(description="Date when the loss occurred (YYYY-MM-DD)")
    notification_date: str = Field(description="Date when claim was notified (YYYY-MM-DD)")
    sum_insured: float = Field(description="Total sum insured amount")
    gross_claim_amount: float = Field(description="Gross amount claimed")
    claim_type: str = Field(description="Type of claim (e.g., Cargo Loss, Hull Damage)")
    class_code: str = Field(description="Classification code for the claim")

class CashCallSchema(BaseModel):
    claim_id: str = Field(description="Claim reference number")
    worksheet_id: str = Field(description="Worksheet identification")
    business_id: str = Field(description="Business reference ID")
    claim_name: str = Field(description="Name or description of the claim")
    date_of_loss: str = Field(description="Loss occurrence date (YYYY-MM-DD)")
    currency_code: str = Field(description="Currency code (USD, EUR, etc.)")
    amount_original: float = Field(description="Original claim amount")
    payment_partner_name: str = Field(description="Payment partner/broker name")

class ClaimBordereauxSchema(BaseModel):
    claim_number: str = Field(description="Associated claim number")
    transaction_date: str = Field(description="Transaction date (YYYY-MM-DD)")
    transaction_type: str = Field(description="Type of transaction (S=Settlement, C=Case)")
    paid_amount: float = Field(description="Amount paid")
    outstanding_amount: float = Field(description="Outstanding amount")

class ClaimParser:
    
    def __init__(self, api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
    
    def parse_claim_notification(self, documents: List[Document]) -> List[ClaimNotificationSchema]:
        parser = PydanticOutputParser(pydantic_object=ClaimNotificationSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract claim notification data from the following text. 
            Return structured data in the specified JSON format.
            
            {parser.get_format_instructions()}
            
            Text content:
            {doc.page_content}
            """
            
            try:
                response = self.llm.invoke(prompt)
                record = parser.parse(response.content)
                results.append(record)
            except Exception:
                continue
        
        return results
    
    def parse_cash_calls(self, documents: List[Document]) -> List[CashCallSchema]:
        parser = PydanticOutputParser(pydantic_object=CashCallSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract cash call data from the following text.
            Look for claim IDs, worksheet references, amounts, and partner information.
            
            {parser.get_format_instructions()}
            
            Text content:
            {doc.page_content}
            """
            
            try:
                response = self.llm.invoke(prompt)
                record = parser.parse(response.content)
                results.append(record)
            except Exception:
                continue
        
        return results
    
    def parse_claim_bordereaux(self, documents: List[Document]) -> List[ClaimBordereauxSchema]:
        parser = PydanticOutputParser(pydantic_object=ClaimBordereauxSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract claims bordereaux data from tabular data.
            Look for claim numbers, transaction dates, amounts paid and outstanding.
            
            {parser.get_format_instructions()}
            
            Text content:
            {doc.page_content}
            """
            
            try:
                response = self.llm.invoke(prompt)
                record = parser.parse(response.content)
                results.append(record)
            except Exception:
                continue
        
        return results