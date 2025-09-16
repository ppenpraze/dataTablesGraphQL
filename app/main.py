from typing import List, Optional, Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


# Strawberry (GraphQL schema 2)
import strawberry
from strawberry.asgi import GraphQL as StrawberryGraphQL

# DB layer (Model)
from app.db import find_page, count_all, count_filtered, COLUMNS, ensure_indexes



# -----------------------------
# Shared server-side processing logic for DataTables
# -----------------------------

def filter_sort_paginate(
    items: List[Dict[str, Any]],
    search_value: str,
    order_column: Optional[str],
    order_dir: str,
    start: int,
    length: int,
) -> (List[Dict[str, Any]], int):
    # Global search (case-insensitive) across stringified values
    if search_value:
        sv = search_value.lower()
        filtered = [
            row for row in items if any(sv in str(v).lower() for v in row.values())
        ]
    else:
        filtered = list(items)

    # Ordering
    if order_column in COLUMNS:
        reverse = order_dir == "desc"
        filtered.sort(key=lambda r: r.get(order_column), reverse=reverse)

    total_filtered = len(filtered)

    # Pagination
    if length == -1:
        paged = filtered
    else:
        paged = filtered[start : start + length]

    return paged, total_filtered




# -----------------------------
# Strawberry schema
# -----------------------------

@strawberry.type
class Person:
    id: int
    name: str
    position: str
    office: str
    age: int
    start_date: str
    salary: int


@strawberry.type
class PersonPage:
    records: List[Person]
    records_total: int
    records_filtered: int


@strawberry.type
class StrawberryQuery:
    @strawberry.field
    def people(
        self,
        search: str = "",
        order_column: str = "id",
        order_dir: str = "asc",
        start: int = 0,
        length: int = 10,
    ) -> PersonPage:
        records, filtered_count = find_page(
            search, order_column, order_dir, start, length
        )
        return PersonPage(
            records=[Person(**r) for r in records],
            records_total=count_all(),
            records_filtered=filtered_count,
        )


strawberry_schema = strawberry.Schema(query=StrawberryQuery)


# -----------------------------
# FastAPI setup
# -----------------------------

app = FastAPI(title="FastAPI + GraphQL (Strawberry) + DataTables Demo")

# Ensure indexes on startup using FastAPI event
@app.on_event("startup")
def _startup():
    try:
        ensure_indexes()
    except Exception:
        # Avoid crashing if Mongo is not up yet; endpoints will error on demand
        pass

# Mount static directory for JS/CSS
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# GraphQL endpoints
# Strawberry endpoint (ASGI app with built-in playground)
app.add_route("/graphql-strawberry", StrawberryGraphQL(schema=strawberry_schema))



# DataTables server-side processing endpoint
@app.api_route("/datatable", methods=["GET", "POST"])
async def datatable(request: Request):
    # Accept standard DataTables GET query params and an optional JSON body
    # with advanced Mongo options: { collection, query, projection, sort }
    q = request.query_params
    body: Dict[str, Any] = {}
    if request.method == "POST":
        try:
            body = await request.json()
            if not isinstance(body, dict):
                body = {}
        except Exception:
            body = {}

    # Required by DataTables
    draw = int(q.get("draw", 1))
    start = int(q.get("start", 0))
    length = int(q.get("length", 10))

    search_value = q.get("search[value]", "")

    # Determine ordering from DataTables parameters
    order_col_idx = q.get("order[0][column]")
    order_dir = q.get("order[0][dir]", "asc")

    # Default ordering
    order_column = "id"

    # DataTables sends the columns list; we prefer to respect the client-provided mapping
    try:
        if order_col_idx is not None:
            idx = int(order_col_idx)
            # columns[idx][data] can be a column name string if configured in JS
            order_column_candidate = q.get(f"columns[{idx}][data]")
            if order_column_candidate in COLUMNS:
                order_column = order_column_candidate
            else:
                # If not provided, fallback to predefined mapping by index
                if 0 <= idx < len(COLUMNS):
                    order_column = COLUMNS[idx]
    except Exception:
        pass

    # Advanced Mongo options from body
    collection = body.get("collection")
    raw_query = body.get("query")
    projection = body.get("projection")

    records, filtered_count = find_page(
        search_value, order_column, order_dir, start, length,
        collection=collection,
        raw_query=raw_query,
        projection=projection,
    )

    # Total records in the selected collection (ignores filtering)
    total_records = count_all(collection)

    return JSONResponse(
        {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_count,
            "data": records,
        }
    )


# Front page serves static index.html
@app.get("/", response_class=HTMLResponse)
async def home():
    # Serve the static HTML file instead of inline HTML
    from fastapi.responses import FileResponse
    return FileResponse("app/static/index.html")


# Simple health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}


# -----------------------------
# Run with: uvicorn app.main:app --reload
# -----------------------------
