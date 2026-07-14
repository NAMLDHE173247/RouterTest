import time
from typing import List
from app.schemas.routing import RouterDecision, RouterRuntime, RouteResponse
from app.qwen_service_client import QwenServiceClient

class QwenV0Adapter:
    ID = "qwen_v0"
    NAME = "Qwen Router V0 (GPU Service)"

    def __init__(self):
        self.client = QwenServiceClient()

    def route(self, question: str, history: List[str] = None) -> RouteResponse:
        try:
            res = self.client.route_question(question, history)
            
            decision_data = res.get("decision", {})
            
            decision = RouterDecision(
                primary_subject=decision_data.get("primary_subject", "unknown"),
                secondary_subjects=decision_data.get("secondary_subjects", []),
                intent=decision_data.get("intent", "unknown"),
                target_slm=decision_data.get("target_slm", "general_tutor"),
                confidence=float(decision_data.get("confidence", 0.0)),
                need_clarification=decision_data.get("need_clarification", False),
                reason=decision_data.get("reason", "")
            )
            
            qwen_runtime = res.get("runtime", {})
            remote_latency = qwen_runtime.get("latency_ms", 0.0)
            
            runtime = RouterRuntime(
                router_type="qwen_v0",
                source="Qwen GPU Service",
                latency_ms=round(remote_latency, 2), 
                parse_success=qwen_runtime.get("parse_success", True),
                input_tokens=qwen_runtime.get("input_tokens", 0),
                output_tokens=qwen_runtime.get("output_tokens", 0),
                model=qwen_runtime.get("model", "Qwen/Qwen2.5-7B-Instruct")
            )
            
            return RouteResponse(
                router_id=self.ID,
                router_name=self.NAME,
                decision=decision,
                runtime=runtime
            )
        except Exception as e:
            raise ValueError(f"Qwen Service Error: {str(e)}")
