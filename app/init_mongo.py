#!/usr/bin/env python3
"""
One-time initialization script to populate MongoDB with sample data.
Defaults: mongodb://localhost:27017, db=datatables_demo, collection=people
Usage:
  python -m app.init_mongo --count 1000000
"""
import argparse
import os
from typing import List, Dict, Any
from pymongo import MongoClient, ASCENDING

DEFAULT_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DEFAULT_DB = os.getenv("MONGO_DB", "datatables_demo")
DEFAULT_COLL = os.getenv("MONGO_COLLECTION", "people")

POSITIONS = ["Developer", "Manager", "Analyst", "QA", "DevOps"]
OFFICES = ["NY", "SF", "Berlin", "Tokyo", "Remote"]


def generate_people(n: int) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        items.append(
            {
                "id": i,
                "name": f"Person {i}",
                "position": POSITIONS[i % 5],
                "office": OFFICES[i % 5],
                "age": 20 + (i % 30),
                "start_date": f"20{10 + (i % 15)}-0{1 + (i % 9)}-15",
                "salary": 50000 + (i % 50) * 1000,
            }
        )
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default=DEFAULT_URI)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--collection", default=DEFAULT_COLL)
    parser.add_argument("--count", type=int, default=1_000_000)
    parser.add_argument("--batch", type=int, default=50_000, help="bulk insert batch size")
    args = parser.parse_args()

    client = MongoClient(args.uri)
    coll = client[args.db][args.collection]

    # Indexes
    coll.create_index([("id", ASCENDING)], unique=True)

    # If already populated, do nothing
    existing = coll.estimated_document_count()
    if existing >= args.count:
        print(f"Collection already has {existing} documents; nothing to do.")
        return

    # Insert in batches
    remaining = args.count - existing
    start_id = existing + 1
    print(f"Inserting {remaining} documents starting at id {start_id}...")

    batch_size = args.batch
    to_insert = []
    for i in range(start_id, args.count + 1):
        to_insert.append(
            {
                "id": i,
                "name": f"Person {i}",
                "position": POSITIONS[i % 5],
                "office": OFFICES[i % 5],
                "age": 20 + (i % 30),
                "start_date": f"20{10 + (i % 15)}-0{1 + (i % 9)}-15",
                "salary": 50000 + (i % 50) * 1000,
            }
        )
        if len(to_insert) >= batch_size:
            coll.insert_many(to_insert, ordered=False)
            print(f"Inserted {len(to_insert)} docs up to id {i}")
            to_insert = []

    if to_insert:
        coll.insert_many(to_insert, ordered=False)
        print(f"Inserted final {len(to_insert)} docs")

    print("Done.")


if __name__ == "__main__":
    main()
