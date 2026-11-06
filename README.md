# LVYUAN Inverter (EyeBond G-ASCII) for Home Assistant

Custom integration for local monitoring and control of **LVYUAN** hybrid inverters (and compatible Must/Voltronic architecture models) via **EyeBond G-ASCII** protocol over serial port (RS-232).

## 🌟 Features

- **100% Local Connection**: No cloud, no Chinese servers, no Wi-Fi loggers. Complete independence.
- **High-Speed Polling**: Smart polling cycle (fast telemetry every 5 seconds, settings every 5 minutes).
- **Full Control**: Read telemetry (voltage, current, power, SOC, temperatures) and write settings (charge priorities, current limits, operating modes).
- **Reliability**: Automatic reconnection on connection loss and proper protocol error handling.
- **No ESP Required**: Just plug in a USB-RS232 cable. No soldering, no ESPHome, no additional firmware.

## 🔌 Supported Models

- **LVYUAN TY-SIC-3.6KBE-W1** (24V system, Must architecture)
- Other inverters using EyeBond G-ASCII protocol via RS-232 (RJ-45 port)

## 🛠️ Physical Connection

The connection requires a **custom-made USB-to-RJ45 adapter** using a phone charger cable and a standard console cable.

### Required Components:
1. **USB phone charger cable** (USB-A to micro-USB/USB-C) - will be cut and modified
2. **RJ-45 keystone jack** (wall socket)
3. **USB-to-RS232 console cable with RJ-45 connector** (commonly used for Cisco/MikroTik switches)
4. **Short RJ-45 patch cord** (optional, for convenience)

### Step 1: Create USB-to-RJ45 Adapter

1. Take a USB phone charger cable and **cut off one end** (the micro-USB/USB-C side), leaving the USB-A connector.
2. **Insert the USB-A connector into the WIFI port** on the inverter.
3. On the cut end, you will find 4 wires. Measure voltages to identify them:
   - ⚫ **Black** = GND (Ground)
   - 🩷 **Pink** = +5V (VCC, power)
   - 🔵 **Blue** = TX (Inverter transmit, RS-232 signal, approximately -5V)
   - ⚪ **White** = RX (Inverter receive, approximately 0V)

### Step 2: Wire the RJ-45 Keystone Jack

Connect the wires from the USB cable to the RJ-45 keystone jack:

| USB Cable Wire | Signal | RJ-45 Pin | Notes |
|----------------|--------|-----------|-------|
| ⚫ **Black**   | GND    | Pin 4 or 5 | Ground |
| 🔵 **Blue**    | TX (Inverter) | Pin 3 | Goes to RX of adapter |
| ⚪ **White**   | RX (Inverter) | Pin 6 | Goes to TX of adapter |
| 🩷 **Pink**    | +5V (VCC) | **DO NOT CONNECT** | ⚠️ **Insulate this wire!** |

> ⚠️ **Critical:** Never connect the +5V (Pink) wire to the RJ-45 jack. This is power only for the original logger. Connecting it to your USB adapter can damage the inverter port or your Home Assistant device.

### Step 3: Connect Console Cable

1. Take the **USB-to-RS232 console cable** with RJ-45 connector.
2. Insert the RJ-45 connector into the keystone jack (directly or via short patch cord).
3. **Plug the USB end of the console cable into your Home Assistant device** (TV box, Raspberry Pi, etc.).

### Final Connection Diagram:
> ⚠️ **Important:** Never connect the +5V (VCC) wire from the USB cable to the inverter. This can damage the inverter port or USB adapter. Use only TX, RX, and GND.

**Port Settings:** `9600` baud, `8` data bits, `None` parity, `1` stop bit (`9600 8N1`).

## 📦 Installation

### Option A: Via HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant.
2. Go to **HACS** → **Integrations** → **⋮** (three dots in top right) → **Custom repositories**.
3. Add this repository URL: `https://github.com/SitifDm/lvyuan_eybond`
4. Select category **Integration**.
5. Find **LVYUAN Inverter (EyeBond G-ASCII)** and click **Install**.
6. Restart Home Assistant.

### Option B: Manual Installation

1. Copy the `custom_components/lvyuan_eybond` folder to `<config_dir>/custom_components/` in your Home Assistant.
2. Restart Home Assistant.

## ⚙️ Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **LVYUAN Inverter (EyeBond G-ASCII)**.
3. Enter connection parameters:
   - **Serial device**: e.g., `/dev/ttyUSB0` (or `COM3` on Windows).
   - **Baud rate**: `9600` (fixed for this protocol).
   - **Scan interval**: `5` seconds (recommended).
   - **Timeout**: `3` seconds.
4. Click **Submit**. The integration will automatically verify the connection to the inverter.

## 📊 Available Entities

The integration creates the following entity groups:

