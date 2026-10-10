import os
from typing import Optional
from nemoguardrails import RailsConfig, LLMRails

class GuardrailsManager:
    """
    Manager class to handle all Enterprise Guardrails.
    Combines NeMo Guardrails (for intent/persona) and
    Custom Filters (for PII/Data Leakage).
    """
    def __init__(self, config_path: str = "app/guardrails/config"):
        # Load NeMo Guardrails configuration
        self.config = RailsConfig.from_path(config_path)
        self.rails = LLMRails(self.config)

        # PII Patterns (Simplified for this implementation)
        # In a production environment, you might use a library like 'presidio-analyzer'
        self.pii_patterns = {
            "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "phone": r"\+?\d{1,3}?[-. ]?\(?\d{1,3}?\)?[-. ]?\d{3,4}[-. ]?\d{4}",
            "api_key": r"(?:sk-|key-|api-)[a-zA-Z0-9]{20,}"
        }

    def _scan_for_pii(self, text: str) -> bool:
        """
        Scans the text for PII patterns.
        Returns True if PII is found, False otherwise.
        """
        import re
        for label, pattern in self.pii_patterns.items():
            if re.search(pattern, text):
                return True
        return False

    async def guarded_chat(self, query: str) -> str:
        """
        The main entry point for all user queries.
        Flow: User Query -> NeMo Flow (Intent) -> LLM -> PII Scan -> Response
        """
        try:
            # 1. Run through NeMo Guardrails
            # This handles Role Violation, Non-Advice, and Off-Topic intents
            response = await self.rails.generate_async(query)

            # 2. Post-Processing: PII Scan
            # Even if the flow is correct, we must ensure the LLM didn't leak data
            if self._scan_for_pii(response):
                return "I'm sorry, but the generated response contains sensitive information and cannot be displayed for security reasons."

            return response

        except Exception as e:
            # Fallback in case of guardrail failure
            print(f"Guardrail Error: {e}")
            return "I'm sorry, I'm having trouble processing that request. Please try again."

# Singleton instance for the application
guardrails_manager = GuardrailsManager()
