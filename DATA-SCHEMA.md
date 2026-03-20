# Bullet R1 Data Schema & Control Reference

> Reverse-engineered from RoasTime 2 (v3.4.1) local data store.
> Based on analysis of 2,196 roast records + 24 recipes.
> Last updated: 2026-03-20

---

## 1. Controls (Inputs)

Bullet R1 has exactly **three control parameters**, each with a **0–9 range** (10 steps).

### Real-time Controls (`actions.actionTimeList`)

| Field      | ctrlType | Range | Description |
|------------|----------|-------|-------------|
| **Power**  | `0`      | 0–9   | Heating element power level |
| **Fan**    | `1`      | 0–9   | Fan / airflow speed |
| **Drum**   | `2`      | 0–9   | Drum rotation speed |

Each action entry:
```json
{
  "ctrlType": 0,
  "index": 107,
  "value": 6
}
```
- `index`: seconds from roast start
- `value`: new control level (0–9)

> **Note:** `actions.actionTempList` exists in the schema but has never been populated (0/2196 roasts).

---

### Recipe Start Settings (`startSettings`)

Initial P/F/D values when a roast begins:

| Key     | Observed Range |
|---------|---------------|
| `power` | 0–9 (you used: 0, 3, 4, 6, 7, 8, 9) |
| `drum`  | 0–9 (you used: 3, 4, 5, 6, 8, 9) |
| `fan`   | 0–9 (you used: 1, 2, 3) |

---

### Recipe Automation (Events)

Recipes define automated control changes triggered by conditions:

**Trigger types:**
| trigger | Condition |
|---------|-----------|
| `0`     | Bean temperature threshold (°C) |
| `3`     | Elapsed time from roast start (seconds) |

**Action types (same as ctrlType):**
| action | Control |
|--------|---------|
| `0`    | Power |
| `1`    | Fan |
| `2`    | Drum |

---

## 2. Collected Data

### Scalar Fields (per roast)

| Field | Coverage | Unit | Description |
|-------|----------|------|-------------|
| `dateTime` | 100% | ms (Unix) | Roast timestamp |
| `totalRoastTime` | 100% | seconds | Total roast duration |
| `roastStartIndex` | 100% | seconds | Start offset in time-series |
| `roastEndIndex` | 100% | seconds | End offset in time-series |
| `sampleRate` | 100% | Hz | Data sampling rate (always 2) |
| `preheatTemperature` | 100% | °C | Drum temp at charge |
| `beanChargeTemperature` | 100% | °C | Bean temp at charge (IBTS) |
| `beanDropTemperature` | 100% | °C | Bean temp at drop (IBTS) |
| `drumChargeTemperature` | 100% | °C | Drum temp at charge |
| `drumDropTemperature` | 100% | °C | Drum temp at drop |
| `rorPreheat` | 94% | °C/min | Rate of rise during preheat |
| `indexFirstCrackStart` | 100% | seconds | First crack start (0 = not marked) |
| `indexFirstCrackEnd` | 100% | seconds | First crack end |
| `indexSecondCrackStart` | 100% | seconds | Second crack start |
| `indexSecondCrackEnd` | 100% | seconds | Second crack end |
| `indexYellowingStart` | 100% | seconds | Yellowing point (Maillard start) |
| `weightGreen` | 100% | g | Green bean weight (0 = not filled) |
| `weightRoasted` | 100% | g | Roasted weight (0 = not filled) |
| `roastNumber` | 100% | count | Machine lifetime roast counter |
| `serialNumber` | 100% | — | Machine serial number |
| `firmware` | 100% | — | Firmware version code |
| `firmwareVersion` | 100% | — | Firmware version (same as above) |
| `softwareVersion` | 100% | — | RoasTime app version |
| `hardware` | 100% | — | Hardware version code |
| `IRSensor` | 100% | — | IR sensor type (2 = IBTS) |
| `recipeID` | 95% | — | Recipe used (references recipes/) |
| `roastName` | 37% | string | Optional user-assigned name |
| `ambient` | 29% | °C | Ambient temperature |
| `humidity` | 29% | % | Ambient humidity |
| `updatedAt` | 29% | ms (Unix) | Last sync timestamp |
| `inventory` | 13% | — | Bean inventory reference |
| `roastDegree` | 2% | string | Manual roast degree label |
| `hasError` | 1% | bool | Error flag |
| `rating` | 0% | — | User rating (field exists, never used) |
| `comments` | 0% | — | User comments (field exists, never used) |
| `uid` | 100% | string | Roast unique ID |
| `userId` | 100% | string | Firebase user ID |

---

### Time-Series Fields (arrays, sampled at `sampleRate` = 2 Hz)

Each array has one value per 0.5 seconds. Length = `totalRoastTime × sampleRate`.

| Field | Coverage | Unit | Description |
|-------|----------|------|-------------|
| `beanTemperature` | 100% | °C | Bean temperature (IBTS) over time |
| `drumTemperature` | 100% | °C | Drum temperature over time |
| `beanDerivative` | 100% | °C/min | Bean RoR (Rate of Rise) over time |
| `ibtsDerivative` | 100% | °C/min | IBTS RoR (same sensor, different smoothing) |
| `exitTemperature` | 100% | °C | Exhaust/exit temperature over time |
| `missingSeconds` | 100% | — | Indexes with missing data (usually empty) |

