from __future__ import annotations

import os
from typing import Any, cast

USE_MONGO = os.getenv("USE_MONGO", "1").lower() in {"1", "true", "yes"}

if USE_MONGO:
    from . import db_mongo as _db  # falls deine Datei anders heißt, hier anpassen
else:
    from . import db_memory as _db

db = cast(Any, _db)

__all__ = ["db"]
