"""
Crew Manager - Main Orchestration
"""
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import List, Dict
import json
from datetime import datetime

from ..tools.web_search_tool import WebSearchTool
from ..tools.summarizer_tool import SummarizerTool
from ..tools.claim_extractor_tool import AdvancedClaimExtractor
from ..tools.formatter_tool import FormatterTool
from ..memory.memory_system import MemorySystem
from ..utils.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, CREW_CONFIG
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class ResearchAssistantCrew:
    def __init__(self):
        logger.info("Initializing Research Assistant Crew...")
        
        self.llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            openai_api_key=OPENAI_API_KEY
        )
        
        self.memory = MemorySystem()
        self.web_search_tool = WebSearchTool()
        self.summarizer_tool = SummarizerTool()
        self.claim_extractor_tool = AdvancedClaimExtractor()
        self.formatter_tool = FormatterTool()
        
        self.init_agents()
        logger.info("Crew initialized successfully")
    
    def init_agents(self):
        self.controller = Agent(
            role='Research Coordinator',
            goal='Orchestrate research to deliver high-quality, evidence-based reports',
            backstory="""Senior research coordinator with 15 years of experience. 
            Expert at breaking down queries, delegating tasks, and ensuring quality.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.researcher = Agent(
            role='Information Retrieval Specialist',
            goal='Find relevant and credible information from web sources',
            backstory="""Expert at finding reliable information quickly. 
            Knows how to evaluate source credibility and extract relevant content.""",
            tools=[self.web_search_tool],
            verbose=True,
            llm=self.llm
        )
        
        self.analyzer = Agent(
            role='Research Analyst',
            goal='Analyze documents to extract key claims and supporting evidence',
            backstory="""Skilled analyst with expertise in critical thinking and evidence evaluation. 
            Excels at identifying key assertions and supporting evidence.""",
            tools=[self.summarizer_tool, self.claim_extractor_tool],
            verbose=True,
            llm=self.llm
        )
        
        self.writer = Agent(
            role='Research Report Writer',
            goal='Create clear, well-structured research reports',
            backstory="""Experienced academic writer specializing in evidence-based reports. 
            Knows how to structure information for maximum clarity.""",
            tools=[self.formatter_tool],
            verbose=True,
            llm=self.llm
        )
    
    def create_research_tasks(self, query: str) -> List[Task]:
        research_task = Task(
            description=f"""Search for information about: "{query}"
            
            Requirements:
            - Find at least 5 credible sources
            - Extract key information from each source
            - Include URLs for citations
            """,
            agent=self.researcher,
            expected_output="List of 5 sources with titles, URLs, and key excerpts"
        )
        
        analysis_task = Task(
            description=f"""Analyze the research results for: "{query}"
            
            Requirements:
            - Summarize main findings
            - Use the Claim Extractor tool to identify key claims
            - For each claim, identify supporting evidence
            - Rate confidence level for each claim
            """,
            agent=self.analyzer,
            expected_output="Structured analysis with claims, evidence, and confidence scores",
            context=[research_task]
        )
        
        writing_task = Task(
            description=f"""Create a comprehensive research report for: "{query}"
            
            Requirements:
            - Write clear overview (3-4 sentences)
            - Present key claims in structured format
            - Include supporting evidence for each claim
            - Add properly formatted sources section
            - Use Markdown formatting
            """,
            agent=self.writer,
            expected_output="Professional Markdown research report",
            context=[analysis_task]
        )
        
        return [research_task, analysis_task, writing_task]
    
    def evaluate_quality(self, output: str) -> Dict[str, float]:
        metrics = {
            'completeness': 0.0,
            'structure': 0.0,
            'evidence_ratio': 0.0,
            'overall': 0.0
        }
        
        required = ['Overview', 'Claims', 'Sources']
        metrics['completeness'] = sum(1 for s in required if s in output) / len(required)
        
        has_headers = output.count('#') >= 3
        has_bullets = output.count('*') >= 5 or output.count('-') >= 5
        metrics['structure'] = (has_headers + has_bullets) / 2
        
        claim_count = output.lower().count('claim')
        evidence_count = output.lower().count('evidence') + output.lower().count('according to')
        metrics['evidence_ratio'] = min(evidence_count / max(claim_count, 1), 1.0)
        
        metrics['overall'] = (
            metrics['completeness'] * 0.4 +
            metrics['structure'] * 0.3 +
            metrics['evidence_ratio'] * 0.3
        )
        
        return metrics
    
    def run(self, query: str, include_history: bool = False) -> Dict:
        try:
            logger.info(f"Starting research for: {query}")
            start_time = datetime.now()
            
            self.memory.add_to_session({'type': 'query', 'query': query})
            
            past_context = []
            if include_history:
                past_context = self.memory.search_past_queries(query, limit=3)
            
            tasks = self.create_research_tasks(query)
            
            crew = Crew(
                agents=[self.controller, self.researcher, self.analyzer, self.writer],
                tasks=tasks,
                process=Process.sequential,
                verbose=CREW_CONFIG['verbose']
            )
            
            logger.info("Executing crew...")
            result = crew.kickoff()
            
            quality_metrics = self.evaluate_quality(str(result))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            report = str(result)
            
            # IMPROVED METRICS CALCULATION
            # Count claims
            claims_count = 0
            for line in report.split('\n'):
                if 'Claim ' in line and any(str(i) in line for i in range(1, 20)):
                    claims_count += 1
            
            if claims_count == 0:
                in_claims = False
                for line in report.split('\n'):
                    if '## Key Claims' in line or 'Key Claims' in line:
                        in_claims = True
                    elif '##' in line:
                        in_claims = False
                    elif in_claims and line.strip() and line.strip()[0].isdigit():
                        claims_count += 1
            
            # Count sources
            sources_count = 0
            in_sources = False
            for line in report.split('\n'):
                if '## Sources' in line or 'Sources' in line:
                    in_sources = True
                elif '##' in line:
                    in_sources = False
                elif in_sources and line.strip() and (line.strip().startswith('*') or line.strip().startswith('-') or (line.strip() and line.strip()[0].isdigit())):
                    sources_count += 1
            
            if sources_count == 0:
                sources_count = report.count('http') + report.count('Encyclopedia') + report.count('Journal')
            
            logger.info(f"Metrics - Claims: {claims_count}, Sources: {sources_count}, Quality: {quality_metrics['overall']:.2%}")
            
            query_id = self.memory.store_query_result(
                query=query,
                response=report,
                metadata={
                    'quality_score': quality_metrics['overall'],
                    'claims_count': claims_count,
                    'evidence_count': claims_count,
                    'sources_count': sources_count
                }
            )
            
            self.memory.add_document_embedding(
                doc_text=report,
                metadata={'query': query, 'query_id': query_id, 'timestamp': datetime.now().isoformat()}
            )
            
            logger.info(f"Research completed in {execution_time:.2f} seconds")
            
            return {
                'success': True,
                'report': report,
                'metadata': {
                    'query': query,
                    'query_id': query_id,
                    'agents_used': 4,
                    'tasks_completed': len(tasks),
                    'execution_time': execution_time,
                    'quality_score': quality_metrics['overall'],
                    'quality_metrics': quality_metrics,
                    'claims_count': claims_count,
                    'sources_count': sources_count,
                    'past_context': past_context if include_history else []
                }
            }
        except Exception as e:
            logger.error(f"Error in crew execution: {e}")
            return {'success': False, 'error': str(e), 'report': f"Error: {str(e)}"}