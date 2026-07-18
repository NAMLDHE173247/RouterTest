"""Prompt and model configuration for LLM Router V0."""

from typing import Dict, List


PROMPT_VERSION = "llm-router-v0.1"
TEMPERATURE = 0
MAX_OUTPUT_TOKENS = 300

MODEL_CONFIGS: Dict[str, Dict[str, str]] = {
    "llm_deepseek_v0": {
        "name": "LLM Router DeepSeek V0",
        "model": "deepseek/deepseek-chat",
    },
    "llm_gemini_v0": {
        "name": "LLM Router Gemini V0",
        "model": "google/gemini-2.0-flash-001",
    },
    "llm_openai_v0": {
        "name": "LLM Router OpenAI V0",
        "model": "openai/gpt-4o-mini",
    },
}

SYSTEM_PROMPT = """You are LLM Router V0. Classify routing only; never solve the user's problem and never write a final educational answer.

Return exactly one JSON object with only these fields:
primary_subject, secondary_subjects, intent, target_slm, confidence, need_clarification, reason.

Allowed primary_subject: math, physics, chemistry, unknown.
Allowed secondary_subjects: math, physics, chemistry. Do not repeat primary_subject and do not use unknown.
Allowed intent: solve_problem, explain_concept, give_hint, check_answer, diagnose_error, ask_follow_up, unknown.
Allowed target_slm: math_slm, physics_slm, chemistry_slm, general_tutor, ask_clarification.
Confidence must be a number from 0 to 1. Reason must not be empty.

Choose the subject that owns the substance of the problem, not merely the presence of arithmetic.
Free fall, velocity, acceleration, force, electricity and waves are physics. Mol, pH, reactions, concentration, acids and bases are chemistry. Derivatives, integrals, functions, geometry and probability as pure mathematics are math.
Map math to math_slm, physics to physics_slm, chemistry to chemistry_slm. Map clearly out-of-scope questions to general_tutor. Map missing or indeterminate routing information to ask_clarification.

Use history for references such as “vậy thì”, “bước tiếp theo”, “câu trên”, “phần đó”, “tại sao chỗ này”.
Current-question subject evidence wins over history. If a history-dependent question lacks enough context, use unknown, ask_clarification and need_clarification=true.
Use diagnose_error before check_answer, then give_hint, explain_concept, solve_problem, ask_follow_up, unknown according to the user's intent.
"""


def build_messages(question: str, history: List[str]) -> List[Dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend({"role": "user", "content": item} for item in history)
    messages.append({"role": "user", "content": question})
    return messages


def json_schema_format() -> Dict[str, object]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "router_decision",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "primary_subject", "secondary_subjects", "intent", "target_slm",
                    "confidence", "need_clarification", "reason",
                ],
                "properties": {
                    "primary_subject": {"type": "string", "enum": ["math", "physics", "chemistry", "unknown"]},
                    "secondary_subjects": {"type": "array", "items": {"type": "string", "enum": ["math", "physics", "chemistry"]}},
                    "intent": {"type": "string", "enum": ["solve_problem", "explain_concept", "give_hint", "check_answer", "diagnose_error", "ask_follow_up", "unknown"]},
                    "target_slm": {"type": "string", "enum": ["math_slm", "physics_slm", "chemistry_slm", "general_tutor", "ask_clarification"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "need_clarification": {"type": "boolean"},
                    "reason": {"type": "string", "minLength": 1},
                },
            },
        },
    }
