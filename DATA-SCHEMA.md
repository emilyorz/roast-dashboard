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

---

## 6. Legacy Architecture (RoasTime v2.x — currently in use)

> The version actively used for roasting is the **older v2.5.5-alpha** (`/Applications/RoasTime.app`, 2022).
> It uses a completely different architecture from v4.x described above.

### Key Difference

| | v4.x (RoasTime 2.app) | v2.x (RoasTime.app) |
|--|----------------------|----------------------|
| Backend | Separate `roastime-backend-mac-x64` process | Embedded in Electron main via webpack |
| Comms | Separate `roastime-comms-mac-x64` (Go) | Native node addon (`node.napi.node`) |
| IPC | WebSocket (`ws://localhost:{port}`) | Electron IPC: `window.webContents.send("usb", data)` |
| Size | 98MB asar | 48MB asar |

### USB IPC (v2.x)

USB data is read in the main process and pushed directly to renderer:
```javascript
window.webContents.send("usb", data)  // main → renderer
```

No localhost ports open — all device communication is in-process.

### Firebase Collections (v2.x config)

| Key | Firestore Collection |
|-----|---------------------|
| configs | `configs` |
| roasts | `roast_tmp` |
| syncs | `syncs` |
| recipes | `recipes` |
| userBeans | `user_beans` |
| beans | `beans` |
| downloads | `roast_downloads` |
| registers | `roaster_register` |
| notifications | `notifications` |
| recipeDownloads | `recipe_downloads` |
| containerGroups | `containerGroups` |
| containers | `containers` |

### API Endpoints (v2.x)

| Name | URL |
|------|-----|
| Identity API | `https://id.aillio.com` |
| RoastWorld API | `https://api.roast.world` |
| RT API (legacy) | `http://209.97.168.64/` |
| Firebase Project | `testaillio` (firebaseapp.com) |
| Firmware release log | `https://roaster-firmware.s3.ap-northeast-1.amazonaws.com/FirmwareReleaseLog.txt` |
| Release notes | `https://raw.githubusercontent.com/roastworld/roast-time/master/release-notes.json` |

---

## 7. USB Protocol (v2.x — Full Byte-Level Specification)

> Reverse-engineered from `bg_window/index.js` (webpack bundle, TypeScript source).
> USB library: `node-usb` (not native NAPI). Interface index: `1`. Endpoints: IN + OUT (bulk transfer).

### Device Identification

```
AILLIO_VENDOR_IDS  = [0x0483]          // STMicroelectronics
AILLIO_PRODUCT_IDS = [0x5741, 0xA27E]  // Old firmware, Current firmware
```

Try `0x5741` first, then `0xA27E`. USB interface `[1]`, claim and detach kernel driver (non-Windows).

### Packet Format

All packets are **fixed 64 bytes** (except device info which is 32 bytes).

- **Send**: `deviceOutEndpoint.transfer(buffer, callback)`
- **Receive**: `deviceInEndpoint.transfer(N_bytes, callback)`, timeout = 5000ms

### Valid Data Check

Before parsing Payload A, validate:
```javascript
data[62] == 0xFF && data[63] == 0xAA && data[41] == 0x0A
```

### USB Session Lifecycle

```
1. CONNECT
   usb.findByIds(0x0483, 0x5741) || usb.findByIds(0x0483, 0xA27E)
   device.open()
   device.interfaces[1].detachKernelDriver()  // non-Windows only
   device.interfaces[1].claim()
   deviceInEndpoint  = find endpoint direction=="in"
   deviceOutEndpoint = find endpoint direction=="out"
   deviceInEndpoint.timeout = 5000

2. INITIALIZE (first poll cycle only, when serialNumber == 0)
   clearBuffer()          → CLEAR_BUFFER [0x30, 0x05]
   getDeviceData()        → GET_DEVICE_DATA [0x30, 0x02], read 32 bytes → parse serial/hardware/firmware
   getDeviceUsage()       → GET_DEVICE_USAGE [0x89, 0x01], read 36 bytes → parse usage stats
   if firmwareVersion > 999: retry (invalid response)

3. STEADY-STATE POLL (every 350ms)
   blueprint = Parser.blueprint()     // empty default object
   send PAYLOAD_PART_A [0x30, 0x01]  // NOT [0x30, 0x99]
   read 64 bytes → validate → setLogPayloadA()
   send PAYLOAD_PART_B [0x30, 0x03]
   read 64 bytes → setLogPayloadB()
   if blueprint.validData: push MSG_TYPE.RoastData via IPC

4. DISCONNECT
   deviceInterface.release()
   connectedDevice.close()
```

