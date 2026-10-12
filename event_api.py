import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load credentials
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
TM_API_KEY = os.getenv("TICKETMASTER_API_KEY")


def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)


def fetch_york_events():
    """Fetch live event data from Ticketmaster for York, UK."""
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TM_API_KEY,
        "city": "York",
        "countryCode": "GB",
        "size": 10,  # Fetch the next 10 events
        "sort": "date,asc"  # Sort by chronological order
    }

    print("Fetching live events from Ticketmaster...")
    response = requests.get(url, params=params)
    response.raise_for_status()

    # Extract the events array from the JSON response
    return response.json().get("_embedded", {}).get("events", [])


def ingest_live_events():
    """Parse API data and UPSERT into PostgreSQL."""
    events_data = fetch_york_events()
    if not events_data:
        print("No events found.")
        return

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        for event in events_data:
            # 1. Extract Venue (Location) Data
            venues = event.get("_embedded", {}).get("venues", [{}])
            venue = venues[0]
            venue_name = venue.get("name", "Unknown Venue")
            address = venue.get("address", {}).get("line1", "Unknown Address")

            # Safely get coordinates (some venues lack them)
            location = venue.get("location", {})
            lat = location.get("latitude")
            lon = location.get("longitude")

            # UPSERT Location: Check if it exists, if not, insert
            cur.execute("SELECT location_id FROM locations WHERE name = %s", (venue_name,))
            loc_row = cur.fetchone()

            if loc_row:
                location_id = loc_row['location_id']
            else:
                cur.execute("""
                            INSERT INTO locations (name, address, latitude, longitude)
                            VALUES (%s, %s, %s, %s) RETURNING location_id;
                            """, (venue_name, address, lat, lon))
                location_id = cur.fetchone()['location_id']

            # 2. Extract Event Data
            title = event.get("name")
            # Dig into nested classifications for category
            category = event.get("classifications", [{}])[0].get("segment", {}).get("name", "General")

            start_time_str = event.get("dates", {}).get("start", {}).get("dateTime")
            if not start_time_str:
                continue  # Skip events that haven't announced a strict time

            # Convert ISO string to Python datetime
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))

            # Ticketmaster Discovery API rarely provides an end time, so we default to 3 hours later
            end_time = start_time + timedelta(hours=3)

            # Ticketmaster doesn't expose attendance capacity for free, so we mock it for the predictor
            estimated_attendance = 1000

            # UPSERT Event: Check if it exists based on location, title, and time
            cur.execute("""
                        SELECT event_id
                        FROM events
                        WHERE location_id = %s
                          AND title = %s
                          AND start_time = %s
                        """, (location_id, title, start_time))

            evt_row = cur.fetchone()
            if evt_row:
                print(f"Skipping duplicate: '{title}' at {venue_name}")
            else:
                cur.execute("""
                            INSERT INTO events (location_id, title, category, start_time, end_time,
                                                estimated_attendance)
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING event_id;
                            """, (location_id, title, category, start_time, end_time, estimated_attendance))
                print(f"Successfully ingested: '{title}' at {venue_name}")

        conn.commit()
        print("\nAPI Ingestion complete. Database updated.")

    except Exception as e:
        conn.rollback()
        print(f"Database error occurred: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    ingest_live_events()
