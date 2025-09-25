from typing import List
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import Document
from pydantic import BaseModel, Field
import os

class AccountStatementSchema(BaseModel):
    account_period: str = Field(description="Accounting period (e.g., Q1 2024)")
    underwriting_year: int = Field(description="Underwriting year")
    currency: str = Field(description="Currency code")
    cargo_premium: float = Field(description="Cargo premium amount")
    hull_premium: float = Field(description="Hull premium amount")
    total_income: float = Field(description="Total premium income")
    commission_rate: float = Field(description="Commission rate as decimal")
    commission_amount: float = Field(description="Commission amount")
    claims_paid: float = Field(description="Total claims paid")
    outstanding_claims: float = Field(description="Outstanding claims amount")
    balance: float = Field(description="Final balance amount")

class ReinsurerShareSchema(BaseModel):
    reinsurer_name: str = Field(description="Name of the reinsurer")
    broker_name: str = Field(description="Broker name if applicable")
    share_amount: float = Field(description="Share amount")
    share_percentage: float = Field(description="Share percentage as decimal")
    is_statutory: bool = Field(description="Whether this is a statutory share")

class StatementParser:
    
    def __init__(self, api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
    
    def parse_account_statement(self, documents: List[Document]) -> List[AccountStatementSchema]:
        parser = PydanticOutputParser(pydantic_object=AccountStatementSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract account statement data from the following text.
            Look for period information, premium amounts, claims, commissions, and balances.
            
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
    
    def parse_reinsurer_shares(self, documents: List[Document]) -> List[ReinsurerShareSchema]:
        parser = PydanticOutputParser(pydantic_object=ReinsurerShareSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract reinsurer share information from the following text.
            Look for reinsurer names, share amounts, percentages, and broker details.
            
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