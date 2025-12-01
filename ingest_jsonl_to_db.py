import os
import json
from typing import List

import psycopg2
from psycopg2.extras import Json
import ollama

# ------------------------------------------------------------------------------
# DB config - match this with your Docker Postgres settings
# ------------------------------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ragdb")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")  # <-- change or env-var

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")



def get_embedding(text: str) -> List[float]:
    """
    Call Ollama to get the embedding vector for a given text chunk.
    """
    resp = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return resp["embedding"]  # list[float]


def ingest_jsonl_file(file_path: str):
    """
    Read a JSONL file (one JSON object per line) and insert each record
    as a row in the rag_chunks table with an embedding.
    """
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    cur = conn.cursor()

    print(f"Ingesting file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue  # skip empty lines

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"⚠️ Skipping line {line_number}: invalid JSON ({e})")
                continue

            # Extract fields from your JSON structure
            source_id = obj.get("source_id", "")
            chunk_id = obj.get("chunk_id", "")
            content = obj.get("content", "")
            metadata = obj.get("metadata", {})

            if not content:
                print(f"⚠️ Skipping line {line_number}: no content")
                continue

            # Get embedding from Ollama
            embedding = get_embedding(content)

            # Insert into rag_chunks
            cur.execute(
                """
                INSERT INTO rag_chunks (source_id, chunk_id, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    source_id,
                    chunk_id,
                    content,
                    Json(metadata),   # psycopg2 will store this as JSONB
                    embedding,        # pgvector accepts array-style input
                ),
            )

            print(f"✅ Inserted line {line_number} (chunk_id={chunk_id})")

    conn.commit()
    cur.close()
    conn.close()
    print("🎉 Finished ingesting file.")


def main():
    # You can point this to a single file...
    # jsonl_path = r"C:\path\to\advisors_graduate_contact_info.jsonl"

    # Or a folder of multiple JSONL files:
    folder = r"F:\SFWE403-Group-6-Project\Json-Files"

    if os.path.isdir(folder):
        for fname in os.listdir(folder):
            if not (fname.endswith(".json") or fname.endswith(".jsonl")):
                continue
            full_path = os.path.join(folder, fname)
            ingest_jsonl_file(full_path)
    else:
        # If folder is actually a single file path, ingest that one
        ingest_jsonl_file(folder)


if __name__ == "__main__":
    import os
    import sys

    # Optional: allow passing a file path as an argument:
    # python ingest_jsonl_to_db.py path\to\file.jsonl
    if len(sys.argv) > 1:
        ingest_jsonl_file(sys.argv[1])
    else:
        main()