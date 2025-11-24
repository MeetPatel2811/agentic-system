"""
Crew Manager - With Reinforcement Learning Concepts
Implements RL-based quality improvement and adaptive prompting
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
        logger.info("Initializing Research Assistant Crew with RL capabilities...")
        
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
        
        # REINFORCEMENT LEARNING COMPONENTS
        self.performance_history = []  # Track quality over time
        self.quality_threshold = 0.65  # Minimum acceptable quality (RL threshold)
        self.max_retries = 2           # Maximum retry attempts
        self.learning_enabled = True   # Enable/disable RL
        
        self.init_agents()
        logger.info(" Crew initialized with RL capabilities")
    
    def init_agents(self):
        """Initialize all specialized agents"""
        
        self.controller = Agent(
            role='Research Coordinator',
            goal='Orchestrate research to deliver high-quality, evidence-based reports',
            backstory="""Senior research coordinator with 15 years of experience managing 
            complex research projects. Expert at breaking down queries, delegating tasks 
            to specialists, and ensuring comprehensive coverage with quality outputs.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.researcher = Agent(
            role='Information Retrieval Specialist',
            goal='Find the most relevant and credible information from web sources',
            backstory="""Expert information specialist with advanced training in source 
            evaluation and information retrieval. Skilled at crafting effective search 
            queries, assessing credibility, and extracting relevant content. Prioritizes 
            recent, authoritative sources and provides proper citations.""",
            tools=[self.web_search_tool],
            verbose=True,
            llm=self.llm
        )
        
        self.analyzer = Agent(
            role='Research Analyst',
            goal='Analyze documents to extract key claims and supporting evidence',
            backstory="""Skilled research analyst with expertise in critical thinking, 
            evidence evaluation, and claim extraction. Excels at identifying key 
            assertions in text, finding supporting evidence, and assessing argument 
            strength using advanced NLP tools.""",
            tools=[self.summarizer_tool, self.claim_extractor_tool],
            verbose=True,
            llm=self.llm
        )
        
        self.writer = Agent(
            role='Research Report Writer',
            goal='Create clear, well-structured, and professional research reports',
            backstory="""Experienced academic writer specializing in evidence-based 
            research reports. Expert at structuring information for maximum clarity, 
            presenting claims with appropriate evidence, and formatting content 
            professionally with accessible language.""",
            tools=[self.formatter_tool],
            verbose=True,
            llm=self.llm
        )
    
    def generate_enhancement_context(self, metrics: Dict) -> str:
        
        issues = []
        
        # Check completeness
        if metrics['completeness'] < 0.8:
            issues.append("CRITICAL: Ensure ALL required sections are present (Overview, Key Claims, Sources)")
        
        # Check evidence ratio
        if metrics['evidence_ratio'] < 0.5:
            issues.append("IMPORTANT: Provide supporting evidence for EVERY claim made")
        
        # Check structure
        if metrics['structure'] < 0.7:
            issues.append("FORMAT: Use clear Markdown headers (##) and bullet points (*)")
        
        if not issues:
            return ""
        
        enhancement = "⚡ REINFORCEMENT LEARNING FEEDBACK - Previous attempt quality issues:\n"
        enhancement += "\n".join(f"• {issue}" for issue in issues)
        enhancement += "\n\nPLEASE ADDRESS THESE ISSUES IN THIS ATTEMPT."
        
        return enhancement
    
    def create_research_tasks(self, query: str, enhancement_context: str = "") -> List[Task]:
        """
        Create task pipeline with optional RL enhancement context
        
        Args:
            query: Research question
            enhancement_context: RL feedback from previous attempt (if any)
            
        Returns:
            List of tasks for the crew
        """
        
        # Prepend enhancement context if provided (RL feedback)
        context_prefix = f"\n{enhancement_context}\n" if enhancement_context else ""
        
        research_task = Task(
            description=f"""{context_prefix}
Search for information about: "{query}"

Requirements:
- Find at least 5 credible, authoritative sources
- Extract key information from each source
- Include full URLs for proper citations
- Focus on recent and reliable sources
- Provide brief summary of each source's relevance
""",
            agent=self.researcher,
            expected_output="List of 5 sources with titles, URLs, and key excerpts"
        )
        
        analysis_task = Task(
            description=f"""{context_prefix}
Analyze the research results for: "{query}"

Requirements:
- Summarize the main findings clearly
- Use the Claim Extractor tool to identify key factual claims
- For EACH claim, identify supporting evidence from sources
- Rate confidence level for each claim
- Note any contradictions or gaps in evidence
""",
            agent=self.analyzer,
            expected_output="Structured analysis with claims, evidence, and confidence scores",
            context=[research_task]
        )
        
        writing_task = Task(
            description=f"""{context_prefix}
Create a comprehensive research report for: "{query}"


""",
            agent=self.writer,
            expected_output="Professional Markdown research report with all required sections",
            context=[analysis_task]
        )
        
        return [research_task, analysis_task, writing_task]
    
    def evaluate_quality(self, output: str) -> Dict[str, float]:
        """
        RL REWARD SIGNAL: Evaluate output quality
        
        This serves as the reward function in reinforcement learning,
        providing feedback on how well the agents performed.
        
        Args:
            output: Generated research report
            
        Returns:
            Dictionary with quality metrics (reward signals)
        """
        metrics = {
            'completeness': 0.0,
            'structure': 0.0,
            'evidence_ratio': 0.0,
            'overall': 0.0
        }
        
        # Metric 1: Completeness (40% weight)
        required_sections = ['Overview', 'Claims', 'Sources']
        sections_present = sum(1 for section in required_sections if section in output)
        metrics['completeness'] = sections_present / len(required_sections)
        
        # Metric 2: Structure quality (30% weight)
        has_headers = output.count('#') >= 3
        has_bullets = output.count('*') >= 5 or output.count('-') >= 5
        metrics['structure'] = (has_headers + has_bullets) / 2
        
        # Metric 3: Evidence ratio (30% weight)
        claim_indicators = output.lower().count('claim')
        evidence_indicators = output.lower().count('evidence') + output.lower().count('according to')
        if claim_indicators > 0:
            metrics['evidence_ratio'] = min(evidence_indicators / claim_indicators, 1.0)
        else:
            metrics['evidence_ratio'] = 0.5
        
        # Overall quality score (weighted average) - This is the RL REWARD
        metrics['overall'] = (
            metrics['completeness'] * 0.4 +
            metrics['structure'] * 0.3 +
            metrics['evidence_ratio'] * 0.3
        )
        
        return metrics
    
    def run(self, query: str, include_history: bool = False) -> Dict:
        """
        Execute research with RL-based quality improvement
        
        RL Process:
        1. Execute crew and generate report
        2. Evaluate quality (compute reward signal)
        3. If quality < threshold, generate enhancement context (policy update)
        4. Retry with enhanced prompts (improved policy)
        5. Track performance over time (learning)
        
        Args:
            query: Research question
            include_history: Whether to include past context
            
        Returns:
            Dictionary with results and metadata including RL metrics
        """
        try:
            logger.info(f"🔬 Starting RL-enhanced research for: {query}")
            start_time = datetime.now()
            
            # Add to session memory
            self.memory.add_to_session({'type': 'query', 'query': query})
            
            # Check for similar past queries
            past_context = []
            if include_history:
                past_context = self.memory.search_past_queries(query, limit=3)
                logger.info(f"Found {len(past_context)} similar past queries")
            
            # INITIAL ATTEMPT (without RL enhancement)
            tasks = self.create_research_tasks(query)
            
            crew = Crew(
                agents=[self.controller, self.researcher, self.analyzer, self.writer],
                tasks=tasks,
                process=Process.sequential,
                verbose=CREW_CONFIG['verbose']
            )
            
            logger.info("⚡ Executing crew (initial attempt)...")
            result = crew.kickoff()
            
            # Evaluate quality (RL REWARD SIGNAL)
            quality_metrics = self.evaluate_quality(str(result))
            logger.info(f"📊 Initial quality score: {quality_metrics['overall']:.2%}")
            
            # RL FEEDBACK LOOP: Adaptive retry based on quality
            retry_count = 0
            improvements = []
            
            while (quality_metrics['overall'] < self.quality_threshold and 
                   retry_count < self.max_retries and 
                   self.learning_enabled):
                
                retry_count += 1
                logger.info(f"🔄 RL RETRY {retry_count}/{self.max_retries}: Quality {quality_metrics['overall']:.2%} below threshold {self.quality_threshold:.0%}")
                
                # RL POLICY: Generate enhancement instructions from metrics
                enhancement_context = self.generate_enhancement_context(quality_metrics)
                improvements.append({
                    'retry': retry_count,
                    'previous_quality': quality_metrics['overall'],
                    'enhancements': enhancement_context
                })
                
                logger.info(f"🎯 RL Enhancement applied:\n{enhancement_context}")
                
                # Create enhanced tasks with RL feedback
                enhanced_tasks = self.create_research_tasks(query, enhancement_context)
                
                crew = Crew(
                    agents=[self.controller, self.researcher, self.analyzer, self.writer],
                    tasks=enhanced_tasks,
                    process=Process.sequential,
                    verbose=CREW_CONFIG['verbose']
                )
                
                logger.info(f"⚡ Re-executing crew with RL-enhanced prompts (attempt {retry_count + 1})...")
                result = crew.kickoff()
                
                # Re-evaluate quality
                new_quality = self.evaluate_quality(str(result))
                improvement = new_quality['overall'] - quality_metrics['overall']
                
                logger.info(f"📈 Quality improvement: {quality_metrics['overall']:.2%} → {new_quality['overall']:.2%} ({improvement:+.1%})")
                
                quality_metrics = new_quality
            
            # RL LEARNING: Store performance for tracking
            self.performance_history.append({
                'query': query,
                'initial_quality': self.performance_history[-1]['quality'] if self.performance_history else quality_metrics['overall'],
                'final_quality': quality_metrics['overall'],
                'retries': retry_count,
                'improved': retry_count > 0,
                'improvements': improvements,
                'timestamp': datetime.now().isoformat()
            })
            
            # Calculate metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            report = str(result)
            
            # Count claims - improved logic
            claims_count = 0
            lines = report.split('\n')
            
            # Method 1: Look for "Claim X" patterns
            for line in lines:
                if 'Claim ' in line and any(str(i) in line for i in range(1, 20)):
                    claims_count += 1
            
            # Method 2: If no claims found, count numbered items in Key Claims section
            if claims_count == 0:
                in_claims_section = False
                for line in lines:
                    if '## Key Claims' in line or '##Key Claims' in line or 'Key Claims' in line:
                        in_claims_section = True
                    elif line.strip().startswith('##') and in_claims_section:
                        in_claims_section = False
                    elif in_claims_section and line.strip():
                        # Check if line starts with number
                        first_char = line.strip()[0] if line.strip() else ''
                        if first_char.isdigit() and '.' in line:
                            claims_count += 1
            
            # Count sources - improved logic
            sources_count = 0
            in_sources_section = False
            
            for line in lines:
                if '## Sources' in line or 'Sources Consulted' in line or 'Sources:' in line:
                    in_sources_section = True
                elif line.strip().startswith('##') and in_sources_section:
                    in_sources_section = False
                elif in_sources_section and line.strip():
                    # Count bullet points or numbered items
                    if line.strip().startswith(('*', '-', '•')):
                        sources_count += 1
                    elif line.strip()[0].isdigit() if line.strip() else False:
                        sources_count += 1
            
            # Fallback: count URLs or known source indicators
            if sources_count == 0:
                sources_count = (report.count('http://') + report.count('https://') + 
                               report.count('Encyclopedia') + report.count('Journal') + 
                               report.count('Publication'))
            
            logger.info(f"📊 Final Metrics - Quality: {quality_metrics['overall']:.2%}, Claims: {claims_count}, Sources: {sources_count}, RL Retries: {retry_count}")
            
            # Store in memory
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
            
            # Add to vector store for semantic search
            self.memory.add_document_embedding(
                doc_text=report,
                metadata={
                    'query': query,
                    'query_id': query_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"✅ Research completed in {execution_time:.2f}s with {retry_count} RL retries")
            
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
                    'rl_retries': retry_count,
                    'rl_improved': retry_count > 0,
                    'rl_improvements': improvements if retry_count > 0 else [],
                    'past_context': past_context if include_history else []
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in crew execution: {e}")
            return {
                'success': False,
                'error': str(e),
                'report': f"Error: {str(e)}"
            }
    
    def get_rl_performance_stats(self) -> Dict:
        """
        Get RL performance statistics
        
        Analyzes improvement over time to demonstrate learning
        
        Returns:
            Dictionary with RL performance metrics
        """
        if not self.performance_history:
            return {
                'total_queries': 0,
                'average_quality': 0.0,
                'improvement_rate': 0.0,
                'retry_rate': 0.0,
                'quality_trend': 'no_data'
            }
        
        total_queries = len(self.performance_history)
        avg_quality = sum(p['final_quality'] for p in self.performance_history) / total_queries
        improved_queries = sum(1 for p in self.performance_history if p['improved'])
        total_retries = sum(p['retries'] for p in self.performance_history)
        
        # Calculate quality trend
        if len(self.performance_history) >= 2:
            recent_avg = sum(p['final_quality'] for p in self.performance_history[-5:]) / min(5, len(self.performance_history[-5:]))
            early_avg = sum(p['final_quality'] for p in self.performance_history[:5]) / min(5, len(self.performance_history[:5]))
            trend = 'improving' if recent_avg > early_avg else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'total_queries': total_queries,
            'average_quality': avg_quality,
            'improvement_rate': improved_queries / total_queries if total_queries > 0 else 0,
            'retry_rate': total_retries / total_queries if total_queries > 0 else 0,
            'quality_trend': trend,
            'total_improvements': improved_queries,
            'total_retries': total_retries
        }