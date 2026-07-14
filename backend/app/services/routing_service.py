from app.adapters.rule_v0_adapter import RuleV0Adapter
from app.adapters.rule_v1_adapter import RuleV1Adapter
from app.adapters.rule_v2_adapter import RuleV2Adapter
from app.adapters.qwen_v0_adapter import QwenV0Adapter
from app.adapters.hybrid_v0_adapter import HybridV0Adapter
from app.schemas.routing import RouteRequest, RouteResponse

class RoutingService:
    def __init__(self):
        self.adapters = {
            "rule_v0": RuleV0Adapter(),
            "rule_v1": RuleV1Adapter(),
            "rule_v2": RuleV2Adapter(),
            "qwen_v0": QwenV0Adapter(),
            "hybrid": HybridV0Adapter()
        }
    
    def get_available_routers(self):
        return [
            {"id": adapter.ID, "name": adapter.NAME, "status": "ready"}
            for adapter in self.adapters.values()
        ]
        
    def get_available_router_ids(self):
        return list(self.adapters.keys())

    def route(self, req: RouteRequest) -> RouteResponse:
        adapter = self.adapters.get(req.router_id)
        if not adapter:
            raise ValueError(f"Router {req.router_id} not found")
        return adapter.route(question=req.question, history=req.history)

    def compare_routers(self, router_ids: list[str], question: str, history: list[str] = None):
        results = []
        for rid in router_ids:
            adapter = self.adapters.get(rid)
            if not adapter:
                results.append({"router_id": rid, "error": "Router not found"})
                continue
            
            try:
                res = adapter.route(question=question, history=history)
                results.append({
                    "router_id": rid,
                    "response": res
                })
            except Exception as e:
                results.append({"router_id": rid, "error": str(e)})
        return results

routing_service = RoutingService()
