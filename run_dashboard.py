import subprocess
import signal
import sys
import time
import os

def run_dashboard():
    print("🚀 Starting J.A.R.V.I.S. Command Center...")
    
    # Start Backend
    print("🔹 Launching Backend (FastAPI)...")
    backend = subprocess.Popen(
        ["uvicorn", "dashboard.backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Start Frontend
    print("🔹 Launching Frontend (React)...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="dashboard/frontend",
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    print("\n✅ Dashboard is running!")
    print("👉 Open: http://localhost:5173")
    print("backend: http://localhost:8000")
    print("\n(Press Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Dashboard...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)

if __name__ == "__main__":
    run_dashboard()