> **重要**：實際輪詢 Payload A 用的是 `PAYLOAD_PART_A [0x30, 0x01]`，不是 `GET_ROASTER_STATUS [0x30, 0x99]`。
> `GET_ROASTER_STATUS` 只在 firmware update bootloader 流程中使用。

### Poll Loop

Runs every **350ms**. Each cycle:
1. Send `PAYLOAD_PART_A [0x30, 0x01]` → receive **Payload A** (64 bytes)
2. Send `PAYLOAD_PART_B [0x30, 0x03]` → receive **Payload B** (64 bytes)

---

### Command Packets (Send → Device)

| Command | Hex Bytes | Description |
|---------|-----------|-------------|
| `GET_ROASTER_STATUS` | `[0x30, 0x99]` | Request real-time status (Payload A) |
| `PAYLOAD_PART_A` | `[0x30, 0x01]` | Request Payload A (alt) |
| `PAYLOAD_PART_B` | `[0x30, 0x03]` | Request extended data (Payload B) |
| `GET_DEVICE_DATA` | `[0x30, 0x02]` | Request device info (32 bytes) |
| `GET_DEVICE_USAGE` | `[0x89, 0x01]` | Request usage counters (36 bytes) |
| `CLEAR_BUFFER` | `[0x30, 0x05]` | Flush device buffer |
| `PSR_BUTTON_COMMAND` | `[0x30, 0x01, 0x00, 0x00]` | Simulate PSR button |
| `SET_DRUM_SPEED` | `[0x32, 0x01, setting, 0x00]` | Set drum speed (0–9) |
| `SET_BLOWER_SETTING` | `[0x31, 0x00, setting, 0x00]` | Set fan/blower (0–9) |
| `SET_FAN_SPEED` | `[0x31, fanId, setting, 0x00]` | fanId: 0x00=fan1, 0x03=fan2 |
| `SET_INDUCTION_POWER` | `[0x34, 0x00, setting, 0xBA]` | Set power level (0–9) |
| `POWER_INCREMENT_SETTING` | `[0x34, 0x01, 0xAA, 0xAA]` | Power +1 |
| `POWER_DECREMENT_SETTING` | `[0x34, 0x02, 0xAA, 0xAA]` | Power -1 |
| `BLOWER_INCREMENT_SETTING` | `[0x31, 0x01, 0xAA, 0xAA]` | Fan +1 |
| `BLOWER_DECREMENT_SETTING` | `[0x31, 0x02, 0xAA, 0xAA]` | Fan -1 |
| `SET_PREHEAT_SETPOINT` | `[0x35, 0x00, setting>>8, setting]` | Preheat target temp |
| `SET_BUZZER` | `[0x38, 0x00, setting>>8, setting]` | Buzzer control |
| `SET_BLINK` | `[0x39, 0x00, 0x01/0x00, 0x00]` | LED blink on/off |
| `RESET_USB` | `[0x4A, 0x01]` | Reset USB connection |
| `RESET_ROASTER` | `[0x20, 0xFF]` | Full roaster reset |

**settingCommand() mapping (from UI string → USB command):**
```
"power-setting"    → SET_INDUCTION_POWER
"drum-setting"     → SET_DRUM_SPEED
"fan-setting"      → SET_BLOWER_SETTING
"power-up"         → POWER_INCREMENT_SETTING
"power-down"       → POWER_DECREMENT_SETTING
"fan-up"           → BLOWER_INCREMENT_SETTING
"fan-down"         → BLOWER_DECREMENT_SETTING
"preheat-setpoint" → SET_PREHEAT_SETPOINT
"blink"            → SET_BLINK
"buzz"             → SET_BUZZER
```

