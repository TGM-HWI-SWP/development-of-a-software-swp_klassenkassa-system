import os, sys

# src/ in den Python-Pfad aufnehmen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "myapp.backend.api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )

