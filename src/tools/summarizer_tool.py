"""
Summarizer Tool using LLM
"""
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from ..utils.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE

class SummarizerInput(BaseModel):
    text: str = Field(..., description="Text to summarize")

class SummarizerTool(BaseTool):
    name: str = "Text Summarizer"
    description: str = (
        "Summarize long text into concise key points. "
        "Extracts main ideas, arguments, and important details."
    )
    args_schema: Type[BaseModel] = SummarizerInput
    
    def _run(self, text: str) -> str:
        """
        Summarize the provided text
        """
        try:
            llm = ChatOpenAI(
                model=MODEL_NAME,
                temperature=TEMPERATURE,
                openai_api_key=OPENAI_API_KEY
            )
            
            max_chars = 4000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = f"""Summarize the following text concisely, focusing on:
- Main arguments and key claims
- Important findings and conclusions
- Supporting details and evidence

Provide a 3-5 sentence summary.

Text:
{text}

Summary:"""
            
            # Use invoke() instead of predict()
            response = llm.invoke(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
            
        except Exception as e:
            return f"Summarization error: {str(e)}"