import os
import sys
import json

from google import genai
from google.genai import types

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config

try:
    from ai.schemas import DiagnosisResponse
except ImportError:
    DiagnosisResponse = None


class GeminiDiagnosisService:
    def __init__(self):
        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY
        )

        self.model_name = "gemini-3.5-flash-lite"

        self.prompt_template_path = getattr(
            Config,
            "PROMPT_FILE",
            os.path.join(
                parent_dir,
                "prompts",
                "network_diagnosis.txt"
            )
        )

        self._load_prompt_template()

    def _load_prompt_template(self):
        """Load the network diagnosis prompt template."""
        if os.path.exists(self.prompt_template_path):
            with open(
                self.prompt_template_path,
                "r",
                encoding="utf-8"
            ) as f:
                self.prompt_template = f.read()
        else:
            self.prompt_template = (
                "You are NetSage AI, an expert Cisco network "
                "troubleshooting assistant for Packet Tracer labs.\n\n"

                "### HISTORICAL CASE CONTEXT:\n"
                "{retrieved_context}\n\n"

                "### CURRENT INCIDENT:\n"
                "- Symptom: {symptom}\n"
                "- Topology Notes: {topology_note}\n"
                "- Show Commands Output: {show_outputs}\n\n"

                "Analyze the current incident independently. "
                "Use historical cases only as supporting evidence. "
                "Do not assume that a historical case has the same "
                "root cause as the current incident.\n\n"

                "Return strictly valid JSON with these keys:\n"
                "root_cause, confidence, evidence, next_command, fix_steps.\n\n"

                "- confidence must be exactly one of the words: \"High\", \"Medium\", or \"Low\". Do not use numbers or percentages.\n"
                "evidence must be a string.\n"
                "fix_steps must be a string."
            )

    def diagnose(
        self,
        symptom: str,
        topology_note: str,
        show_outputs: str,
        retrieved_context: list = None
    ) -> dict:
        """Send incident data and retrieved context to Gemini."""
        if retrieved_context is None:
            retrieved_context = []

        context_items = []
        for case in retrieved_context:
            case_id = case.get("case_id", "Unknown")
            case_symptom = case.get("symptom", "Not provided")
            concept = case.get("concept_tag", case.get("Concept_Tag", case.get("concept", case.get("category", "Not provided"))))
            severity = case.get("severity", "Not provided")

            context_items.append(
                f"- Case {case_id}: "
                f"Symptom: {case_symptom}; "
                f"Concept: {concept}; "
                f"Severity: {severity}"
            )

        context_str = "\n".join(context_items)
        if not context_str:
            context_str = "No similar historical cases found."

        try:
            prompt = self.prompt_template.format(
                retrieved_context=context_str,
                symptom=symptom,
                topology_note=topology_note or "None provided",
                show_outputs=show_outputs or "None provided"
            )
        except KeyError:
            prompt = (
                f"{self.prompt_template}\n\n"
                f"Historical Context:\n"
                f"{context_str}\n\n"
                f"Current Symptom:\n"
                f"{symptom}\n\n"
                f"Topology:\n"
                f"{topology_note or 'None provided'}\n\n"
                f"Show Command Output:\n"
                f"{show_outputs or 'None provided'}"
            )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            raw_text = (response.text or "").strip()
            if not raw_text:
                raise ValueError("Gemini returned an empty response.")

            raw_data = json.loads(raw_text)

            conf_val = str(raw_data.get("confidence", "High")).strip()
            if "%" in conf_val or any(char.isdigit() for char in conf_val):
                raw_data["confidence"] = "High"
            elif conf_val.capitalize() in ["High", "Medium", "Low"]:
                raw_data["confidence"] = conf_val.capitalize()
            else:
                raw_data["confidence"] = "Medium"

            primary_case = retrieved_context[0] if retrieved_context else {}
            raw_data["concept_tag"] = primary_case.get('concept_tag') or primary_case.get('Concept_Tag') or primary_case.get('concept') or primary_case.get('category') or "General Routing"
            raw_data["osi_layer"] = primary_case.get('osi_layer', 'Layer 3/4')

            if DiagnosisResponse:
                validated_response = DiagnosisResponse(**raw_data)
                return validated_response.model_dump()

            return raw_data

        except Exception as e:
            error_message = str(e)
            print(f"Gemini diagnosis error: {error_message}")

            fallback_concept = "General Routing"
            if retrieved_context:
                fallback_concept = retrieved_context[0].get('concept_tag') or retrieved_context[0].get('Concept_Tag') or retrieved_context[0].get('concept') or retrieved_context[0].get('category') or "General Routing"

            if DiagnosisResponse:
                fallback = DiagnosisResponse(
                    root_cause=f"AI Analysis Error: {error_message}",
                    confidence="Low",
                    evidence="Unable to connect to Gemini or parse its response.",
                    next_command="Check the Gemini API configuration and review terminal logs.",
                    fix_steps="1. Verify GEMINI_API_KEY. 2. Check internet connectivity. 3. Retry diagnosis."
                )
                data = fallback.model_dump()
                data["concept_tag"] = fallback_concept
                data["osi_layer"] = "Layer 3/4"
                return data

            return {
                "root_cause": f"Error generating AI diagnosis: {error_message}",
                "confidence": "Low",
                "evidence": "Unable to obtain a valid Gemini response.",
                "next_command": "show version",
                "fix_steps": "1. Verify Gemini API key. 2. Check internet. 3. Review logs.",
                "concept_tag": fallback_concept,
                "osi_layer": "Layer 3/4"
            }