> Index into any time-series array: `second × sampleRate` (e.g. second 60 → index 120)

---

## 3. Derived Metrics (calculable from raw data)

| Metric | Formula |
|--------|---------|
| Weight loss % | `(weightGreen - weightRoasted) / weightGreen × 100` |
| Development time | `(roastEndIndex - indexFirstCrackStart) / sampleRate` seconds |
| DTR % | `developmentTime / totalRoastTime × 100` |
| Turning point temp | `min(beanTemperature[roastStartIndex:])` |
| Turning point time | `argmin(beanTemperature) / sampleRate` seconds |
| Maillard duration | `(indexFirstCrackStart - indexYellowingStart) / sampleRate` seconds |
| Avg RoR | `mean(beanDerivative[roastStartIndex:roastEndIndex])` |
| Peak RoR | `max(beanDerivative[roastStartIndex:roastEndIndex])` |

---

## 4. Storage & Infrastructure

```
~Library/Application Support/roast-time/
├── roasts/          # One JSON file per roast (filename = uid)
├── recipes/         # 24 automation recipes
├── indexes/         # LokiJS index (index.db, ASCII JSON)
├── configs/         # App config (OFFLINE = local, or user-id)
├── users/           # Firebase anonymous auth token
├── device/          # Connected roaster metadata (nanoid-based device ID)
├── sync/            # Firebase sync state
└── logs/            # App logs
```

---

## 5. Application Architecture (Electron Layer)

> Reverse-engineered from `app.asar` (RoasTime v4.6.16, main=`dist/index.js`)

### Process Topology

```
Electron main process (dist/index.js)
│
├── spawns → roastime-backend-mac-x64 --port {randomPort}
│               ↕ WebSocket: ws://localhost:{backendPort}
│
└── spawns → roastime-comms-mac-x64 --port {randomPort}
                ↕ WebSocket: ws://localhost:{commsPort}/usb
```

Both backend and comms ports are **dynamically assigned** via `get-port-please`.

### How Frontend Gets Ports

```javascript
// Electron main exposes via IPC:
ipcMain.handle('get-ports', () => {
    frontend.webContents.send('websocket-ports', {
        backend: `ws://localhost:${backendPort}`,
        comms:   `ws://localhost:${commsPort}/usb`
    })
})

// Frontend (renderer) calls:
window.electronAPI.getPorts((event, { backend, comms }) => {
    // connect to both WebSocket endpoints
})
```

### IPC Channels (Electron main ↔ renderer)

| Channel | Direction | Description |
|---------|-----------|-------------|
| `get-ports` | renderer → main (invoke) | Request backend + comms port |
| `websocket-ports` | main → renderer (send) | Returns `{ backend, comms }` URLs |
| `update-versions` | renderer → main (invoke) | Report frontend version info |
| `download-logs` | renderer → main (invoke) | Trigger log download |
| `force-install-dependencies` | renderer → main (invoke) | Force re-install deps |
| `update-log-config` | renderer → main (invoke) | Update logging config |
| `on-roast-world-close` | main → renderer (send) | RoastWorld window closed |
| `on-new-versions` | main → renderer (send) | New version available |
| `on-update-start` | main → renderer (send) | Update download started |
| `on-update-finish` | main → renderer (send) | Update complete |

### WebSocket Endpoints

| Endpoint | Purpose |
|----------|---------|
| `ws://localhost:{backendPort}` | Data store, Firebase sync, recipe management, roast history |
| `ws://localhost:{commsPort}/usb` | Real-time device: temperature stream, P/F/D control, device state |

> **Note:** WebSocket message schemas are defined in the frontend SPA (separate repo, not in app.asar).
> To discover full message formats: intercept localhost WS traffic with Charles/Proxyman while running RoasTime.

### External API

```
Base URL: https://api.roast.world/api/v3

Endpoints used by Electron main:
  GET /identity/updates/roastime-{frontend|backend|comms}/{platform}/{userId}
  GET /updates/roastime-{frontend|backend|comms}/{platform}/{cohort}
  GET /bins/download/roastime-{frontend|backend|comms}/{platform}/{version}
```

### USB Device Identifiers

From Windows driver installer (`wdi-simple.exe`):

| Model | VID | PID |
|-------|-----|-----|
| Bullet R1 (current) | `0x0483` | `0xA27E` |
| Bullet R1 (old firmware) | `0x0483` | `0x5741` |

Vendor `0x0483` = STMicroelectronics (STM32 USB HID).

### Firmware URLs

```
https://roaster-firmware.s3-ap-northeast-1.amazonaws.com/bulletR1{version}.json?timestamp={ts}
https://roaster-firmware.s3-ap-northeast-1.amazonaws.com/MainProgram{version}.bin?timestamp={ts}
```

### GitHub Org

`https://github.com/roastworld` — Aillio's org.
Repos `roastime-backend` and `roastime-comms` are **private**.
Only `roastime-release` is public (update manifest only).
