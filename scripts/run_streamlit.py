#!/usr/bin/env python3
"""
Launch script for Turbo Code Streamlit interface

This script starts the Streamlit web interface for Turbo Code.
Make sure the FastAPI backend is running before starting this.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Change to project root
    os.chdir(project_root)

    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)

    # Streamlit app path
    app_path = project_root / "streamlit_app.py"

    if not app_path.exists():
        print(f"❌ Streamlit app not found at {app_path}")
        sys.exit(1)

    print("🚀 Starting Turbo Code Streamlit Interface...")
    print("📡 Make sure FastAPI backend is running at http://localhost:8001")
    print("🌐 Streamlit will open at http://localhost:8501")
    print()

    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.serverAddress", "localhost",
            "--browser.serverPort", "8501"
        ], env=env)
    except KeyboardInterrupt:
        print("\n👋 Streamlit interface stopped")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()