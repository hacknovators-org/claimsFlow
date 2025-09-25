from typing import List
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import Document
from pydantic import BaseModel, Field
import os

class TreatyContractSchema(BaseModel):
    treaty_name: str = Field(description="Name of the treaty contract")
    reinsured_name: str = Field(description="Name of the reinsured party")
    treaty_type: str = Field(description="Type of treaty (e.g., Marine Hull and Cargo)")
    underwriting_year: int = Field(description="Underwriting year")
    period_from: str = Field(description="Treaty period start date (YYYY-MM-DD)")
    period_to: str = Field(description="Treaty period end date (YYYY-MM-DD)")
    currency: str = Field(description="Currency code")
    commission_rate: float = Field(description="Commission rate as decimal")
    profit_commission_rate: float = Field(description="Profit commission rate as decimal")

class ReinsurerSchema(BaseModel):
    name: str = Field(description="Reinsurer company name")
    country: str = Field(description="Country of the reinsurer")
    share_percentage: float = Field(description="Share percentage as decimal")
    broker_name: str = Field(description="Broker name if applicable")
    is_statutory: bool = Field(description="Whether this is a statutory reinsurer")

class TreatyParser:
    
    def __init__(self, api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
    
    def parse_treaty_contract(self, documents: List[Document]) -> List[TreatyContractSchema]:
        parser = PydanticOutputParser(pydantic_object=TreatyContractSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract treaty contract information from the following text.
            Look for treaty names, parties, periods, commission rates, and contract terms.
            
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
    
    def parse_reinsurers(self, documents: List[Document]) -> List[ReinsurerSchema]:
        parser = PydanticOutputParser(pydantic_object=ReinsurerSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract reinsurer information from the following text.
            Look for reinsurer names, countries, share percentages, and broker details.
            
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