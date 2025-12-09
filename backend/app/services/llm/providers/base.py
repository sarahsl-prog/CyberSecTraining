"""
Base LLM provider interface.

Defines the abstract interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.services.llm.models import (
    ExplanationRequest,
    ExplanationResponse,
    LLMProvider,
)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers (Ollama, Hosted API, Static) must implement this interface.
    This allows the main LLM service to switch between providers seamlessly.
    """

    @property
    @abstractmethod
    def provider_type(self) -> LLMProvider:
        """Return the provider type identifier."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider is currently available.

        Returns:
            True if the provider can accept requests, False otherwise
        """
        pass

    @abstractmethod
    async def generate_explanation(
        self,
        request: ExplanationRequest,
    ) -> Optional[ExplanationResponse]:
        """
        Generate an explanation for the given request.

        Args:
            request: The explanation request containing topic and context

        Returns:
            ExplanationResponse if successful, None if generation failed
        """
        pass

    def _build_prompt(self, request: ExplanationRequest) -> str:
        """
        Build a prompt for the LLM based on the request type.

        Args:
            request: The explanation request

        Returns:
            A formatted prompt string for the LLM
        """
        difficulty_context = {
            "beginner": "Explain in simple terms suitable for someone new to cybersecurity. Avoid jargon and use everyday analogies.",
            "intermediate": "Explain for someone with basic technical knowledge. Include relevant technical terms with brief explanations.",
            "advanced": "Provide a detailed technical explanation suitable for IT professionals.",
        }

        base_context = difficulty_context.get(
            request.difficulty_level,
            difficulty_context["beginner"]
        )

        prompts = {
            "vulnerability": f"""You are a cybersecurity educator. {base_context}

Explain what the "{request.topic}" vulnerability is:
1. What it means in simple terms
2. Why it's a security risk
3. What attackers could potentially do if they found this
4. How serious it is (rate: Low/Medium/High/Critical)

{f"Additional context: {request.context}" if request.context else ""}

Keep the explanation concise (2-3 paragraphs) and educational.""",

            "remediation": f"""You are a cybersecurity educator. {base_context}

Explain how to fix the "{request.topic}" security issue:
1. Step-by-step remediation instructions
2. Why each step is important
3. How to verify the fix worked
4. Best practices to prevent this in the future

{f"Additional context: {request.context}" if request.context else ""}

Keep instructions clear and actionable.""",

            "concept": f"""You are a cybersecurity educator. {base_context}

Explain the concept of "{request.topic}":
1. What it is and why it matters
2. How it relates to network security
3. Real-world examples or analogies
4. Key points to remember

{f"Additional context: {request.context}" if request.context else ""}

Keep the explanation educational and engaging.""",

            "service": f"""You are a cybersecurity educator. {base_context}

Explain the "{request.topic}" network service:
1. What this service does
2. Common ports it uses
3. Potential security concerns
4. Whether it should typically be exposed to the internet

{f"Additional context: {request.context}" if request.context else ""}

Focus on security implications.""",

            "risk": f"""You are a cybersecurity educator. {base_context}

Explain the security risks of "{request.topic}":
1. What makes this risky
2. Potential attack scenarios
3. Impact if exploited
4. Risk mitigation strategies

{f"Additional context: {request.context}" if request.context else ""}

Be specific about real-world implications.""",
        }

        return prompts.get(
            request.explanation_type.value,
            prompts["concept"]
        )

    def _extract_related_topics(self, topic: str) -> list[str]:
        """
        Extract related topics for further learning.

        Args:
            topic: The main topic

        Returns:
            List of related topic suggestions
        """
        # Topic relationships for common vulnerabilities and concepts
        topic_relations = {
            "default_credentials": ["password_security", "authentication", "brute_force"],
            "open_telnet": ["ssh", "encryption", "secure_protocols"],
            "open_ftp": ["sftp", "file_transfer", "encryption"],
            "open_snmp": ["network_monitoring", "authentication", "protocol_security"],
            "unencrypted_http": ["https", "ssl_tls", "encryption"],
            "upnp_enabled": ["port_forwarding", "network_segmentation", "firewall"],
            "open_smb": ["file_sharing", "ransomware", "network_segmentation"],
            "open_database": ["sql_injection", "authentication", "network_segmentation"],
            "open_rdp": ["remote_access", "authentication", "vpn"],
            "open_vnc": ["remote_access", "authentication", "encryption"],
            "weak_wifi": ["wpa3", "encryption", "wireless_security"],
            "outdated_firmware": ["patch_management", "vulnerability_scanning", "updates"],
        }

        return topic_relations.get(topic.lower(), ["network_security", "best_practices"])