---

### Response Payload A (64 bytes) — Real-Time Data

> `getFloat(data, offset)` = `Float32Array` from 4 bytes LE

| Offset | Length | Type | Field | Description |
|--------|--------|------|-------|-------------|
| 0 | 4 | float32 LE | `beanTemp` | Bean temperature (IBTS) °C |
| 4 | 4 | float32 LE | `beanRise` | Bean RoR (rate of rise) °C/min |
| 8 | 4 | float32 LE | `drumTemp` | Drum temperature °C |
| 12 | 4 | float32 LE | `ibtsRise` | IBTS RoR °C/min |
| 16 | 4 | float32 LE | `exitTemp` | Exhaust/exit temperature °C |
| 20 | 4 | uint32 LE | `buttons` | Button bitmask (bit 31 = crack button) |
| 24 | 1 | uint8 | `minutes` | Elapsed roast time (minutes) |
| 25 | 1 | uint8 | `seconds` | Elapsed roast time (seconds) |
| 26 | 1 | uint8 | `blowerSetting` | Current fan setting (0–9) |
| 27 | 1 | uint8 | `inductionPowerSetting` | Current power setting (0–9) |
| 28 | 1 | uint8 | `drumSetting` | Current drum speed (0–9) |
| 29 | 1 | uint8 | `stateMachine` | Roaster state — **confirmed 1 byte** (`blueprint.stateMachine = data[29]`) |
| 30 | 2 | uint16 LE | `sampleNumber` | Sequential sample counter (`data[30] \| (data[31] << 8)`) |
| 32 | 4 | float32 LE | `ambientTemp` | Ambient temperature °C |
| 36 | 4 | float32 LE | `ambientIRTemp` | Ambient IR temperature °C |
| 41 | 1 | uint8 | *(valid flag)* | Must be `0x0A` for valid data |
| 42 | 2 | uint16 LE | `samplesInFIFO` | Samples queued in device FIFO |
| 44 | 2 | uint16 LE | `blowerRPM` | Blower motor RPM |
| 48 | 2 | uint16 LE | `inputVoltage` | Input voltage |
| 52 | 2 | uint16 LE | `coilRPM` | Induction coil RPM |
| 54 | 2 | uint16 LE | `errorCodes` | Error code flags |
| 60 | 1 | uint8 | `crc` | CRC byte (algorithm unspecified, not validated in source) |
| 61 | 1 | — | *(reserved/unused)* | Not read by parser |
| 62 | 1 | uint8 | *(valid flag)* | Must be `0xFF` |
| 63 | 1 | uint8 | *(valid flag)* | Must be `0xAA` |

**Known gaps in Payload A** (bytes not referenced in parser):
- byte 40: unknown / reserved
- bytes 46–47: unknown / reserved
- bytes 50–51: unknown / reserved
- bytes 56–59: unknown / reserved
- byte 61: unknown / reserved

These may contain additional sensor data in newer firmware versions or be padding. Recommend capturing a real hex dump to confirm.

---

### Response Payload B (64 bytes) — Extended Data

| Offset | Length | Type | Field | Description |
|--------|--------|------|-------|-------------|
| 0 | 4 | float32 LE | `beanSoundEnergy` | Acoustic energy (crack detection) |
| 4 | 4 | float32 LE | `beanSoundBaseline` | Acoustic baseline |
| 8 | 4 | float32 LE | `rorPreheat` | RoR during preheat phase |
| 24 | 2 | uint16 LE | `errorCode1` | Error code 1 |
| 26 | 2 | uint16 LE | `errorValue1` | Error value 1 |
| 28 | 2 | uint16 LE | `errorCode2` | Error code 2 |
| 30 | 2 | uint16 LE | `errorValue2` | Error value 2 |
| 32 | 2 | uint16 LE | `coilRPMFan2` | Fan 2 coil RPM |
| 34 | 2 | uint16 LE | `currentTest` | Current sensor reading |
| 36 | 1 | uint8 | `IGBTTemperature` | IGBT heatsink temp |
| 37 | 1 | uint8 | `IGBT2Temperature` | IGBT 2 temp |
| 38 | 2 | uint16 LE | `timerPeriod` | Timer period for freq calc (`IGBTFrequency = 40000000 / timerPeriod`) |
| 40 | 2 | uint16 LE | `pHTemperatureSetting` | pH temperature setting |
| 42 | 2 | uint16 LE | `IRFanRPM` | IR sensor fan RPM |

