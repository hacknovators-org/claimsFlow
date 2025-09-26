#!/usr/bin/env python3

import subprocess
import sys
import os
import time
import threading
from dotenv import load_dotenv

load_dotenv()

def run_websocket_server():
    """Run the WebSocket server in a separate process"""
    print("🚀 Starting Enhanced WebSocket Server...")
    
    try:
        subprocess.run([
            sys.executable, "websocket_server.py"
        ], check=False)
    except KeyboardInterrupt:
        print("🛑 WebSocket server stopped")
    except Exception as e:
        print(f"❌ WebSocket server error: {e}")

def run_streamlit_ui():
    """Run the Streamlit UI application"""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(current_dir, "ui", "main.py")
    
    if not os.path.exists(ui_path):
        print(f"❌ Error: UI main file not found at {ui_path}")
        return
    
    print("🎨 Starting Enhanced Claims Processing UI...")
    print("📊 Real-time WebSocket updates enabled")
    print("🌐 Access the interface at: http://localhost:8501")
    print("---")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = current_dir + (os.pathsep + env.get('PYTHONPATH', ''))
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", ui_path,
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light",
            "--theme.primaryColor", "#1f77b4",
            "--theme.backgroundColor", "#ffffff",
            "--theme.secondaryBackgroundColor", "#f0f2f6"
        ], env=env, check=False)
    except KeyboardInterrupt:
        print("\n👋 Shutting down UI...")
    except Exception as e:
        print(f"❌ Error running UI: {e}")

def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        "OPENAI_API_KEY",
        "EMAIL_HOST", 
        "EMAIL_APP_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please check your .env file")
        return False
    
    print("✅ Environment validation successful")
    return True

def main():
    print("=" * 60)
    print("🏢 ENHANCED CLAIMS PROCESSING AGENT SYSTEM")
    print("🤖 AI-Powered Real-time Claims Analysis")
    print("=" * 60)
    
    if not validate_environment():
        return
    
    print("\n🔧 System Components:")
    print("   📡 WebSocket Server - Real-time updates")
    print("   🎨 Streamlit UI - Interactive dashboard")
    print("   🧠 AI Agents - Claims analysis pipeline")
    print("   📊 Live Progress - Real-time monitoring")
    
    mode = input("\n🚀 Select mode:\n1. Full System (WebSocket + UI)\n2. UI Only (Fallback mode)\n3. WebSocket Server Only\n\nChoice (1-3): ").strip()
    
    if mode == "1":
        print("\n🚀 Starting Full Enhanced System...")
        
        websocket_thread = threading.Thread(target=run_websocket_server)
        websocket_thread.daemon = True
        websocket_thread.start()
        
        time.sleep(2)
        
        try:
            run_streamlit_ui()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down system...")
        
    elif mode == "2":
        print("\n🎨 Starting UI Only (Fallback mode)...")
        run_streamlit_ui()
        
    elif mode == "3":
        print("\n📡 Starting WebSocket Server Only...")
        run_websocket_server()
        
    else:
        print("❌ Invalid choice. Exiting...")
        return
    
    print("\n✨ Thanks for using the Enhanced Claims Processing Agent!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 System stopped by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        raise