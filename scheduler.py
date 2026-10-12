import time
import schedule
from event_api import ingest_live_events
from predictor import calculate_predicted_traffic

def run_pipeline():
    print(f"\n--- Running Track-Predict Pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    ingest_live_events()
    calculate_predicted_traffic()
    print("--- Pipeline execution complete ---\n")

# Run it immediately upon starting
run_pipeline()

# Schedule it to run daily at 3:00 AM
schedule.every().day.at("03:00").do(run_pipeline)

print("Track-Predict scheduler is active. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60) # Check the time every 60 seconds
