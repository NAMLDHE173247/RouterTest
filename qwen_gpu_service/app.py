import os
import time
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from llm_router import QwenRouter
from schema import RouterDecision

# --- Schemas ---
class RouteRequest(BaseModel):
    question: str
    history: Optional[List[Any]] = []

class BatchRouteRequest(BaseModel):
    items: List[RouteRequest]

# --- App State ---
# model_loaded, startup_error, router, model_name

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.model_loaded = False
    app.state.startup_error = None
    app.state.router = None
    app.state.model_name = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
    
    try:
        print(f"Loading model: {app.state.model_name}...")
        router = QwenRouter(model_name=app.state.model_name)
        print("Warming up...")
        router.warmup()
        app.state.router = router
        app.state.model_loaded = True
        print("Model loaded successfully.")
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        app.state.startup_error = error_msg
        print(f"Failed to load model: {error_msg}")
        
    yield
    # Shutdown
    print("Shutting down Qwen GPU Service.")

app = FastAPI(title="Qwen GPU Service", lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/model/status")
def model_status():
    return {
        "model_loaded": app.state.model_loaded,
        "model_name": app.state.model_name,
        "startup_error": app.state.startup_error
    }

@app.post("/route")
def route(req: RouteRequest):
    if not app.state.model_loaded:
        raise HTTPException(status_code=503, detail=f"Model not loaded. Error: {app.state.startup_error}")
    
    router: QwenRouter = app.state.router
    try:
        # router.route returns:
        # { "prediction": dict, "raw_response": str, "model": str, "latency_ms": float, ... }
        result = router.route(question=req.question, history=req.history)
        
        decision = result.pop("prediction")
        raw_response = result.pop("raw_response", None)
        
        return {
            "router": "qwen_v0",
            "decision": decision,
            "runtime": result,
            "raw_response": raw_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-route")
def batch_route(req: BatchRouteRequest):
    if not app.state.model_loaded:
        raise HTTPException(status_code=503, detail=f"Model not loaded. Error: {app.state.startup_error}")
    
    router: QwenRouter = app.state.router
    responses = []
    
    for item in req.items:
        try:
            result = router.route(question=item.question, history=item.history)
            decision = result.pop("prediction")
            raw_response = result.pop("raw_response", None)
            responses.append({
                "router": "qwen_v0",
                "decision": decision,
                "runtime": result,
                "raw_response": raw_response,
                "error": None
            })
        except Exception as e:
            responses.append({
                "router": "qwen_v0",
                "decision": None,
                "runtime": None,
                "raw_response": None,
                "error": str(e)
            })
            
    return responses
