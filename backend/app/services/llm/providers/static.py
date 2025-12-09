"""
Static knowledge base provider.

Provides pre-written explanations from a static knowledge base
as a fallback when LLM providers are not available.
"""

from typing import Optional

from app.core.logging import get_llm_logger
from app.services.llm.models import (
    ExplanationRequest,
    ExplanationResponse,
    ExplanationType,
    LLMProvider,
)
from .base import BaseLLMProvider

logger = get_llm_logger()


# Static knowledge base containing pre-written explanations
# for common vulnerabilities and security concepts
KNOWLEDGE_BASE: dict[str, dict[str, str]] = {
    # Vulnerability explanations
    "default_credentials": {
        "beginner": """**Default Credentials** means the device is using the username and password it came with from the factory. Think of it like leaving your front door key under the welcome mat - everyone knows where to look!

**Why it's risky:** Attackers know the default passwords for thousands of devices. They can simply try common combinations like "admin/admin" or "admin/password" to break in.

**Severity: HIGH** - This is one of the easiest vulnerabilities to exploit and should be fixed immediately.

**How to fix:** Change the default username and password to something unique and strong. Use a combination of letters, numbers, and symbols.""",

        "intermediate": """**Default Credentials** is a configuration vulnerability where a device or service still uses manufacturer-supplied authentication credentials.

**Risk Assessment:**
- Attack Vector: Network-accessible
- Complexity: Low (credentials are publicly documented)
- Impact: Complete compromise of affected device

**Technical Details:**
Many IoT devices, routers, and network equipment ship with documented default credentials. Attackers use automated scanners to identify devices and test known credential pairs.

**Remediation:**
1. Change default passwords during initial setup
2. Use strong, unique passwords (12+ characters)
3. Implement multi-factor authentication where available
4. Disable default accounts if possible""",

        "advanced": """**Default Credentials (CWE-1393)**

A critical authentication bypass vulnerability resulting from unchanged factory-default credentials. This vulnerability is frequently targeted in automated botnets like Mirai.

**CVSS Considerations:**
- Attack Vector: Network (AV:N)
- Attack Complexity: Low (AC:L)
- Privileges Required: None (PR:N)
- User Interaction: None (UI:N)
- Scope: Unchanged (S:U)
- Impact: High across CIA triad for device compromise

**Exploitation:**
Attackers leverage credential dictionaries containing known default username/password combinations. Tools like Hydra and Medusa automate credential stuffing attacks.

**Defense in Depth:**
1. Mandatory password change on first login
2. Account lockout policies
3. Network segmentation
4. Monitoring for authentication anomalies
5. Regular credential audits"""
    },

    "open_telnet": {
        "beginner": """**Open Telnet Service** means your device has an old-style remote access service running that sends everything in plain text - like sending a postcard instead of a sealed letter!

**Why it's risky:** Anyone watching the network can see your username, password, and everything you type. It's like having a conversation in public where everyone can hear.

**Severity: CRITICAL** - Telnet should almost never be used on modern networks.

**How to fix:** Disable Telnet and use SSH (Secure Shell) instead. SSH encrypts all your communications.""",

        "intermediate": """**Open Telnet Service (Port 23)** exposes a legacy remote administration protocol that transmits data without encryption.

**Risk Assessment:**
- All traffic including credentials transmitted in plaintext
- Susceptible to man-in-the-middle attacks
- Often indicates outdated systems or poor security practices

**Technical Impact:**
- Credential theft via network sniffing
- Session hijacking
- Complete system compromise

**Remediation:**
1. Disable Telnet service immediately
2. Enable SSH (port 22) for remote access
3. If Telnet is required, isolate to management VLAN
4. Use VPN for remote administration""",
    },

    "unencrypted_http": {
        "beginner": """**Unencrypted HTTP** means the website or service doesn't protect your information while it travels across the internet. It's like sending a postcard - anyone along the way can read it!

**Why it's risky:** Attackers can see and steal sensitive information like passwords, credit card numbers, or personal data. They can also change what you see on the website.

**Severity: MEDIUM to HIGH** - Depends on what data is transmitted.

**How to fix:** Enable HTTPS by installing an SSL/TLS certificate. Many providers offer free certificates through Let's Encrypt.""",

        "intermediate": """**Unencrypted HTTP (Port 80)** exposes web traffic to interception and manipulation.

**Risk Assessment:**
- Data transmitted in plaintext
- Session cookies can be stolen
- Content can be modified in transit (MITM)

**Technical Impact:**
- Credential theft
- Session hijacking
- Content injection (malvertising, cryptomining)

**Remediation:**
1. Obtain SSL/TLS certificate (Let's Encrypt provides free certs)
2. Configure HTTPS (port 443)
3. Enable HTTP Strict Transport Security (HSTS)
4. Redirect all HTTP traffic to HTTPS
5. Update internal links and resources""",
    },

    "open_smb": {
        "beginner": """**Open SMB Service** means file sharing is exposed on your network. SMB (Server Message Block) lets computers share files, but if it's open to the wrong people, it's like leaving your filing cabinet unlocked in a public space!

**Why it's risky:** Attackers can access your shared files, spread malware (like ransomware), or use it to move around your network.

**Severity: HIGH** - SMB vulnerabilities have been used in major attacks like WannaCry ransomware.

**How to fix:** Block SMB at your firewall, disable SMBv1, and ensure file shares require authentication.""",
    },

    "outdated_firmware": {
        "beginner": """**Outdated Firmware** means your device is running old software that may have known security holes. It's like having a lock on your door that burglars have already learned to pick!

**Why it's risky:** Attackers often know exactly how to break into devices with outdated software because the weaknesses have been publicly documented.

**Severity: VARIES** - Depends on what vulnerabilities exist in the old version.

**How to fix:** Check the manufacturer's website for updates and install the latest firmware. Set up automatic updates if available.""",
    },

    # Security concepts
    "encryption": {
        "beginner": """**Encryption** is like putting your message in a locked box that only the intended recipient has the key to open. Even if someone intercepts the box, they can't read what's inside!

**Why it matters:** Encryption protects your sensitive information (passwords, messages, financial data) from being read by attackers.

**Common examples:**
- HTTPS (the padlock in your browser)
- Wi-Fi passwords (WPA2/WPA3)
- Encrypted messaging apps

**Remember:** Always look for the padlock icon when entering sensitive information online!""",
    },

    "firewall": {
        "beginner": """**Firewall** is like a security guard for your network. It checks all incoming and outgoing traffic and decides what's allowed through based on rules you set.

**Why it matters:** Firewalls block unauthorized access attempts and can prevent malware from communicating with attackers.

**Types of firewalls:**
- Network firewalls (protect your whole network)
- Host firewalls (protect individual devices - like Windows Firewall)

**Best practice:** Enable your firewall and only allow traffic that's necessary for your needs.""",
    },
}


