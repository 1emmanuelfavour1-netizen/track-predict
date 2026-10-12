# Track-Predict 📍

A full-stack data ingestion pipeline and predictive engine that forecasts local customer foot traffic rushes based on dynamic live events and static city routines. Built to help local businesses anticipate staffing needs.

## System Architecture

*   **Data Ingestion (Python):** Automatically fetches live event data via the Ticketmaster Discovery API.
*   **Database (PostgreSQL):** Stores relational data across `locations` and `events` tables, enforcing strict schema constraints.
*   **Predictive Engine (Python/FastAPI):** A rules-based engine that merges live event capacity with scheduled daily routines (lunch breaks, commutes, nightlife) to calculate expected customer surges.
*   **Frontend (Next.js & Tailwind CSS):** A responsive, dark-mode dashboard visualizing the 24-hour traffic timeline.
*   **Automation:** Utilizes Python's `schedule` library to run daily database updates.

## Tech Stack
*   **Backend:** Python 3.9, FastAPI, psycopg2, requests
*   **Database:** PostgreSQL
*   **Frontend:** React, Next.js, Tailwind CSS, TypeScript

## How to Run Locally

1. Clone the repository and install dependencies for both the Python backend and Next.js frontend.
2. Create a local PostgreSQL database named `trackpredict` and run `src/db/schema.sql`.
3. Create a `.env` file with your database credentials and Ticketmaster API Key.
4. Run `uvicorn api:app --reload` to start the backend.
5. Run `npm run dev` in the `track-predict-web` directory to start the frontend.
