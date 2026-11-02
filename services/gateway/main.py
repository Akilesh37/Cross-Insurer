import os
from pathlib import Path
import httpx
from fastapi import FastAPI, Request, Response, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cross-Insurer Consortium API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DECISION_SERVICE_URL = os.getenv("DECISION_SERVICE_URL", "http://decision_service:8000")
if DECISION_SERVICE_URL.endswith("/evaluate_claim"):
    DECISION_SERVICE_URL = DECISION_SERVICE_URL[:-len("/evaluate_claim")]
DECISION_SERVICE_URL = DECISION_SERVICE_URL.rstrip("/")

FINGERPRINT_SERVICE_URL = os.getenv("FINGERPRINT_SERVICE_URL", "http://fingerprint_service:8000")
if FINGERPRINT_SERVICE_URL.endswith("/fingerprint"):
    FINGERPRINT_SERVICE_URL = FINGERPRINT_SERVICE_URL[:-len("/fingerprint")]
FINGERPRINT_SERVICE_URL = FINGERPRINT_SERVICE_URL.rstrip("/")

SIMILARITY_SERVICE_URL = os.getenv("SIMILARITY_SERVICE_URL", "http://similarity_service:8000")
if SIMILARITY_SERVICE_URL.endswith("/similarity"):
    SIMILARITY_SERVICE_URL = SIMILARITY_SERVICE_URL[:-len("/similarity")]
SIMILARITY_SERVICE_URL = SIMILARITY_SERVICE_URL.rstrip("/")

INGESTION_SERVICE_URL = os.getenv("INGESTION_SERVICE_URL", "http://ingestion_service:8000")
if INGESTION_SERVICE_URL.endswith("/evaluate_claim"):
    INGESTION_SERVICE_URL = INGESTION_SERVICE_URL[:-len("/evaluate_claim")]
INGESTION_SERVICE_URL = INGESTION_SERVICE_URL.rstrip("/")

