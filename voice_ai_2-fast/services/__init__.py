# services/__init__.py
"""
SIMPLIFIED: Core services for the Voice AI system without caller recognition
"""

from .session import create_optimized_session

__all__ = [
    'create_optimized_session'
]