---

### Response: GET_DEVICE_DATA (32 bytes)

| Offset | Length | Type | Field |
|--------|--------|------|-------|
| 0 | 4 | uint32 LE | `serialNumber` |
| 4 | 1 | uint8 | `yearManufacturing` |
| 5 | 1 | uint8 | `monthManufacturing` |
| 6 | 1 | uint8 | `dayManufacturing` |
| 7 | 1 | uint8 | `hourManufacturing` |
| 8 | 4 | uint32 LE | `hardwareVersion` |
| 10 | 1 | uint8 | `IRSensor` (within hardwareVersion bytes) |
| 12 | 4 | uint32 LE | `uniqueID1` (hex string) |
| 16 | 4 | uint32 LE | `uniqueID2` |
| 20 | 4 | uint32 LE | `uniqueID3` |
| 24 | 4 | uint32 LE | `firmwareVersion` |
| 28 | 4 | uint32 LE | `crc` |

---

### State Machine Values (`stateMachine` byte 29)

| Value | State | Description |
|-------|-------|-------------|
| `0x0000` | STARTUP | Idle / startup |
| `0x0002` | PREHEATING | Preheat phase (also 0x0003, 0x0023, 0x0024) |
| `0x0003` | PREHEATING | — |
| `0x0004` | CHARGE | Bean charge |
| `0x0006` | ROASTING | Active roast |
| `0x0008` | COOLING | Cooling cycle |
| `0x0009` | COOLDOWN | Cooldown |
| `0x0023` | PREHEATING | — |
| `0x0024` | PREHEATING | — |

**Software State enum:**
```
-1 = ISSUE
 0 = CONNECTED
 1 = STARTUP
 2 = PREHEATING
 3 = CHARGE
 4 = ROASTING
 5 = COOLING
 6 = COOLDOWN
 7 = OFFLINE
```

---

### IPC Handler Commands (Renderer → bg_window)

The renderer sends requests to bg_window via node-ipc. Supported handler names:

| Handler name | Payload | Action |
|-------------|---------|--------|
| `prs` | — | Simulate PSR button press |
| `preheat` | `{ settingType, settingValue }` | Set preheat setpoint (settingType="preheat") |
| `setting` | `{ settingType, settingValue }` | Direct set: "power"/"fan"/"drum"-setting |
| `setting-up` | `{ settingType, settingValue }` | Increment: "power"/"fan"/"drum"-up |
| `setting-down` | `{ settingType, settingValue }` | Decrement: "power"/"fan"/"drum"-down |
| `roast-meta` | `{ userId, roastId, ... }` | Set logger metadata for active roast |
| `state` | — | Query current device state (returns state object) |

### Error Handling

Error codes are numeric (uint16). Values 1–10 trigger `hasError = true` in the roast record.
No enum/map of error code meanings found in source — error codes are stored raw.

### IPC Transport (bg_window ↔ renderer)

bg_window uses `node-ipc` Unix socket server. Messages are JSON:

**Push (device → UI):**
```json
{ "type": "push", "name": "<MSG_TYPE>", "args": { ... } }
```

**Request/Reply:**
```json
// Request:  { "type": "message", "id": "<uuid>", "name": "<handler>", "args": { ... } }
// Reply:    { "type": "reply", "id": "<uuid>", "result": { ... } }
// Error:    { "type": "error", "id": "<uuid>", "args": { "error": "..." } }
```

