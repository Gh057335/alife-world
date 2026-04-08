#!/usr/bin/env python3
import uvicorn
from config import HOST, PORT
if __name__ == "__main__":
    print(f"\n  🧬 ALife — AI World\n  http://localhost:{PORT}\n")
    uvicorn.run("server:app", host=HOST, port=PORT, reload=False, log_level="warning")
