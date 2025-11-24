"""
Formatter Tool for Markdown Reports
"""
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import ast

class FormatterInput(BaseModel):
    content: str = Field(..., description="Content to format")

class FormatterTool(BaseTool):
    name: str = "Report Formatter"
    description: str = (
        "Format research content into a professional Markdown report. "
        "Organizes overview, claims, evidence, and sources."
    )
    args_schema: Type[BaseModel] = FormatterInput
    
    def _run(self, content: str) -> str:
        try:
            # Try to parse content - handle multiple formats
            content_dict = None
            
            # Try JSON first
            try:
                content_dict = json.loads(content)
            except json.JSONDecodeError:
                pass
            
            # Try literal_eval (safer than eval)
            if content_dict is None:
                try:
                    content_dict = ast.literal_eval(content)
                except (ValueError, SyntaxError):
                    pass
            
            # If content is already a string report, return it
            if content_dict is None:
                if isinstance(content, str) and '##' in content:
                    return content
                # Otherwise create minimal report
                return f"# Research Report\n\n## Overview\n{content}\n\n## Sources\nNo sources provided.\n"
            
            # Build formatted report
            report = "# Research Report\n\n"
            
            report += "## Overview\n"
            overview = content_dict.get('overview', content_dict.get('description', 'No overview provided'))
            report += f"{overview}\n\n"
            
            report += "## Key Claims\n\n"
            claims = content_dict.get('claims', [])
            
            if claims:
                for i, claim in enumerate(claims, 1):
                    if isinstance(claim, dict):
                        claim_text = claim.get('claim', claim.get('text', str(claim)))
                        confidence = claim.get('claim_confidence', claim.get('confidence', 0))
                        evidence_list = claim.get('evidence', [])
                    elif isinstance(claim, str):
                        claim_text = claim
                        confidence = 0
                        evidence_list = []
                    else:
                        continue
                    
                    report += f"### Claim {i}\n"
                    report += f"**{claim_text}**\n\n"
                    
                    if confidence > 0:
                        report += f"*Confidence: {confidence:.0%}*\n\n"
                    
                    if evidence_list:
                        report += "**Supporting Evidence:**\n"
                        for evid in evidence_list[:2]:
                            if isinstance(evid, dict):
                                evid_text = evid.get('text', str(evid))
                                similarity = evid.get('similarity', 0)
                                report += f"- {evid_text}"
                                if similarity > 0:
                                    report += f" *(Relevance: {similarity:.0%})*"
                                report += "\n"
                            else:
                                report += f"- {evid}\n"
                        report += "\n"
            else:
                report += "*No specific claims extracted.*\n\n"
            
            report += "## Sources\n\n"
            sources = content_dict.get('sources', [])
            
            if sources:
                for i, source in enumerate(sources, 1):
                    if isinstance(source, dict):
                        title = source.get('title', f'Source {i}')
                        url = source.get('url', source.get('href', '#'))
                        report += f"{i}. [{title}]({url})\n"
                    else:
                        report += f"{i}. {source}\n"
            else:
                report += "*No sources provided.*\n"
            
            return report
            
        except Exception as e:
            # Return the content as-is with minimal formatting
            return f"# Research Report\n\n{content}\n"