DASHBOARD_PATH = Path(__file__).resolve().parent.parent.parent / "dashboard" / "index.html"
if not DASHBOARD_PATH.exists():
    DASHBOARD_PATH = Path("/app/dashboard/index.html")

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    """Serves the central consortium fraud detection dashboard."""
    if DASHBOARD_PATH.exists():
        return HTMLResponse(content=DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Cross-Insurer Consortium Gateway Active</h1><p>Dashboard file not found.</p>")

@app.get("/health")
async def health_check():
    """Aggregated health check across all microservices."""
    services = {
        "gateway": "healthy",
        "fingerprint_service": "unknown",
        "similarity_service": "unknown",
        "decision_service": "unknown",
        "ingestion_service": "unknown",
    }
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        # Check fingerprint service
        try:
            r = await client.get(f"{FINGERPRINT_SERVICE_URL}/health")
            services["fingerprint_service"] = "healthy" if r.status_code == 200 else f"unhealthy ({r.status_code})"
        except Exception:
            services["fingerprint_service"] = "unreachable"

        # Check similarity service (doesn't have explicit /health, test /docs or /)
        try:
            r = await client.get(f"{SIMILARITY_SERVICE_URL}/docs")
            services["similarity_service"] = "healthy" if r.status_code == 200 else f"unhealthy ({r.status_code})"
        except Exception:
            services["similarity_service"] = "unreachable"

        # Check decision service
        try:
            r = await client.get(f"{DECISION_SERVICE_URL}/docs")
            services["decision_service"] = "healthy" if r.status_code == 200 else f"unhealthy ({r.status_code})"
        except Exception:
            services["decision_service"] = "unreachable"

        # Check ingestion service
        try:
            r = await client.get(f"{INGESTION_SERVICE_URL}/health")
            services["ingestion_service"] = "healthy" if r.status_code == 200 else f"unhealthy ({r.status_code})"
        except Exception:
            services["ingestion_service"] = "unreachable"

    all_healthy = all(v == "healthy" for v in services.values())
    return JSONResponse(status_code=200 if all_healthy else 207, content={"status": "ok" if all_healthy else "degraded", "services": services})

# Proxy helper
async def forward_request(target_url: str, request: Request) -> Response:
    client = httpx.AsyncClient(timeout=30.0)
    try:
        body = await request.body()
        req_headers = dict(request.headers)
        req_headers.pop("host", None)
        req_headers.pop("content-length", None)
        
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=req_headers,
            content=body,
            params=request.query_params,
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
    except httpx.RequestError as exc:
        return JSONResponse(status_code=502, content={"error": f"Failed to reach service: {str(exc)}"})
    finally:
        await client.aclose()

# Routes to Decision Service
@app.api_route("/evaluate_claim", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/api/evaluate_claim", methods=["GET", "POST", "OPTIONS"])
async def proxy_evaluate_claim(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/evaluate_claim", request)

@app.api_route("/debug/reset", methods=["DELETE", "POST", "OPTIONS"])
@app.api_route("/api/debug/reset", methods=["DELETE", "POST", "OPTIONS"])
async def proxy_debug_reset(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/debug/reset", request)

@app.api_route("/debug/registry", methods=["GET", "OPTIONS"])
async def proxy_debug_registry(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/debug/registry", request)

@app.api_route("/debug/db", methods=["GET", "OPTIONS"])
async def proxy_debug_db(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/debug/db", request)

@app.api_route("/graph/analytics", methods=["GET", "OPTIONS"])
@app.api_route("/api/graph/analytics", methods=["GET", "OPTIONS"])
async def proxy_graph_analytics(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/graph/analytics", request)

@app.api_route("/blockchain/ledger", methods=["GET", "OPTIONS"])
@app.api_route("/api/blockchain/ledger", methods=["GET", "OPTIONS"])
async def proxy_blockchain_ledger(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/blockchain/ledger", request)

@app.api_route("/benchmark/stats", methods=["GET", "OPTIONS"])
@app.api_route("/api/benchmark/stats", methods=["GET", "OPTIONS"])
async def proxy_benchmark_stats(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/benchmark/stats", request)

@app.api_route("/benchmark/run", methods=["POST", "OPTIONS"])
@app.api_route("/api/benchmark/run", methods=["POST", "OPTIONS"])
async def proxy_benchmark_run(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/benchmark/run", request)

@app.api_route("/simulate/multi_insurer", methods=["POST", "OPTIONS"])
@app.api_route("/api/simulate/multi_insurer", methods=["POST", "OPTIONS"])
async def proxy_simulate_multi_insurer(request: Request):
    return await forward_request(f"{DECISION_SERVICE_URL}/simulate/multi_insurer", request)

# Routes to Fingerprint Service
@app.api_route("/fingerprint", methods=["POST", "OPTIONS"])
@app.api_route("/api/fingerprint", methods=["POST", "OPTIONS"])
async def proxy_fingerprint(request: Request):
    return await forward_request(f"{FINGERPRINT_SERVICE_URL}/fingerprint", request)

# Routes to Similarity Service
@app.api_route("/similarity", methods=["POST", "OPTIONS"])
@app.api_route("/api/similarity", methods=["POST", "OPTIONS"])
async def proxy_similarity(request: Request):
    return await forward_request(f"{SIMILARITY_SERVICE_URL}/similarity", request)

# Routes to Ingestion Service
@app.api_route("/ingest/claim", methods=["POST", "OPTIONS"])
@app.api_route("/api/ingest/claim", methods=["POST", "OPTIONS"])
async def proxy_ingest_claim(request: Request):
    return await forward_request(f"{INGESTION_SERVICE_URL}/ingest/claim", request)

@app.api_route("/ingest/batch", methods=["POST", "OPTIONS"])
@app.api_route("/api/ingest/batch", methods=["POST", "OPTIONS"])
async def proxy_ingest_batch(request: Request):
    return await forward_request(f"{INGESTION_SERVICE_URL}/ingest/batch", request)

@app.post("/ingest/csv")
@app.post("/api/ingest/csv")
async def proxy_ingest_csv(file: UploadFile = File(...)):
    async with httpx.AsyncClient(timeout=60.0) as client:
        file_bytes = await file.read()
        files = {"file": (file.filename, file_bytes, file.content_type or "text/csv")}
        try:
            r = await client.post(f"{INGESTION_SERVICE_URL}/ingest/csv", files=files)
            return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type"))
        except httpx.RequestError as exc:
            return JSONResponse(status_code=502, content={"error": f"Failed to reach ingestion service: {str(exc)}"})
