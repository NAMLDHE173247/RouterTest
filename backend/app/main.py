from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import routing, health, evaluations, datasets

app = FastAPI(
    title="RouterTest API",
    description="API for Rule-based Router Test and Evaluation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(routing.router, prefix="/api/v1", tags=["Routing"])
app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["Evaluations"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])
# app.include_router(comparisons.router, prefix="/api/v1", tags=["Comparisons"])
# app.include_router(evaluations.router, prefix="/api/v1", tags=["Evaluations"])
# app.include_router(datasets.router, prefix="/api/v1", tags=["Datasets"])
