"""
API Client for Research Assistant Frontend
"""
import requests

API_BASE_URL = "http://localhost:8000"

def ask_backend(query: str) -> str:
    """
    Call the backend research endpoint
    
    Args:
        query: Research question
        
    Returns:
        Formatted research report
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "No response generated")
        else:
            return f"Error: API returned status {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The research is taking longer than expected."
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to backend. Make sure the API is running on port 8000."
    except Exception as e:
        return f"Error: {str(e)}"