# FastAPI + Strawberry GraphQL + DataTables (Server‑Side) + MongoDB

A production‑ready starter showing how to power jQuery DataTables with true server‑side processing using FastAPI and MongoDB, alongside a Strawberry GraphQL API that reads from the same database. It also includes a one‑time data seeding script to generate large datasets (e.g., 1,000,000 documents) for realistic testing.

## Why this project?
- Many examples show DataTables fetching all data in the browser. That doesn’t scale.
- Here, pagination, sorting, and searching happen on the server (MongoDB), so it remains fast for millions of rows.
- A Strawberry GraphQL endpoint demonstrates how the same data model can be queried via GraphQL.

## Architecture
- FastAPI application exposing:
  - REST endpoint for DataTables at `/datatable` (supports GET and advanced POST queries)
  - Strawberry GraphQL API at `/graphql-strawberry`
  - Static frontend at `/` (DataTables client)
- MongoDB for persistence (default: `mongodb://localhost:27017`)
- Simple data access helpers in `app/db.py` (ensures indexes, builds queries, and uses aggregation for paging + counts)
- One‑time data init script in `app/init_mongo.py`

## Features
- Server‑side DataTables (paging, sort, global search)
- Strawberry GraphQL endpoint with a People page type
- MongoDB text index for fast search
- Advanced POST mode on `/datatable` to run arbitrary MongoDB queries and choose collections
- Static assets split for production under `app/static/include/`

## Quick start
1) Prerequisites
- Python 3.10+ (tested with modern FastAPI/Starlette)
- MongoDB running locally on `mongodb://localhost:27017`

2) Create a virtual environment
- python -m venv .venv
- source .venv/bin/activate   # Windows: .venv\Scripts\activate

3) Install dependencies
- pip install -r requirements.txt

4) Seed the database (one‑time)
- python -m app.init_mongo --count 1000000
- Tips:
  - Use `--count` to change dataset size.
  - You can set env vars to target a different DB/collection (see below).

5) Run the app
- uvicorn app.main:app --reload

6) Open in your browser
- App (DataTables): http://127.0.0.1:8000/
- GraphQL (Strawberry): http://127.0.0.1:8000/graphql-strawberry

## Configuration (env vars)
- MONGO_URI (default: `mongodb://localhost:27017`)
- MONGO_DB (default: `datatables_demo`)
- MONGO_COLLECTION (default: `people`)

You can export these before running the server or the init script.

## Data seeding (app/init_mongo.py)
- Generates consistent sample documents with fields: `id`, `name`, `position`, `office`, `age`, `start_date`, `salary`.
- Creates a unique index on `id`.
- Example:
  - python -m app.init_mongo --count 250000 --batch 50000

## DataTables server‑side API
Endpoint: `/datatable`
- Methods: GET (classic DataTables params) or POST (advanced query)
- Response shape (standard DataTables):
  - `{ draw, recordsTotal, recordsFiltered, data }`

GET usage (what the included frontend does):
- DataTables sends params: `draw`, `start`, `length`, `search[value]`, `order[0][column]`, `order[0][dir]`, and `columns[i][data]`.
- The server applies:
  - Global search via Mongo `$text` (with a combined text index) + numeric equality for integers
  - Sorting on the requested column (defaults to `id`)
  - Pagination via skip/limit in an aggregation `$facet`

Advanced POST usage (arbitrary Mongo query):
- POST JSON body in addition to the usual query params:
```
{
  "collection": "people",             // optional, switch collections
  "query": {"office": "NY"},         // optional, raw MongoDB filter
  "projection": {"_id": 0, "name": 1} // optional, projection
}
```
- The server will:
  - Run the provided `query` (if present) or fall back to the global search built from `search[value]`
  - Respect sorting/pagination from DataTables params
  - Return the same DataTables response shape

Security note: Allowing arbitrary queries from the client is powerful but risky. Add authentication/authorization and validate/whitelist allowed operators in production.

## GraphQL (Strawberry)
- Endpoint: `/graphql-strawberry` (comes with an interactive UI)
- Example query:
```
query {
  people(search: "Person 42", orderColumn: "id", orderDir: "asc", start: 0, length: 10) {
    recordsTotal
    recordsFiltered
    records { id name position office age startDate salary }
  }
}
```
- Notes:
  - The GraphQL resolver reuses the same DB paging/search logic as the DataTables route.

## Frontend
- Static page at `app/static/index.html`
- Custom CSS/JS under `app/static/include/`
- Change visible columns by modifying `columns` in `app/static/include/js/main.js` and the table header in `index.html`.

## Performance tips
- The init script and `ensure_indexes()` create useful indexes, including a text index for fast search.
- Keep page sizes reasonable (10–50).
- For high concurrency, run uvicorn with multiple workers: `uvicorn app.main:app --workers 2`.
- Consider hosting MongoDB on SSD and tuning WiredTiger cache for very large datasets.

## Troubleshooting
- Server can start before Mongo is up; endpoints will fail on demand. Ensure Mongo is running.
- If searches seem slow, verify the text index exists on your target collection.
- If you change `MONGO_DB`/`MONGO_COLLECTION`, re‑run the seeding script or point to an existing dataset.

## Contributing
PRs and issues are welcome. Please open a discussion if you’d like to add more query modes, authentication, or schema customization.

## License
MIT License (see LICENSE if provided).
