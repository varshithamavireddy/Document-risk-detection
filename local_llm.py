import re
import time


class GroqClient:
    def __init__(self, api_key):
        from groq import Groq
        self.client = Groq(api_key=api_key)

    def generate(self, model, system, prompt, json_mode=False):
        options = {"model": model, "temperature": 0.1, "max_completion_tokens": 2048, "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]}
        if json_mode:
            options["reasoning_effort"] = "low"
            options["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "document_risk_assessment",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "risks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "title": {"type": "string"},
                                        "category": {"type": "string"},
                                        "description": {"type": "string"},
                                        "evidence": {"type": "string"},
                                        "impact": {"type": "integer", "minimum": 1, "maximum": 5},
                                        "likelihood": {"type": "integer", "minimum": 1, "maximum": 5},
                                        "control_gap": {"type": "integer", "minimum": 1, "maximum": 5},
                                        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                                        "mitigations": {"type": "array", "items": {"type": "string"}},
                                    },
                                    "required": ["title", "category", "description", "evidence", "impact", "likelihood", "control_gap", "confidence", "mitigations"],
                                },
                            }
                        },
                        "required": ["risks"],
                    },
                },
            }
        for attempt in range(5):
            try:
                result = self.client.chat.completions.create(**options)
                return result.choices[0].message.content or ""
            except Exception as exc:
                message = str(exc)
                upper = message.upper()
                if attempt == 4 or not ("TPM" in upper or "TOKENS PER MINUTE" in upper):
                    raise
                match = re.search(r"try again in\s+([\d.]+)\s*(ms|milliseconds|s|seconds)", message, re.IGNORECASE)
                if match:
                    delay = float(match.group(1))
                    if match.group(2).lower() in {"ms", "milliseconds"}:
                        delay /= 1000
                else:
                    delay = 1.5 * (attempt + 1)
                if delay > 30:
                    raise
                time.sleep(max(0.5, delay))