**MSG_TYPE events:**

| Event name | Payload | Trigger |
|------------|---------|---------|
| `state` | `{ state, serialNumber, firmwareVersion, hardwareVersion, irSensor, roastCount, isActive }` | State change |
| `data` | Full blueprint object (Payload A + B fields) | Every 350ms during roast |
| `new-roast-from-device` | — | PSR/preheat button pressed |
| `crack-from-device` | — | Crack button (bit 31 of `buttons`) |
| `detach-from-device` | `{ error }` | USB disconnect |
| `error` | `{ errorCode1, errorCode2, errorValue1, errorValue2 }` | Device error |
| `log-send-started` | — | Log upload begin |
| `log-send-ended` | — | Log upload complete |

---

## 8. TypeScript Interfaces

### Roast Record (roasts/ JSON file)

```typescript
interface RoastRecord {
  // Identity
  uid: string;                    // nanoid, used as filename
  userId: string;                 // Firebase UID
  recipeID?: string;              // references recipes/ dir

  // Timestamps
  dateTime: number;               // Unix ms
  updatedAt?: number;             // Unix ms (29% present)

  // Timing
  totalRoastTime: number;         // seconds
  roastStartIndex: number;        // index into time-series arrays
  roastEndIndex: number;          // index into time-series arrays
  sampleRate: number;             // always 2 (Hz)
  missingSeconds: number[];       // indexes with missing data (usually [])

  // Temperatures (scalar, °C)
  preheatTemperature: number;
  beanChargeTemperature: number;  // IBTS bean temp at charge
  beanDropTemperature: number;    // IBTS bean temp at drop
  drumChargeTemperature: number;
  drumDropTemperature: number;
  rorPreheat?: number;            // °C/min (94% present)

  // Time-series (length = totalRoastTime * sampleRate)
  beanTemperature: number[];      // °C, IBTS
  drumTemperature: number[];      // °C
  beanDerivative: number[];       // °C/min, RoR
  ibtsDerivative: number[];       // °C/min, IBTS RoR (different smoothing)
  exitTemperature: number[];      // °C, exhaust

  // Milestone indexes (in time-series units; 0 = not marked)
  indexYellowingStart: number;
  indexFirstCrackStart: number;
  indexFirstCrackEnd: number;
  indexSecondCrackStart: number;
  indexSecondCrackEnd: number;

  // Weight (g; 0 = not filled by user)
  weightGreen: number;
  weightRoasted: number;

  // Machine info
  roastNumber: number;            // lifetime roast counter on machine
  serialNumber: number;
  firmware: number;
  firmwareVersion: number;        // same as firmware
  softwareVersion: string;        // e.g. "3.4.1"
  hardware: number;
  IRSensor: number;               // 2 = IBTS

  // User-filled (optional)
  roastName?: string;
  roastDegree?: string;
  ambient?: number;               // °C
  humidity?: number;              // %
  inventory?: string;
  hasError?: boolean;
  rating?: number;                // never used in observed data
  comments?: string;              // never used in observed data

  // Manual actions log
  actions: {
    actionTimeList: Array<{
      ctrlType: 0 | 1 | 2;       // 0=Power, 1=Fan, 2=Drum
      index: number;              // seconds from roast start
      value: number;              // 0–9
    }>;
    actionTempList: never[];      // always empty
  };
}
```

### Recipe

```typescript
interface Recipe {
  uid: string;
  name: string;
  userId: string;
  dateTime: number;               // Unix ms
  updatedAt?: number;
  tempMeasurement: "C" | "F";
  preheatTemp: number;            // °C
  isFork: boolean;

  startSettings: {
    power: string;                // "0"–"9"
    drum: string;
    fan: string;
  };

  events: Array<Array<{
    trigger: 0 | 3;               // 0=temp threshold, 3=elapsed time
    condition: number;
    value: number | null;         // °C or seconds
    actions: Array<{
      action: 0 | 1 | 2;         // 0=Power, 1=Fan, 2=Drum
      value: string;              // "0"–"9"
    }>;
  }>>;
}
```

