"""
Streamlit Frontend for Research Assistant
Professional UI with real-time updates and comprehensive features
"""

import streamlit as st
import requests
from datetime import datetime
import time
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import API_HOST, API_PORT

# Configuration
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================

st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    
    /* Report box styling */
    .report-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 20px 0;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 10px;
        border: none;
    }
    
    .stButton>button:hover {
        background-color: #1557a0;
    }
    
    /* Progress indicators */
    .status-text {
        font-size: 1.1rem;
        color: #1f77b4;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================

# Initialize session state variables
if 'research_history' not in st.session_state:
    st.session_state.research_history = []

if 'current_report' not in st.session_state:
    st.session_state.current_report = None

if 'show_history' not in st.session_state:
    st.session_state.show_history = False

# ==================== HELPER FUNCTIONS ====================

def check_api_health():
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200, response.json()
    except:
        return False, None

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

# ==================== SIDEBAR ====================

with st.sidebar:
    st.title("🔬 Research Assistant")
    st.markdown("*Powered by CrewAI & GPT-4*")
    st.markdown("---")
    
    # System status
    st.subheader("🔋 System Status")
    is_healthy, health_data = check_api_health()
    
    if is_healthy:
        st.success("✅ System Online")
        if health_data and health_data.get('crew_initialized'):
            st.info("🤖 Agents Ready")
    else:
        st.error("❌ Cannot connect to backend")
        st.warning("Please start the API server:\n`python api/main.py`")
    
    st.markdown("---")
    
    # Memory Statistics
    st.subheader("💾 Memory Stats")
    
    if is_healthy:
        try:
            stats_response = requests.get(f"{API_BASE_URL}/memory/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Total Queries", 
                        stats['long_term']['total_queries']
                    )
                    st.metric(
                        "Documents", 
                        stats['vector_store']['documents']
                    )
                
                with col2:
                    st.metric(
                        "Claims", 
                        stats['long_term']['total_claims']
                    )
                    st.metric(
                        "Sources", 
                        stats['long_term']['total_sources']
                    )
        except:
            st.warning("Could not load stats")
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    include_history = st.checkbox(
        "Include past context", 
        value=False,
        help="Search similar past queries for context"
    )
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("🎯 Quick Actions")
    
    if st.button("📜 View History"):
        st.session_state.show_history = True
    
    if st.button("🗑️ Clear Session"):
        try:
            requests.delete(f"{API_BASE_URL}/memory/clear-session", timeout=5)
            st.success("Session cleared!")
            time.sleep(1)
            st.rerun()
        except:
            st.error("Failed to clear session")
    
    # Info section
    st.markdown("---")
    st.markdown("""
    ### About
    This research assistant uses:
    - 🤖 4 Specialized Agents
    - 🔧 4 Advanced Tools
    - 💾 3-Tier Memory System
    - 🧠 GPT-4 & NLP Models
    """)

# ==================== MAIN CONTENT ====================

# Header
st.markdown("<h1 class='main-header'>🔬 AI Research Assistant</h1>", unsafe_allow_html=True)

# Introduction
st.markdown("""
### Welcome to your intelligent research assistant!

Ask any question and I'll:
1. 🔍 Search the web for credible sources
2. 🧠 Analyze content and extract key claims
3. 📊 Match claims with supporting evidence
4. 📄 Generate a comprehensive, structured report

**Powered by multi-agent AI orchestration with advanced NLP.**
""")

st.markdown("---")

# Query Input
st.subheader("💬 Ask Your Research Question")

col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "Enter your research question:",
        placeholder="e.g., What are the latest developments in quantum computing?",
        key="query_input",
        label_visibility="collapsed"
    )

with col2:
    st.write("")  # Spacing
    search_button = st.button("🔍 Research", type="primary", use_container_width=True)

# Example queries
with st.expander("💡 Example Questions"):
    st.markdown("""
    - What is agentic AI and how does it work?
    - How do multi-agent systems coordinate tasks?
    - What are the latest developments in large language models?
    - Explain reinforcement learning in the context of AI agents
    - What are the key challenges in building agentic systems?
    """)

# ==================== QUERY PROCESSING ====================

