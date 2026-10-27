"""
Backward compatibility bridge for GroqService -> GrokService.
Ensures existing imports continue functioning seamlessly.
"""
from services.grok_service import GrokService as _GrokService, grok_service as _grok_service

# Backward compatibility aliases
GroqService = _GrokService
groq_service = _grok_service

__all__ = ["GroqService", "groq_service"]