### Real-time Blueprint (IPC data event payload)

```typescript
interface Blueprint {
  // Payload A fields
  beanTemp: number;               // °C float, IBTS
  beanRise: number;               // °C/min float, RoR
  drumTemp: number;               // °C float
  ibtsRise: number;               // °C/min float
  exitTemp: number;               // °C float
  buttons: number;                // bitmask; bit31=crack button
  minutes: number;                // elapsed time
  seconds: number;
  blowerSetting: number;          // 0–9, current fan level
  inductionPowerSetting: number;  // 0–9, current power level
  drumSetting: number;            // 0–9, current drum speed
  stateMachine: number;           // 0x0000–0x0024, see state table
  sampleNumber: number;           // sequential counter
  ambientTemp: number;            // °C float
  ambientIRTemp: number;          // °C float
  roomHumidity: number;           // % (from ambient profile, not USB)
  samplesInFIFO: number;
  blowerRPM: number;
  inputVoltage: number;
  coilRPM: number;
  errorCodes: number;
  validData: boolean;

  // Payload B fields
  beanSoundEnergy: number;        // acoustic crack energy
  beanSoundBaseline: number;
  rorPreheat: number;             // °C/min
  errorCode1: number;             // 1–10 = hasError
  errorValue1: number;
  errorCode2: number;
  errorValue2: number;
  coilRPMFan2: number;
  currentTest: number;
  IGBTTemperature: number;        // °C
  IGBT2Temperature: number;       // °C
  IGBTFrequency: number;          // Hz = 40000000 / timerPeriod
  pHTemperatureSetting: number;
  IRFanRPM: number;
}
```

### GET_DEVICE_USAGE — 36-byte Response

```typescript
interface DeviceUsage {
  totalSecondsOn: number;         // bytes 0–3, uint32 LE
  totalSecondsDrumMotorOn: number;// bytes 4–7, uint32 LE
  powerOnCounter: number;         // bytes 8–11, uint32 LE
  states: [number, number, number, number]; // bytes 12–27, 4× uint32 LE
  eepromMainFailure: number;      // bytes 28–29, uint16 LE
  numberRoasts: number;           // bytes 30–31, uint16 LE
  // bytes 32–35: unspecified
}
```

---

## 7. USB Protocol (v2.x — Complete)

> Source: reverse-engineered from `.webpack/renderer/bg_window/index.js` inside `RoasTime.app/Contents/Resources/app.asar`

### Device Identifiers

```javascript
AILLIO_VENDOR_IDS  = [0x0483]          // STMicroelectronics
AILLIO_PRODUCT_IDS = [0x5741, 0xa27e]  // Old firmware / Current firmware
```

### Packet Format

All USB packets are **64 bytes**, transferred via HID/USB bulk.

**Command → Device:** `Buffer.alloc(64)` — first bytes are command-specific (see below).

**Device → App:** 64-byte response. Validity check:
```javascript
data[62] == 0xFF && data[63] == 0xAA && data[41] == 0x0A
```

---

### Command Reference (Write to Device)

