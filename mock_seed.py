import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


def get_db_connection():
    """Establish and return a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def ingest_mock_data():
    """Insert a test location and event into the PostgreSQL database."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Insert a mock location
        cur.execute("""
                    INSERT INTO locations (name, address, latitude, longitude)
                    VALUES (%s, %s, %s, %s) RETURNING location_id;
                    """, ("York Community Stadium", "Kathryn Avenue, York", 53.983, -1.045))

        location_id = cur.fetchone()['location_id']
        print(f"Created location with ID: {location_id}")

        # 2. Insert a mock event for this location
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=3)

        cur.execute("""
                    INSERT INTO events (location_id, title, category, start_time, end_time, estimated_attendance)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING event_id;
                    """, (location_id, "Local Football Match", "sports", start_time, end_time, 8500))

        event_id = cur.fetchone()['event_id']
        print(f"Ingested event '{event_id}' for location '{location_id}'")

        # Commit the transaction
        conn.commit()
        print("Mock data ingested successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Database error occurred: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    ingest_mock_data()
