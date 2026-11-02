#!/bin/bash
echo "Stopping all cross-insurer microservices..."
lsof -ti :8000 -ti :8001 -ti :8002 -ti :8003 -ti :8004 | xargs kill -9 2>/dev/null
pkill -f "services.gateway.main:app" 2>/dev/null
pkill -f "services.decision_service.main:app" 2>/dev/null
pkill -f "services.fingerprint_service.main:app" 2>/dev/null
pkill -f "services.similarity_service.main:app" 2>/dev/null
pkill -f "services.ingestion_service.main:app" 2>/dev/null
pkill -f "run_services.py" 2>/dev/null
echo "All microservices stopped."

