# FastAPI + GraphQL (Strawberry) + DataTables Demo

This repository contains a minimal FastAPI application exposing a Strawberry GraphQL endpoint and a simple HTML page that demonstrates DataTables with full server-side processing.

## Features
- FastAPI web server
- GraphQL via Strawberry at `/graphql-strawberry`
- DataTables server-side processing endpoint at `/datatable`
- Root page `/` serves a static HTML page (app/static/index.html) with a DataTable fetching from `/datatable`.
- Frontend assets are split for production: CSS in `app/static/include/css/` and JS in `app/static/include/js/`.

## Getting Started

1. Ensure MongoDB is running locally
   - Install and start MongoDB Community Server (listening on mongodb://localhost:27017).
   - Optionally set environment variables: MONGO_URI, MONGO_DB, MONGO_COLLECTION.

2. Create and activate a virtual environment (recommended)
   - python -m venv .venv
   - source .venv/bin/activate   # on Windows: .venv\\Scripts\\activate

3. Install dependencies
   - pip install -r requirements.txt

4. Initialize sample data in MongoDB (one-time)
   - python -m app.init_mongo --count 1000000
   - You can change the count and use env vars to target a different DB/collection.

5. Run the server
   - uvicorn app.main:app --reload

6. Open the app in your browser
   - http://127.0.0.1:8000/
   - Strawberry GraphQL Playground: http://127.0.0.1:8000/graphql-strawberry

## Notes
- The backend now reads from MongoDB (collection defaults to datatables_demo.people). Use app/init_mongo.py to seed data.
- The DataTables server-side processing implementation supports global search, ordering, and pagination, compatible with DataTables' expected query parameters and response structure.
- Advanced querying: You can POST to `/datatable` with a JSON body like `{ "collection": "people", "query": {"office":"NY"}, "projection": {"_id":0} }`. DataTables paging/sort params are still honored while the MongoDB query is applied server-side.
- Tip: For large datasets, ensure appropriate indexes exist (the init script creates useful indexes, including a text index for fast search). Prefer reasonable page lengths (10–50). You can also run uvicorn with multiple workers for concurrency, e.g., `uvicorn app.main:app --workers 2`.
