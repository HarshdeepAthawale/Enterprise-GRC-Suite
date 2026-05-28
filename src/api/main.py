from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, frameworks, controls, evidence, dashboard, risk, collectors

app = FastAPI(
    title="Enterprise GRC Suite",
    description="Automated Information Security Auditing Tool",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(frameworks.router, prefix="/api")
app.include_router(controls.router, prefix="/api")
app.include_router(evidence.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(collectors.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
