import os
import sys
import subprocess
import time
import signal
import httpx

SERVICES = [
    {
        "name": "fingerprint_service",
        "cmd": [sys.executable, "-m", "uvicorn", "services.fingerprint_service.main:app", "--host", "0.0.0.0", "--port", "8001"],
        "env": {"CONSORTIUM_SALT": "dev-salt-abc-123"}
    },
    {
        "name": "similarity_service",
        "cmd": [sys.executable, "-m", "uvicorn", "services.similarity_service.main:app", "--host", "0.0.0.0", "--port", "8002"],
        "env": {}
    },
    {
        "name": "decision_service",
        "cmd": [sys.executable, "-m", "uvicorn", "services.decision_service.main:app", "--host", "0.0.0.0", "--port", "8003"],
        "env": {
            "FINGERPRINT_SERVICE_URL": "http://localhost:8001/fingerprint",
            "SIMILARITY_SERVICE_URL": "http://localhost:8002/similarity",
            "DATABASE_URL": ""
        }
    },
    {
        "name": "ingestion_service",
        "cmd": [sys.executable, "-m", "uvicorn", "services.ingestion_service.main:app", "--host", "0.0.0.0", "--port", "8004"],
        "env": {
            "DECISION_SERVICE_URL": "http://localhost:8003/evaluate_claim"
        }
    },
    {
        "name": "gateway",
        "cmd": [sys.executable, "-m", "uvicorn", "services.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "env": {
            "DECISION_SERVICE_URL": "http://localhost:8003",
            "FINGERPRINT_SERVICE_URL": "http://localhost:8001",
            "SIMILARITY_SERVICE_URL": "http://localhost:8002",
            "INGESTION_SERVICE_URL": "http://localhost:8004"
        }
    }
]

os.makedirs("logs", exist_ok=True)
processes = []

def cleanup(signum=None, frame=None):
    print("\nShutting down all services...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
    time.sleep(1)
    for p in processes:
        if p.poll() is None:
            p.kill()
    print("All services stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    print("==================================================")
    print("Launching Cross-Insurer Fraud Detection Framework")
    print("==================================================")

    for svc in SERVICES:
        env = os.environ.copy()
        env.update(svc["env"])
        log_file = open(f"logs/{svc['name']}.log", "w")
        proc = subprocess.Popen(
            svc["cmd"],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        processes.append(proc)
        print(f"-> Started {svc['name']:<22} (PID: {proc.pid})")

    # Give services a moment to initialize
    print("\nVerifying service health...")
    time.sleep(2)

    checks = [
        ("Fingerprint (8001)", "http://localhost:8001/health"),
        ("Similarity  (8002)", "http://localhost:8002/docs"),
        ("Decision    (8003)", "http://localhost:8003/docs"),
        ("Ingestion   (8004)", "http://localhost:8004/health"),
        ("Gateway     (8000)", "http://localhost:8000/health"),
    ]

    for label, url in checks:
        for attempt in range(10):
            try:
                r = httpx.get(url, timeout=2.0)
                if r.status_code in [200, 207]:
                    print(f" [OK] {label}: {r.status_code}")
                    break
            except Exception:
                time.sleep(0.5)
        else:
            print(f" [WAIT] {label} not responding yet")

    print("\n--------------------------------------------------")
    print("Consortium Platform running successfully!")
    print("Dashboard: http://localhost:8000")
    print("Health:    http://localhost:8000/health")
    print("--------------------------------------------------")

    # Keep running indefinitely
    try:
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    print(f"Warning: A service process (PID {p.pid}) exited unexpectedly.")
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()

