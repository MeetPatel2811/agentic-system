"""
Custom Exceptions for Research Assistant
"""

class ResearchAssistantError(Exception):
    def __init__(self, message: str, error_code: str = "UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"

class CrewError(ResearchAssistantError):
    def __init__(self, message: str):
        super().__init__(message, "CREW_ERROR")

class CrewNotInitializedError(CrewError):
    def __init__(self):
        super().__init__("Crew system is not initialized")

class ToolError(ResearchAssistantError):
    def __init__(self, message: str, tool_name: str = "unknown"):
        self.tool_name = tool_name
        super().__init__(message, "TOOL_ERROR")

class MemoryError(ResearchAssistantError):
    def __init__(self, message: str):
        super().__init__(message, "MEMORY_ERROR")

class ValidationError(ResearchAssistantError):
    def __init__(self, message: str, field: str = "unknown"):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class InvalidQueryError(ValidationError):
    def __init__(self, message: str):
        super().__init__(f"Invalid query: {message}", "query")

def get_error_response(error: Exception) -> dict:
    if isinstance(error, ResearchAssistantError):
        return {
            "error": error.message,
            "error_code": error.error_code,
            "error_type": error.__class__.__name__
        }
    else:
        return {
            "error": str(error),
            "error_code": "UNKNOWN",
            "error_type": error.__class__.__name__
        }