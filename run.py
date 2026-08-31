import sys
import os
import subprocess
import webbrowser
import threading
import time

# Map package names to import names
PACKAGE_MAP = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "scikit-learn": "sklearn",
    "numpy": "numpy",
    "pandas": "pandas",
    "pydantic": "pydantic",
    "httpx": "httpx"
}

def check_and_install_dependencies():
    missing = []
    for pkg_name, import_name in PACKAGE_MAP.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        print(f"[Anchor Launcher] Installing required packages: {missing} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("[Anchor Launcher] Dependencies successfully installed.\n")


def print_banner():
    banner = """
==========================================================================
     _                 _                   
    / \\   _ __   ___| |__   ___  _ __      
   / _ \\ | '_ \\ / __| '_ \\ / _ \\| '__|     
  / ___ \\| | | | (__| | | | (_) | |        
 /_/   \\_\\_| |_|\\___|_| |_|\\___/|_|        
                                           
   PREDICTIVE INTELLIGENCE FOR CUSTOMER RETENTION
==========================================================================
 [>] Server is LIVE and listening for connections!
 [>] Open your browser and navigate to:
     -> http://127.0.0.1:8000
     -> http://localhost:8000
     -> http://127.0.0.1:8000/docs (Interactive Swagger API Docs)
==========================================================================
 [!] NOTE: Do not type '0.0.0.0' in your browser URL bar.
     Use: http://127.0.0.1:8000
==========================================================================
 [!] Keep this terminal open while using the platform.
 [!] Press CTRL+C to stop the server.
==========================================================================
"""
    print(banner)


def open_browser():
    time.sleep(1.2)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass


def main():
    check_and_install_dependencies()
    print_banner()

    # Automatically open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )


if __name__ == "__main__":
    main()
