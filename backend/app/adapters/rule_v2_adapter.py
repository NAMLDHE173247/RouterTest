import os
import time
from typing import List
from app.schemas.routing import RouterDecision, RouterRuntime, RouteResponse
from app.adapters.base import load_isolated_router

class RuleV2Adapter:
    ID = "rule_v2"
    NAME = "Rule-based Router V2"

    def __init__(self):
        v2_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Rule_based_Router/rule_based_router_v2/router_experiment/src"))
        self.route_fn = load_isolated_router(v2_path)

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
            runtime = RouterRuntime(
                router_type="rule_v2",
                source="Local Rule-based",
                latency_ms=round(latency_ms, 2), 
                parse_success=True,
                model="Regex/Heuristic"
            )
            return RouteResponse(
                router_id=self.ID,
                router_name=self.NAME,
                decision=decision,
                runtime=runtime
            )
        except Exception as e:
            raise e
