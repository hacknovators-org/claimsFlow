#!/usr/bin/env python3

import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def run_streamlit():
    """Run the Streamlit UI application"""
    
    # Get the absolute path to the UI main file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(current_dir, "ui", "main.py")
    
    if not os.path.exists(ui_path):
        print(f"Error: UI main file not found at {ui_path}")
        return
    
    print("🚀 Starting Claims Processing Agent UI...")
    print("📊 Access the interface at: http://localhost:8501")
    print("---")
    
    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir + (os.pathsep + env.get('PYTHONPATH', ''))
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", ui_path,
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ], env=env)
    except KeyboardInterrupt:
        print("\n👋 Shutting down UI...")
    except Exception as e:
        print(f"❌ Error running UI: {e}")

if __name__ == "__main__":
    run_streamlit()