| Command ID | Name | Bytes | Description |
|-----------|------|-------|-------------|
| 0 | SET_DRUM_SPEED | `[0x32, 0x00, setting, 0x00]` | Set drum speed (0–9) |
| 1 | PSR_BUTTON_COMMAND | `[0x30, 0x01, 0x00, 0x00]` | Physical button press |
| 2 | SET_FAN_SPEED | `[0x31, fanId, setting, 0x00]` | Fan 1: fanId=0x00, Fan 2: fanId=0x03 |
| 3 | SET_INDUCTION_POWER | `[0x34, 0x00, setting, 0xBA]` | Set power level (0–9) |
| 7 | SET_BUZZER | `[0x38, 0x00, setting>>8, setting]` | Buzzer control |
| 9 | SET_PREHEAT_SETPOINT | `[0x35, 0x00, setting>>8, setting]` | Preheat target temp (°C) |
| 10 | POWER_INCREMENT | `[0x34, 0x01, 0xAA, 0xAA]` | Power +1 step |
| 11 | POWER_DECREMENT | `[0x34, 0x02, 0xAA, 0xAA]` | Power −1 step |
| 12 | SET_BLOWER_SETTING | `[0x31, 0x00, setting, 0x00]` | Blower direct set |
| 13 | BLOWER_INCREMENT | `[0x31, 0x01, 0xAA, 0xAA]` | Blower +1 step |
| 14 | BLOWER_DECREMENT | `[0x31, 0x02, 0xAA, 0xAA]` | Blower −1 step |
| 19 | GET_DEVICE_DATA | `[0x89, 0x01, ...]` read 32 bytes | Device info (serial, hardware, firmware) |
| 20 | GET_DEVICE_USAGE | `[0x89, 0x01, ...]` read 36 bytes | Lifetime usage stats |
| 21 | PAYLOAD_PART_A | `[0x30, 0x01]` read 64 bytes | Real-time sensor data Part A |
| 22 | PAYLOAD_PART_B | `[0x30, 0x03]` read 64 bytes | Real-time sensor data Part B |
| 23 | CLEAR_BUFFER | `[0x30, 0x05]` | Clear device FIFO buffer |
| 24 | RESET_USB | `[0x4A, 0x01]` | Reset USB connection |
| 25 | RESET_ROASTER | `[0x20, 0xFF]` | Full roaster reset |
| 26 | GET_ROASTER_STATUS | `[0x30, 0x99]` | Get roaster status (same as GET_VARS in v4) |

**Note:** SET_DRUM_SPEED byte 0 deduced as `0x32` from pattern; exact value should be verified.

---

### PAYLOAD_PART_A — 64-byte Response Layout

Called every sample (2 Hz). Contains all real-time sensor readings.

| Bytes | Field | Type | Unit | Description |
|-------|-------|------|------|-------------|
| 0–3 | `beanTemp` | float32 LE | °C | Bean temperature (IBTS) |
| 4–7 | `beanRise` | float32 LE | °C/min | Bean RoR |
| 8–11 | `drumTemp` | float32 LE | °C | Drum temperature |
| 12–15 | `ibtsRise` | float32 LE | °C/min | IBTS RoR |
| 16–19 | `exitTemp` | float32 LE | °C | Exhaust temperature |
| 20–23 | `buttons` | uint32 LE | — | Button state bitmask |
| 24 | `minutes` | uint8 | min | Elapsed time (minutes) |
| 25 | `seconds` | uint8 | sec | Elapsed time (seconds) |
| 26 | `blowerSetting` | uint8 | 0–9 | Current fan/blower level |
| 27 | `inductionPowerSetting` | uint8 | 0–9 | Current power level |
| 28 | `drumSetting` | uint8 | 0–9 | Current drum speed |
| 29 | `stateMachine` | uint8 | enum | Roaster state (see below) |
| 30–31 | `sampleNumber` | uint16 LE | count | Sample sequence number |
| 32–35 | `ambientTemp` | float32 LE | °C | Ambient temperature |
| 36–39 | `ambientIRTemp` | float32 LE | °C | Ambient IR temperature |
| 41 | *(validity byte)* | uint8 | — | Must be `0x0A` for valid data |
| 42–43 | `samplesInFIFO` | uint16 LE | count | Samples waiting in buffer |
| 44–45 | `blowerRPM` | uint16 LE | RPM | Blower motor RPM |
| 48–49 | `inputVoltage` | uint16 LE | — | Input voltage reading |
| 52–53 | `coilRPM` | uint16 LE | RPM | Induction coil RPM |
| 54–55 | `errorCodes` | uint16 LE | — | Error code bitmask |
| 60 | `crc` | uint8 | — | CRC byte |
| 62 | *(validity byte)* | uint8 | — | Must be `0xFF` |
| 63 | *(validity byte)* | uint8 | — | Must be `0xAA` |

---

