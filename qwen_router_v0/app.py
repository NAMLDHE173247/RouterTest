import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Optional unsloth import
USE_UNSLOTH = os.environ.get("USE_UNSLOTH", "false").lower() == "true"
if USE_UNSLOTH:
    try:
        import unsloth
        # We don't strictly need to do anything with it here, 
        # just ensuring it doesn't crash the app if false.
    except ImportError:
        pass

from llm_router import get_router, RouterGenerationError

class RouteRequest(BaseModel):
    question: str
    history: List[str] = []
    max_retries: int = 2

class BatchRouteRequest(BaseModel):
    questions: List[str]
    history: List[str] = []
    max_retries: int = 2

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo model
    app.state.model_loaded = False
    app.state.startup_error = None
    app.state.router = None
    
    try:
        router = get_router()
        # Optional: warmup can be done here if needed
        # router.warmup()
        app.state.router = router
        app.state.model_loaded = True
        print("Model loaded successfully.")
    except Exception as e:
        app.state.startup_error = str(e)
        print(f"Failed to load model: {e}")
        
    yield
    # Cleanup nếu cần
    pass

app = FastAPI(
    title="Qwen Router GPU Service",
    description="FastAPI service cho Qwen Router V0",
    lifespan=lifespan
)

# Cấu hình CORS
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "qwen-router-gpu-service",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    response = {
        "status": "ok" if app.state.model_loaded else "error",
        "model_loaded": app.state.model_loaded
    }
    
    if not app.state.model_loaded:
        response["startup_error"] = app.state.startup_error
    else:
        response["device"] = str(app.state.router.model.device)
        response["model_name"] = app.state.router.model_name
        
    return response

@app.get("/model/status")
async def model_status():
    import torch
    cuda_available = torch.cuda.is_available()
    response = {
        "cuda_available": cuda_available,
        "model_loaded": app.state.model_loaded
    }
    
    if app.state.model_loaded:
        response["quantization"] = "4-bit"
        response["device"] = str(app.state.router.model.device)
    else:
        response["startup_error"] = app.state.startup_error
        
    return response

@app.post("/route")
async def route_question(req: RouteRequest):
    if not app.state.model_loaded:
        raise HTTPException(
            status_code=503, 
            detail=f"Service reachable but model is not loaded. Error: {app.state.startup_error}"
        )
        
    try:
        result = app.state.router.route(
            question=req.question,
            history=req.history,
            max_retries=req.max_retries
        )
        
        # Format lại output theo schema mong muốn
        return {
            "router": "qwen_router_v0",
            "decision": result["prediction"],
            "runtime": {
                "latency_ms": result["latency_ms"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "retries": result["retries"],
                "parse_success": result["parse_success"],
                "model": result["model"]
            },
            "raw_response": result["raw_response"]
        }
    except RouterGenerationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-route")
async def batch_route(req: BatchRouteRequest):
    if not app.state.model_loaded:
        raise HTTPException(
            status_code=503, 
            detail=f"Service reachable but model is not loaded. Error: {app.state.startup_error}"
        )
        
    results = []
    for q in req.questions:
        try:
            res = app.state.router.route(
                question=q,
                history=req.history,
                max_retries=req.max_retries
            )
            results.append({
                "question": q,
                "status": "success",
                "router": "qwen_router_v0",
                "decision": res["prediction"],
                "runtime": {
                    "latency_ms": res["latency_ms"],
                    "input_tokens": res["input_tokens"],
                    "output_tokens": res["output_tokens"],
                    "retries": res["retries"],
                    "parse_success": res["parse_success"],
                    "model": res["model"]
                }
            })
        except Exception as e:
            results.append({
                "question": q,
                "status": "error",
                "error": str(e)
            })
            
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