if search_button and query:
    if len(query.strip()) < 3:
        st.error("⚠️ Please enter a question with at least 3 characters")
    else:
        with st.spinner(""):
            try:
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Stage 1: Searching
                status_text.markdown(
                    "<p class='status-text'>🔍 Searching the web for sources...</p>", 
                    unsafe_allow_html=True
                )
                progress_bar.progress(25)
                time.sleep(0.3)
                
                # Make API request
                response = requests.post(
                    f"{API_BASE_URL}/research",
                    json={
                        "query": query,
                        "include_history": include_history
                    },
                    timeout=120  # 2 minute timeout
                )
                
                # Stage 2: Analyzing
                status_text.markdown(
                    "<p class='status-text'>🧠 Analyzing sources and extracting claims...</p>", 
                    unsafe_allow_html=True
                )
                progress_bar.progress(50)
                time.sleep(0.3)
                
                if response.status_code == 200:
                    # Stage 3: Writing
                    status_text.markdown(
                        "<p class='status-text'>✍️ Generating comprehensive report...</p>", 
                        unsafe_allow_html=True
                    )
                    progress_bar.progress(75)
                    time.sleep(0.3)
                    
                    result = response.json()
                    
                    # Stage 4: Complete
                    status_text.markdown(
                        "<p class='status-text'>✅ Research complete!</p>", 
                        unsafe_allow_html=True
                    )
                    progress_bar.progress(100)
                    time.sleep(0.5)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Store in session
                    st.session_state.current_report = result
                    st.session_state.research_history.insert(0, {
                        'query': query,
                        'timestamp': result['timestamp'],
                        'metadata': result['metadata']
                    })
                    
                    # Success message
                    st.success("✅ Research completed successfully!")
                    
                else:
                    st.error(f"❌ Error: {response.text}")
                    
            except requests.Timeout:
                st.error("⏱️ Request timed out. The research might be taking longer than expected. Please try again.")
            except requests.RequestException as e:
                st.error(f"🔌 Connection error: {str(e)}\n\nMake sure the API server is running.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

# ==================== DISPLAY CURRENT REPORT ====================

if st.session_state.current_report:
    st.markdown("---")
    
    # Metadata metrics
    st.subheader("📊 Report Metrics")
    metadata = st.session_state.current_report['metadata']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        quality = metadata.get('quality_score', 0)
        st.metric(
            "Quality Score", 
            f"{quality:.1%}",
            delta=None,
            help="Overall quality of the report based on completeness, structure, and evidence"
        )
    
    with col2:
        claims = metadata.get('claims_count', 0)
        st.metric(
            "Claims Found", 
            claims,
            help="Number of key claims extracted from sources"
        )
    
    with col3:
        sources = metadata.get('sources_count', 0)
        st.metric(
            "Sources", 
            sources,
            help="Number of unique sources cited"
        )
    
    with col4:
        exec_time = metadata.get('execution_time', 0)
        st.metric(
            "Time", 
            f"{exec_time:.1f}s",
            help="Total execution time"
        )
    
    st.markdown("---")
    
    # The Report
    st.subheader("📄 Research Report")
    
    # Display in a nice box
    st.markdown(
        f"<div class='report-box'>{st.session_state.current_report['report']}</div>",
        unsafe_allow_html=True
    )
    
    # Download button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.download_button(
            label="📥 Download Markdown",
            data=st.session_state.current_report['report'],
            file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            label="📥 Download Text",
            data=st.session_state.current_report['report'],
            file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Related Content
    with st.expander("🔗 Related Content from Memory"):
        try:
            semantic_results = requests.post(
                f"{API_BASE_URL}/memory/semantic-search",
                params={
                    "query": st.session_state.current_report['query'],
                    "search_type": "documents",
                    "limit": 3
                },
                timeout=10
            )
            
            if semantic_results.status_code == 200:
                results = semantic_results.json()['results']
                
                if results:
                    for i, result in enumerate(results, 1):
                        st.markdown(f"**{i}. {result['metadata'].get('query', 'N/A')}**")
                        st.markdown(f"*Similarity: {(1 - result.get('distance', 1)):.0%}*")
                        st.markdown(result['text'][:300] + "...")
                        st.markdown("---")
                else:
                    st.info("No related content found yet. Keep researching to build your knowledge base!")
        except:
            st.warning("Could not load related content")

# ==================== HISTORY VIEW ====================

if st.session_state.get('show_history', False):
    st.markdown("---")
    st.markdown("## 📚 Research History")
    
    try:
        history_response = requests.get(f"{API_BASE_URL}/history?limit=20", timeout=10)
        if history_response.status_code == 200:
            history = history_response.json()['history']
            
            if history:
                st.info(f"Found {len(history)} past queries")
                
                for item in history:
                    with st.expander(
                        f"🔍 {item['query']} - {format_timestamp(item['timestamp'])}"
                    ):
                        st.markdown(f"**Query ID:** {item['id']}")
                        st.markdown(f"**Timestamp:** {format_timestamp(item['timestamp'])}")
                        if item.get('quality_score'):
                            st.markdown(f"**Quality:** {item['quality_score']:.0%}")
                        
                        # Option to view full response if available
                        if st.button(f"View Full Report", key=f"view_{item['id']}"):
                            st.info("Full report viewing coming soon!")
            else:
                st.info("No history yet. Start researching to build your history!")
    except Exception as e:
        st.error(f"Could not load history: {str(e)}")
    
    if st.button("✖️ Close History"):
        st.session_state.show_history = False
        st.rerun()

# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>AI Research Assistant</strong> | INFO 7375 - Building Agentic Systems</p>
    <p>Powered by CrewAI, GPT-4, spaCy, and ChromaDB</p>
    <p><em>Built with ❤️ by Meet Patel</em></p>
</div>
""", unsafe_allow_html=True)