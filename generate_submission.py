import os
import json
import asyncio
import asyncpg

DATABASE_URL =  "postgresql://user1:harsh123@localhost:5432/pharmadb"


BENCHMARK_FILE = "benchmark_queries.json"
SUBMISSION_FILE = "submission.json"

async def fetch_results(pool, query_type, query_text, limit=20):
    async with pool.acquire() as conn:
        if query_type == "prefix":
            sql = """
            SELECT name
            FROM medicines
            WHERE name ILIKE $1
            ORDER BY name
            LIMIT $2
            """
            rows = await conn.fetch(sql, f"{query_text}%", limit)
        elif query_type == "substring":
            sql = """
            SELECT name
            FROM medicines
            WHERE name ILIKE $1
            ORDER BY name
            LIMIT $2
            """
            rows = await conn.fetch(sql, f"%{query_text}%", limit)
        elif query_type == "fuzzy":
            sql = """
            SELECT name
            FROM medicines
            WHERE name % $1
            ORDER BY similarity(name, $1) DESC
            LIMIT $2
            """
            rows = await conn.fetch(sql, query_text, limit)
        elif query_type == "fulltext":
            sql = """
            SELECT name
            FROM medicines
            WHERE search_tsv @@ plainto_tsquery('english', $1)
            ORDER BY ts_rank_cd(search_tsv, plainto_tsquery('english', $1)) DESC
            LIMIT $2
            """
            rows = await conn.fetch(sql, query_text, limit)
        else:
            rows = []
    return [r["name"] for r in rows]

async def main():
    # Load benchmark queries
    with open(BENCHMARK_FILE, "r") as f:
        benchmark_data = json.load(f)

    # Connect to DB
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)

    submission_results = {}

    for test in benchmark_data["tests"]:
        test_id = str(test["id"])
        query_type = test["type"]
        query_text = test["query"]

        names = await fetch_results(pool, query_type, query_text, limit=20)
        # Convert list to dict with numeric string keys (hackathon format)
        submission_results[test_id] = {str(i): name for i, name in enumerate(names)}

    await pool.close()

    submission_json = {"results": submission_results}

    # Write to submission.json
    with open(SUBMISSION_FILE, "w") as f:
        json.dump(submission_json, f, indent=2)

    print(f"✅ Submission generated: {SUBMISSION_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
