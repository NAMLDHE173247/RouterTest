"""Backward-compatible import for the high-level routing facade."""

from app.services.routing.routing_service import RoutingService, routing_service

__all__ = ["RoutingService", "routing_service"]
