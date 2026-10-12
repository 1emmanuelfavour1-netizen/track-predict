import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)


def get_routine_rushes(target_date):
    """Generate static daily rushes based on the day of the week."""
    day_of_week = target_date.weekday()  # 0 = Monday, 4 = Friday, 5 = Saturday
    routines = []

    # 1. Lunchtime Rush (Every day)
    routines.append({
        "title": "City Centre Lunch Rush",
        "venue_name": "Commercial District",
        "start_time": target_date.replace(hour=12, minute=30, second=0, microsecond=0),
        "estimated_attendance": 2000,
        "rush_multiplier": 0.15  # High conversion for food places
    })

    # 2. Train Commuter Peak (Weekdays)
    if day_of_week < 5:
        routines.append({
            "title": "Evening Commute Peak",
            "venue_name": "York Train Station",
            "start_time": target_date.replace(hour=17, minute=0, second=0, microsecond=0),
            "estimated_attendance": 3500,
            "rush_multiplier": 0.08
        })

    # 3. Nightlife / Pub Closure Rush (Friday & Saturday nights)
    if day_of_week in [4, 5]:
        # Technically happens at 3 AM the *next* morning, but we track it as part of tonight's cycle
        next_day = target_date + timedelta(days=1)
        routines.append({
            "title": "Pubs & Clubs Closing",
            "venue_name": "Nightlife District (Micklegate/City Centre)",
            "start_time": next_day.replace(hour=3, minute=0, second=0, microsecond=0),
            "estimated_attendance": 1500,
            "rush_multiplier": 0.20  # Huge conversion for 24hr food
        })

    # 4. Weekend Shopping Peak
    if day_of_week in [5, 6]:
        routines.append({
            "title": "Weekend Retail Peak",
            "venue_name": "Designer Outlet / City Centre",
            "start_time": target_date.replace(hour=14, minute=0, second=0, microsecond=0),
            "estimated_attendance": 5000,
            "rush_multiplier": 0.10
        })

    return routines


def calculate_predicted_traffic():
    """Analyze dynamic events and routine schedules for the next 24 hours."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    now = datetime.now(timezone.utc)

    try:
        # Fetch dynamic events strictly within the next 24 hours
        cur.execute("""
                    SELECT e.title, e.start_time, e.estimated_attendance, l.name as venue_name
                    FROM events e
                             JOIN locations l ON e.location_id = l.location_id
                    WHERE e.start_time >= CURRENT_TIMESTAMP
                      AND e.start_time <= CURRENT_TIMESTAMP + INTERVAL '24 hours'
                    ORDER BY e.start_time ASC;
                    """)

        dynamic_events = cur.fetchall()
        routine_events = get_routine_rushes(now)

        # Combine database events with our daily routines
        all_events = dynamic_events + routine_events

        # Sort everything chronologically
        all_events.sort(key=lambda x: x['start_time'])

        print(f"\n--- 24-Hour Traffic Forecast (Generated {now.strftime('%H:%M')}) ---")

        if not all_events:
            print("No significant events or routines found for the next 24 hours.")
            return

        for event in all_events:
            title = event['title']
            venue = event['venue_name']
            start_time = event['start_time']
            attendance = event.get('estimated_attendance') or 1000

            # Use the defined multiplier for routines, or default to 5% for Ticketmaster events
            multiplier = event.get('rush_multiplier', 0.05)
            predicted_customers = int(attendance * multiplier)

            # Predict the rush happening 1 hour before the event start time
            rush_time = (start_time - timedelta(hours=1)).strftime('%H:%M')

            print(f"[{start_time.strftime('%a %H:%M')}] {title} @ {venue}")
            print(f"   -> Expected Rush: ~{predicted_customers} customers peaking around {rush_time}\n")

    except Exception as e:
        print(f"Database error occurred: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    calculate_predicted_traffic()