from typing import List, Dict, Any, Optional, Tuple
import os
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.collection import Collection

# Shared columns allowed for sorting/searching
COLUMNS = ["id", "name", "position", "office", "age", "start_date", "salary"]

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "datatables_demo")
MONGO_COLL = os.getenv("MONGO_COLLECTION", "people")

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, tz_aware=False)
    return _client


def get_collection(collection: Optional[str] = None) -> Collection:
    db = get_client()[MONGO_DB]
    return db[collection or MONGO_COLL]


def ensure_indexes() -> None:
    coll = get_collection()
    # Unique index on id for stable ordering and avoiding duplicates
    coll.create_index([("id", ASCENDING)], unique=True)
    # Helpful indexes for common sorts
    coll.create_index([("name", ASCENDING)])
    coll.create_index([("position", ASCENDING)])
    coll.create_index([("office", ASCENDING)])
    coll.create_index([("age", ASCENDING)])
    coll.create_index([("start_date", ASCENDING)])
    coll.create_index([("salary", ASCENDING)])
    # Text index for fast global search across string fields
    try:
        coll.create_index([("name", TEXT), ("position", TEXT), ("office", TEXT), ("start_date", TEXT)], name="_text_all")
    except Exception:
        pass


def _build_filter(search: str) -> Dict[str, Any]:
    if not search:
        return {}
    # Prefer MongoDB text search for string content; supports stemming and can use text index.
    flt: Dict[str, Any] = {"$text": {"$search": search}}
    # If search is purely numeric, augment with numeric equality across numeric fields
    try:
        n = int(search)
        flt = {"$or": [flt, {"id": n}, {"age": n}, {"salary": n}]}
    except ValueError:
        pass
    return flt


def count_all(collection: Optional[str] = None) -> int:
    coll = get_collection(collection)
    return coll.estimated_document_count()


def count_filtered(search: str) -> int:
    coll = get_collection()
    flt = _build_filter(search)
    if not flt:
        return coll.estimated_document_count()
    return coll.count_documents(flt)


def find_page(
    search: str,
    order_column: Optional[str],
    order_dir: str,
    start: int,
    length: int,
    collection: Optional[str] = None,
    raw_query: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, int]] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Find a page of documents. If raw_query is provided, it overrides the default
    search-based filter. You can also specify a collection name and projection.
    """
    coll = get_collection(collection)
    flt = raw_query if raw_query is not None else _build_filter(search)

    # Sort: allow arbitrary field when custom query/collection is used
    sort_col = order_column if order_column else "id"
    sort_dir = DESCENDING if order_dir == "desc" else ASCENDING

    proj = projection if projection is not None else {"_id": 0}

    # Build aggregation pipeline to fetch page and filtered count in one round trip
    pipeline: List[Dict[str, Any]] = []
    if flt:
        pipeline.append({"$match": flt})
    # If sorting by text score, project score; else regular sort
    sort_stage: Dict[str, Any]
    if isinstance(flt, dict) and "$text" in flt and sort_col in (None, "score"):
        pipeline.append({"$addFields": {"score": {"$meta": "textScore"}}})
        sort_stage = {"score": -1}
    else:
        sort_stage = {sort_col: -1 if sort_dir == DESCENDING else 1}
    pipeline.append({"$sort": sort_stage})
    pipeline.append({"$project": {**proj}})
    facet: Dict[str, Any] = {
        "data": [],
        "meta": [{"$count": "recordsFiltered"}],
    }
    if start:
        facet["data"].append({"$skip": start})
    if length != -1:
        facet["data"].append({"$limit": length})
    pipeline.append({"$facet": facet})

    agg_res = list(coll.aggregate(pipeline, allowDiskUse=True))
    if agg_res:
        res = agg_res[0]
        data = res.get("data", [])
        meta = res.get("meta", [])
        filtered = meta[0].get("recordsFiltered", 0) if meta else (coll.estimated_document_count() if not flt else 0)
    else:
        data, filtered = [], 0

    return data, filtered
