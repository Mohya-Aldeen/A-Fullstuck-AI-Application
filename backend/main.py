"""Service-root entrypoint for Railpack.

The monorepo config in railway.toml is not always applied when the service
root is backend/, and Railpack then fails prepare with no start command.
It does run main.py in this directory.
"""

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT)
