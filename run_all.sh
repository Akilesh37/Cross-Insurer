#!/bin/bash
echo "Starting services..."
source venv/bin/activate

# Install dependencies if not already
pip install -r services/fingerprint_service/requirements.txt -q
pip install -r services/similarity_service/requirements.txt -q
pip install -r services/decision_service/requirements.txt -q
pip install -r services/ingestion_service/requirements.txt -q
pip install -r services/gateway/requirements.txt -q

export CONSORTIUM_SALT=dev-salt-abc-123
export FINGERPRINT_SERVICE_URL=http://localhost:8001/fingerprint
export SIMILARITY_SERVICE_URL=http://localhost:8002/similarity
export DECISION_SERVICE_URL=http://localhost:8003/evaluate_claim
export INGESTION_SERVICE_URL=http://localhost:8004

# Start services using module path from root to resolve relative imports correctly
uvicorn services.fingerprint_service.main:app --port 8001 &
PID1=$!
uvicorn services.similarity_service.main:app --port 8002 &
PID2=$!
uvicorn services.decision_service.main:app --port 8003 &
PID3=$!
uvicorn services.ingestion_service.main:app --port 8004 &
PID4=$!
uvicorn services.gateway.main:app --port 8000 &
PID5=$!

echo "Waiting for services to start..."
sleep 5

echo "Running Pipeline..."
python run_pipeline.py

echo "Cleaning up..."
kill $PID1 $PID2 $PID3 $PID4 $PID5
