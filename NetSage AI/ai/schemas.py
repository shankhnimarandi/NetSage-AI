from pydantic import BaseModel, Field

class DiagnosisResponse(BaseModel):
    root_cause: str = Field(description="Identified root cause of the network fault.")
    osi_layer: str = Field(default="Layer 3/4", description="Involved OSI layer (e.g., Layer 2, Layer 3/4).")
    concept_tag: str = Field(default="General Routing", description="Concept tag (e.g., VLAN, DHCP, ACL, NAT, DNS).")
    confidence: str = Field(description="Confidence level: High, Medium, or Low.")
    evidence: str = Field(description="Quotes or references from show-command outputs supporting the diagnosis.")
    next_command: str = Field(description="Next troubleshooting command to run.")
    fix_steps: str = Field(description="Step-by-step evidence-backed fix instructions.")