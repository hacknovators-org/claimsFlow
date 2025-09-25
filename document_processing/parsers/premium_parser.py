from typing import List
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import Document
from pydantic import BaseModel, Field
import os

class PremiumBordereauxSchema(BaseModel):
    policy_number: str = Field(description="Policy number")
    insured_name: str = Field(description="Name of insured party")
    period_from: str = Field(description="Policy period start date (YYYY-MM-DD)")
    period_to: str = Field(description="Policy period end date (YYYY-MM-DD)")
    sum_insured: float = Field(description="Sum insured amount")
    gross_premium: float = Field(description="Gross premium amount")
    ri_premium: float = Field(description="Reinsurance premium")
    retention_premium: float = Field(description="Retention premium")
    underwriting_year: int = Field(description="Underwriting year")

class PremiumParser:
    
    def __init__(self, api_key: str = None):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
    
    def parse_premium_bordereaux(self, documents: List[Document]) -> List[PremiumBordereauxSchema]:
        parser = PydanticOutputParser(pydantic_object=PremiumBordereauxSchema)
        results = []
        
        for doc in documents:
            prompt = f"""
            Extract premium bordereaux data from the following text.
            Look for policy numbers, premium amounts, insured names, and policy periods.
            
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