# Ground Control Hub (GCH)  
> One-stop desktop application for configuring, monitoring and analyzing the Regular-HZ FDR flight recorder.

---

## Overview
Ground Control Hub is a cross-platform GUI written in **Python** that turns your PC into a mission-control center for the **Regular-HZ FDR** stack.  
It unifies:
* real-time telemetry display,
* parameter tuning,
* pre-flight sensor tests,
* flight-data download (USB, SD, LoRa_Link),
* powerful log plotting with user-configurable dashboards.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-tab interface** | Settings • Flight • Tests • LoRa Link • Analysis |
| **USB/LoRa dual link** | Auto-detects COM ports by VID/PID; seamless switch between USB-CDC and LoRa Link |
| **Parameter editor** | Modify `safe_settings`, `critical_settings`, and radio parameters on the fly |
| **Real-time dashboard** | Numeric widgets for altitude, speed, battery, RSSI |
| **Pre-flight tests** | One-click sensor health check and “fake take-off” test |
| **LoRa Link console** | Bind, ping, and dump black-box logs directly via the LoRa radio module |
| **Log analyzer** | CRUD-style plot builder, save/load plot configs, export PNG/SVG/CSV |
| **Dark / light themes** | Toggle on demand |
| **Portable configs** | All user files (*.gchcfg, *.gchplot) are JSON and human-readable |

---

## Screenshots
*(Coming soon)*

---

## Quick Start

### 1. Requirements
| Component | Minimum |
|-----------|---------|
| OS | Windows 10 |
| Python | 3.10+ |
| RAM | 512 MB free |
| Ports | 1× USB-A for Regular-HZ FDR or LoRa_Link dongle |
| Optional | SD card reader (for offline log import) |

### 2. Install
```bash
git clone https://github.com/Nate-Hunter-max/HZ-Ground-Control-Hub.git
cd hz-ground-control-hub
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Launch
```bash
python -m gch.main
```
The app will search for connected devices and open the **Flight** tab by default.

---

## Usage Walk-through
1. **Settings** – Load `*.gchcfg`, edit parameters, write back to the airframe.  
2. **Flight** – Watch live telemetry; press **Record** to capture a new log.  
3. **Tests** – Run **Health Check** before every launch.  
4. **LoRa Link** – Open terminal, type `bind`, then `download` to pull black-box data.  
5. **Analysis** – Drag-and-drop any `.log` file, build dashboards, export graphs.

---

## File Formats
| Extension | Purpose |
|-----------|---------|
| `.gchcfg` | Aircraft configuration (JSON) |
| `.gchplot` | Saved plot layout (JSON) |
| `.log` / `.csv` / `.bin` | Flight logs from SD, USB, or LoRa Link |

---

## Hardware Compatibility
* **Regular-HZ FDR**
* **LoRa Link v1.0**

---

## License
MIT © 2025 SHARAGA_FOREVER!