class StaticKnowledgeProvider(BaseLLMProvider):
    """
    Static knowledge base provider.

    Uses pre-written explanations as a fallback when LLM providers
    are not available. Ensures users always get helpful information
    even without network connectivity or LLM services.
    """

    def __init__(self):
        """Initialize the static knowledge provider."""
        logger.info("StaticKnowledgeProvider initialized")

    @property
    def provider_type(self) -> LLMProvider:
        """Return the provider type."""
        return LLMProvider.STATIC

    async def is_available(self) -> bool:
        """
        Static provider is always available.

        Returns:
            Always True
        """
        return True

    async def generate_explanation(
        self,
        request: ExplanationRequest,
    ) -> Optional[ExplanationResponse]:
        """
        Look up an explanation from the static knowledge base.

        Args:
            request: The explanation request

        Returns:
            ExplanationResponse if topic found, generic response otherwise
        """
        logger.info(
            "Looking up static explanation",
            extra={
                "topic": request.topic,
                "type": request.explanation_type.value,
            }
        )

        # Normalize topic for lookup
        topic_key = request.topic.lower().replace(" ", "_").replace("-", "_")

        # Try to find in knowledge base
        if topic_key in KNOWLEDGE_BASE:
            topic_data = KNOWLEDGE_BASE[topic_key]
            difficulty = request.difficulty_level

            # Get explanation for requested difficulty, fallback to beginner
            explanation = topic_data.get(difficulty) or topic_data.get("beginner")

            if explanation:
                logger.info(
                    "Found static explanation",
                    extra={"topic": topic_key, "difficulty": difficulty}
                )

                return ExplanationResponse(
                    explanation=explanation,
                    provider=self.provider_type,
                    topic=request.topic,
                    cached=False,
                    difficulty_level=request.difficulty_level,
                    related_topics=self._extract_related_topics(topic_key),
                )

        # Generate a generic response if topic not found
        logger.info(
            "Topic not in knowledge base, generating generic response",
            extra={"topic": request.topic}
        )

        generic_explanation = self._generate_generic_explanation(request)

        return ExplanationResponse(
            explanation=generic_explanation,
            provider=self.provider_type,
            topic=request.topic,
            cached=False,
            difficulty_level=request.difficulty_level,
            related_topics=["network_security", "best_practices"],
        )

    def _generate_generic_explanation(self, request: ExplanationRequest) -> str:
        """
        Generate a generic explanation when topic is not in knowledge base.

        Args:
            request: The explanation request

        Returns:
            A generic but helpful explanation
        """
        topic = request.topic

        if request.explanation_type == ExplanationType.VULNERABILITY:
            return f"""**{topic}** is a security finding that was detected on your network.

While we don't have specific details about this particular issue in our knowledge base, here are some general recommendations:

1. **Research the issue** - Search online for "{topic}" to learn more about what it means
2. **Assess the risk** - Consider what data or systems could be affected
3. **Consult documentation** - Check the device or software manufacturer's security guidelines
4. **Seek expert advice** - For critical systems, consider consulting a cybersecurity professional

For more information, you can search security databases like:
- NIST National Vulnerability Database (NVD)
- MITRE CVE database
- Manufacturer security advisories"""

        elif request.explanation_type == ExplanationType.REMEDIATION:
            return f"""**How to address: {topic}**

General remediation steps:

1. **Identify the scope** - Determine which systems are affected
2. **Check for updates** - Look for security patches or firmware updates
3. **Review configuration** - Ensure security settings are properly configured
4. **Apply least privilege** - Limit access to only what's necessary
5. **Monitor for issues** - Watch for unusual activity after making changes

**Important:** Always test changes in a non-production environment first if possible."""

        elif request.explanation_type == ExplanationType.SERVICE:
            return f"""**{topic}** appears to be a network service.

General considerations for network services:

1. **Purpose** - Understand why this service is running
2. **Necessity** - Disable the service if it's not needed
3. **Access control** - Limit who can access the service
4. **Updates** - Keep the service software up to date
5. **Monitoring** - Log and monitor service activity

If this service is unfamiliar, consider researching its purpose and associated security risks."""

        else:
            return f"""**{topic}**

This is a cybersecurity-related topic. Here are some general learning resources:

1. **NIST Cybersecurity Framework** - Industry-standard security guidelines
2. **OWASP** - Web application security resources
3. **SANS Reading Room** - In-depth security whitepapers
4. **Cybrary** - Free cybersecurity training courses

For hands-on learning, consider setting up a home lab to practice security concepts safely."""