### PAYLOAD_PART_B — 64-byte Response Layout

| Bytes | Field | Type | Unit | Description |
|-------|-------|------|------|-------------|
| 0–3 | `beanSoundEnergy` | float32 LE | — | Bean crack sound energy |
| 4–7 | `beanSoundBaseline` | float32 LE | — | Sound baseline |
| 8–11 | `rorPreheat` | float32 LE | °C/min | RoR during preheat |
| 24–25 | `errorCode1` | uint16 LE | — | Error code 1 |
| 26–27 | `errorValue1` | uint16 LE | — | Error value 1 |
| 28–29 | `errorCode2` | uint16 LE | — | Error code 2 |
| 30–31 | `errorValue2` | uint16 LE | — | Error value 2 |
| 32–33 | `coilRPMFan2` | uint16 LE | RPM | Coil RPM Fan 2 |
| 34–35 | `currentTest` | uint16 LE | — | Self-test current |
| 36 | `IGBTTemperature` | uint8 | °C | IGBT 1 temperature |
| 37 | `IGBT2Temperature` | uint8 | °C | IGBT 2 temperature |
| 38–39 | `timerPeriod` | uint16 LE | — | IGBTFrequency = 40000000 / timerPeriod |
| 40–41 | `pHTemperatureSetting` | uint16 LE | — | pH temp setting |
| 42–43 | `IRFanRPM` | uint16 LE | RPM | IR sensor fan RPM |

---

### GET_DEVICE_DATA — 32-byte Response

| Bytes | Field | Description |
|-------|-------|-------------|
| 0–3 | `serialNumber` | uint32 LE |
| 4 | `yearManufacturing` | uint8 |
| 5 | `monthManufacturing` | uint8 |
| 6 | `dayManufacturing` | uint8 |
| 7 | `hourManufacturing` | uint8 |
| 8–11 | `hardwareVersion` | uint32 LE |
| 10 | `IRSensor` | uint8 (within hardwareVersion) |
| 12–15 | `uniqueID1` | uint32 LE, hex string |
| 16–19 | `uniqueID2` | uint32 LE, hex string |
| 20–23 | `uniqueID3` | uint32 LE, hex string |
| 24–27 | `firmwareVersion` | uint32 LE |
| 28–31 | `crc` | uint32 LE |

---

### stateMachine Values (Roaster State)

| Value | State | Description |
|-------|-------|-------------|
| `0x0000` | IDLE | Roaster idle / off |
| `0x0002` | PREHEATING (start) | Preheat initiated |
| `0x0003` | PREHEATING | Preheating in progress |
| `0x0004` | CHARGE | Bean charge detected |
| `0x0005` | — | Valid roasting state |
| `0x0006` | ROASTING | Active roast |
| `0x0007` | — | Valid roasting state |
| `0x0008` | COOLING | Cooling cycle |
| `0x0009` | COOLDOWN | Cooldown complete |
| `0x0023` | PREHEATING | Preheating (alt state) |
| `0x0024` | — | Valid roasting state |

`VALID_ROASTER_STATES = [0x0002, 0x0003, 0x0004, 0x0005, 0x0006, 0x0007, 0x0008, 0x0009, 0x0023, 0x0024]`

`PREHEATING_ROASTER_STATES = [0x0023, 0x0002, 0x0003]`

---

### IPC Events (bg_window → main_window)

| Event | Type | Payload |
|-------|------|---------|
| `state` | MSG_TYPE.State | Roaster state update |
| `data` | MSG_TYPE.RoastData | Full blueprint object (Part A + B merged) |
| `new-roast-from-device` | MSG_TYPE.RoastStartedByDevice | Roast auto-started by physical button |
| `crack-from-device` | MSG_TYPE.CrackButtonPressedByDevice | Crack button pressed on device |
| `detach-from-device` | MSG_TYPE.UsbDetached | USB disconnected |
| `error` | MSG_TYPE.Error | Error event |

Transport: `node-ipc` Unix socket (socket name passed via `set-socket` IPC message).
