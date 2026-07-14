from typing import List
from app.schemas.routing import RouteResponse

class HybridV0Adapter:
    ID = "hybrid"
    NAME = "Hybrid Router — Coming soon"

    def route(self, question: str, history: List[str] = None) -> RouteResponse:
        raise NotImplementedError("Hybrid Router is 'Coming soon'. HTTP 501 Not Implemented.")
