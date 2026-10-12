import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Track-Predict API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )


def get_routine_rushes(target_date):
    day_of_week = target_date.weekday()
    routines = []

    routines.append({
        "title": "City Centre Lunch Rush",
        "venue_name": "Commercial District",
        "start_time": target_date.replace(hour=12, minute=30, second=0, microsecond=0),
        "estimated_attendance": 2000,
        "rush_multiplier": 0.15
    })

    if day_of_week < 5:
        routines.append({
            "title": "Evening Commute Peak",
            "venue_name": "York Train Station",
            "start_time": target_date.replace(hour=17, minute=0, second=0, microsecond=0),
            "estimated_attendance": 3500,
            "rush_multiplier": 0.08
        })

    if day_of_week in [4, 5]:
        next_day = target_date + timedelta(days=1)
        routines.append({
            "title": "Pubs & Clubs Closing",
            "venue_name": "Nightlife District (Micklegate/City Centre)",
            "start_time": next_day.replace(hour=3, minute=0, second=0, microsecond=0),
            "estimated_attendance": 1500,
            "rush_multiplier": 0.20
        })

    if day_of_week in [5, 6]:
        routines.append({
            "title": "Weekend Retail Peak",
            "venue_name": "Designer Outlet / City Centre",
            "start_time": target_date.replace(hour=14, minute=0, second=0, microsecond=0),
            "estimated_attendance": 5000,
            "rush_multiplier": 0.10
        })

    return routines


@app.get("/api/forecast")
def get_forecast():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    now = datetime.now(timezone.utc)

    try:
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

        all_events = dynamic_events + routine_events
        all_events.sort(key=lambda x: x['start_time'])

        results = []
        for event in all_events:
            title = event['title']
            venue = event['venue_name']
            start_time = event['start_time']
            attendance = event.get('estimated_attendance') or 1000
            multiplier = event.get('rush_multiplier', 0.05)

            predicted_customers = int(attendance * multiplier)
            rush_time = (start_time - timedelta(hours=1)).strftime('%H:%M')

            results.append({
                "event_title": title,
                "venue": venue,
                "start_time": start_time.strftime('%a %H:%M'),
                "predicted_customers": predicted_customers,
                "peak_rush_time": rush_time
            })

        return {"status": "success", "data": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
        conn.close()
