# wound-infection-risk

## Overview
`wound-infection-risk` is a local-first MVP for *risk estimation / triage support* based on wound images. The iPhone app captures or uploads a photo, calls a local FastAPI backend, and returns a **risk score** with a plain-language explanation of visual cues. **It does not diagnose infection and does not provide treatment instructions.**

### What it is
- A visual risk estimation tool intended for **triage support and monitoring**.
- A local-network workflow: iOS app + FastAPI backend running on a Mac or small server.
- A transparent, heuristic baseline model that explains its signals.

### What it is not
- Not a medical device.
- Not a diagnostic system.
- Not a substitute for clinical care.

## Safety disclaimer (read first)
This application provides **non-diagnostic risk estimation** only. It cannot diagnose infection, prescribe treatment, or replace professional medical evaluation. If you have concerns about a wound, consult a qualified clinician.

The UI, API responses, and documentation repeat this disclaimer intentionally.

## Architecture

```
[ iPhone App (SwiftUI) ]
         |
         |  HTTP (local network)
         v
[ FastAPI Backend ] ---> [ Heuristic Feature Pipeline ] ---> [ Risk Score + Explanation ]
```

## Heuristic model (baseline)
The backend uses OpenCV-based heuristic signals:
- **Periwound redness**: red hue ratio in a ring surrounding the wound region.
- **Exudate proxy**: yellow/green pixels within the wound region.
- **Dark tissue proxy**: dark pixel clusters in the wound region.
- **Swelling proxy**: edge density in the periwound ring.

The features are combined with configurable weights in `backend/config/weights.yaml` and a simple linear scoring function. Explanations are generated from the top-weighted signals.

## API

## Web app
The FastAPI backend also serves a lightweight web UI that mirrors the iOS experience, including settings, image upload, and results visualization. Start the backend and open:

```
http://localhost:8000
```

### `GET /health`
Returns a simple status JSON.

**Example:**
```bash
curl http://localhost:8000/health
```

Response:
```json
{ "status": "ok" }
```

### `POST /assess`
Multipart upload with a single image file.

**Example:**
```bash
curl -F "file=@samples/sample-wound.png" http://localhost:8000/assess
```

Response:
```json
{
  "risk_score": 0.54,
  "risk_level": "medium",
  "signals": [
    {"name": "periwound_redness", "value": 0.42, "weight": 0.35, "note": "..."},
    {"name": "exudate_proxy", "value": 0.31, "weight": 0.25, "note": "..."},
    {"name": "dark_tissue_proxy", "value": 0.12, "weight": 0.25, "note": "..."},
    {"name": "swelling_proxy", "value": 0.09, "weight": 0.15, "note": "..."}
  ],
  "explanation": "Estimated risk level: medium...",
  "disclaimer": "This output is a non-diagnostic risk estimation...",
  "recommended_next_steps": [
    "Continue monitoring and recheck if the appearance changes.",
    "Seek clinical advice if you are concerned about progression."
  ]
}
```

## iPhone app setup
### Prerequisites
- macOS with Xcode 15+
- iOS 17+ device or simulator

### Running in the simulator
1. Open `ios/WoundInfectionRisk/WoundInfectionRisk.xcodeproj` in Xcode.
2. Select an iPhone simulator.
3. Run the app.
4. Start the backend (see below) and copy the LAN IP printed in the backend logs into the Settings screen.

### Running on a real device
1. Open the project in Xcode.
2. Select your device and sign with your Apple ID.
3. Ensure your Mac and iPhone are on the same Wi-Fi network.
4. Start the backend and paste the LAN IP into the app settings.

## App Transport Security (ATS)
iOS blocks HTTP by default. For **local development only**, configure `Info.plist` to allow local networking:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

Alternatively, you can use `NSAllowsLocalNetworking` on iOS 14+ for tighter scope. **Do not ship production apps with relaxed ATS rules.**

## Backend setup
### Requirements
- Python 3.10+

### Installation
```bash
make setup
```

### Run locally
```bash
make run-backend
```

On startup, the backend prints:
```
Backend running. iPhone app can connect at: http://<LAN-IP>:8000
```

### Run tests
```bash
make test-backend
```

## Docker (optional)
```bash
docker compose up --build
```

## Roadmap
- Longitudinal wound tracking + trend analysis
- Clinical calibration with real-world data
- Robustness across lighting conditions and skin tones
- Evaluation pipeline with labeled data
- On-device model packaging via CoreML
