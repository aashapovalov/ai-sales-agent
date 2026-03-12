"""Start the Agent Memory API server."""

import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("API_HOST", "127.0.0.1")
port = int(os.getenv("API_PORT", "8000"))

if __name__ == "__main__":
    print(f"Starting Agent Memory API at http://{host}:{port}")
    print(f"Docs available at http://{host}:{port}/docs\n")
    uvicorn.run("api.server:app", host=host, port=port, reload=True)
