# Tanker Tracker

A real-time maritime surveillance dashboard tracking dark fleet vessels, sanctioned tankers, and live AIS vessel positions.

## Features

- **Live AIS Feed** - real-time vessel positions via aisstream.io, cross-referenced against sanctioned vessel lists
- **Dark Fleet** - 1,400+ vessels operating outside normal tracking (tankertrackers.com)
- **Lost & Found** - vessels seized by Iran or Houthi rebels, plus Iranian navy sightings
- **Sanctioned Vessels** - 1,380+ OFAC/EU sanctioned tankers with IMO cross-reference
- **Hourly refresh** - all data auto-updates from tankertrackers.com every hour

## Setup

1. Install dependencies: pip3 install websockets
2. Get a free API key at aisstream.io
3. Start the proxy: python3 proxy.py --key YOUR_API_KEY
4. Open tanker-tracker.html in your browser, go to Live AIS tab, click Connect

The proxy runs on ws://localhost:8765 (AIS stream) and http://localhost:8766 (hourly data refresh).

## Data Sources

- Dark Fleet: tankertrackers.com/report/darkfleetinfo
- Lost and Found: tankertrackers.com/report/lostandfound
- Sanctioned: tankertrackers.com/report/sanctioned
- Live AIS: aisstream.io

## Architecture

The browser connects to a local Python proxy which bridges two services. ws://localhost:8765 forwards live vessel positions from aisstream.io. http://localhost:8766 fetches dark fleet and sanctions data from tankertrackers.com hourly. The proxy keeps your API key server-side and handles CORS restrictions.