### Sensors
- **Grid**: Voltage, frequency, power, energy (today/total)
- **PV**: Voltage, current, power, charging current, energy (today/total), temperature
- **Battery**: Voltage, current, capacity (SOC), type, cutoff/alarm voltages
- **Output**: Voltage, frequency, current, active power, load percentage, energy (today/total)
- **Inverter**: Voltage, current, temperatures (mainboard, PV, charger, ambient)
- **System**: Operating mode, software version, fault codes, warning status

### Binary Sensors
- Battery charging/discharging status
- PV charging status
- PV tracking/chargeable status
- Fan 1/2 stopped status
- Fault/Warning active status

### Numbers (Settings)
- Max charging current (Prog 07)
- Max utility charging current (Prog 06)
- Constant voltage charging voltage (Prog 20)
- Float charging voltage (Prog 21)
- Equalization charging voltage/time/timeout/interval
- Battery discharge cutoff/alarm voltages
- Battery to grid/grid to battery voltages
- Battery overvoltage protection
- Grid overvoltage/undervoltage protection
- Low power discharge time
- Constant current charging max time

### Selects
- Output mode (Appliance/UPS)
- Output priority (Utility/PV/PV>Battery>Utility)
- Charging priority (Utility/PV/Utility+PV/PV only)
- Battery type (Lead-acid/Flooded/Lithium/Custom)
- Output voltage (208V/220V/230V/240V)
- Charging method (Auto/2-stage/3-stage)
- AC input range (APL wide/UPS narrow)

### Switches
- BMS communication (Prog 38)
- Energy saving mode (Prog 12)
- Battery equalization (Prog 29)
- Battery not connected alarm (Prog 28)
- Buzzer silent mode (Prog 14)
- Inverter soft start (Prog 25)

## 🛠️ Services

- **`lvyuan_eybond.send_command`**: Send raw EyeBond G-ASCII command to the inverter (for advanced users and debugging).
- **`lvyuan_eybond.refresh`**: Force immediate refresh of all LVYUAN sensors.

## ❓ Troubleshooting

### Error: "Failed to connect"
1. Verify the port is correctly identified (`/dev/ttyUSB0`). Check Home Assistant logs or run `dmesg | grep tty` in terminal.
2. Ensure the cable is securely connected and TX/RX wiring is correct (try swapping TX and RX if no response).
3. Verify the `homeassistant` user has read/write permissions for the port:

        sudo usermod -a -G dialout homeassistant
        sudo reboot

### Data not updating or shows "unavailable"
- Check if the port is occupied by another program (e.g., Python script, `screen`, `minicom`, or another integration instance).

### NAK response to commands
- TX and RX may be swapped. Try reversing the connections.

### Timeout errors
- Ensure no other process is using the serial port.
- Check cable connections and port settings (9600 8N1).

## 📝 Development

### Project Structure

    custom_components/lvyuan_eybond/
    ├── __init__.py          # Integration setup and services
    ├── binary_sensor.py     # Binary sensors
    ├── client.py            # Base client and exceptions
    ├── client_serial.py     # Serial client (pyserial)
    ├── config_flow.py       # UI configuration flow
    ├── const.py             # Constants and mappings
    ├── coordinator.py       # Data coordinator with fast/slow cycles
    ├── manifest.json        # Integration manifest
    ├── number.py            # Number entities (settings)
    ├── select.py            # Select entities
    ├── sensor.py            # Sensor entities
    ├── services.yaml        # Service definitions
    ├── strings.json         # Translation strings template
    ├── switch.py            # Switch entities
    ├── brand/               # Brand icons for HA UI
    │   ├── icon.png         # 96x96 icon
    │   ├── logo.png         # 512x512 logo
    │   └── dark_icon.png    # 96x96 icon for dark theme
    └── translations/        # UI translations
        ├── en.json          # English translations
        └── ru.json          # Russian translations

### Key Technical Details
- **Protocol**: EyeBond G-ASCII (text-based commands terminated with `\r`)
- **Polling Strategy**: Fast cycle (5s) for telemetry, slow cycle (5min) for settings
- **Dependencies**: `pyserial==3.5`
- **Minimum HA Version**: 2024.1.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Home Assistant community and HACS developers
- Enthusiasts reverse-engineering Must/Voltronic and EyeBond G-ASCII protocols

## 📺 Video Tutorial

Check out the detailed setup and review video tutorial on the **Solar Разбор** YouTube channel (in Russian):  
🔗 **[Subscribe to Solar Разбор on YouTube](https://www.youtube.com/@SolarRazbor)**

## 📧 Contact & Community

- **GitHub**: [@SitifDm](https://github.com/SitifDm)
- **YouTube**: [Solar Разбор](https://www.youtube.com/@SolarRazbor)
