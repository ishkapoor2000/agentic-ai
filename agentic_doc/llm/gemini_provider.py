"""
Google Gemini AI provider (Free Tier Available).
"""
import os
from typing import Optional
from .providers import ModelProvider

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiProvider(ModelProvider):
    """Google Gemini provider with free tier support."""
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini provider.
        
        Args:
            model: Model name (gemini-2.5-flash, gemini-2.0-flash, etc.)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )
        
        # Configure API
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required.\n"
                "Get your free API key from: https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=api_key)
        
        # Store model name as string for cache
        self.model_name = model
        
        # Create model instance
        self.model = genai.GenerativeModel(model)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate documentation using Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
            
        Returns:
            Generated text
        """
        from agentic_doc.llm.api_tracker import get_tracker
        
        # Combine system and user prompts
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self.model.generate_content(full_prompt)
            
            # Track API request
            get_tracker().increment("gemini")
            
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
