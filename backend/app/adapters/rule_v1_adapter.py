import os
import time
from typing import List
from app.schemas.routing import RouterDecision, RouterRuntime, RouteResponse
from app.adapters.base import load_isolated_router

class RuleV1Adapter:
    ID = "rule_v1"
    NAME = "Rule-based Router V1"

    def __init__(self):
        v1_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Rule_based_Router/rule_based_router_v1/router_experiment/src"))
        self.route_fn = load_isolated_router(v1_path)

    def route(self, question: str, history: List[str] = None) -> RouteResponse:
        history = history or []
        start_time = time.time()
        try:
            prediction = self.route_fn(question=question, history=history)
            latency_ms = (time.time() - start_time) * 1000
            
            decision = RouterDecision(
                primary_subject=prediction.get("primary_subject", "unknown"),
                secondary_subjects=prediction.get("secondary_subjects", []),
                intent=prediction.get("intent", "unknown"),
                target_slm=prediction.get("target_slm", "general_tutor"),
                confidence=float(prediction.get("confidence", 0.0)),
                need_clarification=prediction.get("need_clarification", False),
                reason=prediction.get("reason", "")
            )
            runtime = RouterRuntime(latency_ms=round(latency_ms, 2), success=True)
            return RouteResponse(
                router_id=self.ID,
                router_name=self.NAME,
                decision=decision,
                runtime=runtime
            )
        except Exception as e:
            raise e
