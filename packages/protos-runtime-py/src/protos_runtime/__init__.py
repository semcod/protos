"""protos-runtime: lightweight runtime library extracted from semcod/protos.

Public API:
    - SearchIndex: SQLite FTS5 read model
    - models.search_v1: Pydantic contract types for search domain
    - models.identification_v1: Pydantic contract types for identification domain
"""

from .search_index import SearchIndex

__all__ = ["SearchIndex"]
__version__ = "0.1.24"
