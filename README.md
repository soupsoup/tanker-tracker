# Tanker Tracker

A real-time maritime surveillance dashboard tracking dark fleet vessels, sanctioned tankers, and live AIS vessel positions.

## Features

- **Live AIS Feed** — real-time vessel positions via aisstream.io, cross-referenced against sanctioned vessel lists
- **Dark Fleet** — 1,400+ vessels operating outside normal tracking (tankertrackers.com)
- **Lost & Found** — vessels seized by Iran or Houthi rebels, plus Iranian navy sightings
- **Sanctioned Vessels** — 1,380+ OFAC/EU sanctioned tankers with IMO cross-reference
- **Hourly refresh** — all data auto-updates from tankertrackers.com every hour

## Setup

### 1. Install dependencies

    pip3 install websockets

### 2. Get an API key

Sign up at [aisstream.io](https://aisstream.io) for a free API key.

### 3. Start the proxy

    python3 proxy.py --key YOUR_AISSTREAM_API_KEY

The proxy runs on ws://localhost:8765 (AIS WebSocket) and http://localhost:8766 (data refresh API).

### 4. Open the dashboard

Open tanker-tracker.html in your browser, go to the Live AIS tab, and click Connect.

## Data Sources

| Tab | Source |
|-----|--------|
| Dark Fleet | tankertrackers.com/report/darkfleetinfo |
| Lost & Found | tankertrackers.com/report/lostandfound |
| Sanctioned | tankertrackers.com/report/sanctioned |
| Live AIS | aisstream.io |

## Architecture

The browser connects to a local Python proxy which bridges two services:

- ws://localhost:8765 forwards to wss://stream.aisstream.io (live vessel positions)
- http://localhost:8766/data/* fetches from tankertrackers.com (dark fleet and sanctions data)

The proxy keeps your API key server-side and handles CORS restrictions from file:// origins.
