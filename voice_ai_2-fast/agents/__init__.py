# agents/__init__.py - FIXED FOR INTELLIGENT SYSTEM
"""
FIXED: Agent modules for the Intelligent Voice AI system
Uses LLM brain with RAG pricing instead of separate specialist routing
"""

# Import both for backwards compatibility during transition
try:
    from .dispatcher import IntelligentDispatcherAgent
    # Also make it available as MainDispatcherAgent for any remaining references
    MainDispatcherAgent = IntelligentDispatcherAgent
except ImportError:
    # Fallback - try importing the old name if new one doesn't exist
    try:
        from .dispatcher import MainDispatcherAgent
        IntelligentDispatcherAgent = MainDispatcherAgent
    except ImportError:
        raise ImportError("Could not import dispatcher agent")

__all__ = [
    'IntelligentDispatcherAgent',
    'MainDispatcherAgent'  # Keep for compatibility
]