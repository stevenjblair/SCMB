# Star Citizen Mining Buddy (SCMB)

A lightweight, external HUD overlay and telemetry utility designed for Star Citizen miners. **SCMB** uses real-time, non-intrusive Optical Character Recognition (OCR) to track mining deposit signatures and active server performance metrics—completely independent of the game client.

<img width="991" height="627" alt="Screenshot 2026-07-08 112827" src="https://github.com/user-attachments/assets/17994a5e-c91d-485e-9713-97a40d6f65ec" />

---

## 🚀 Features

* **Instant Signature Identification:** Eliminates manual lookup tables. SCMB instantly reads scanning signantures and cross-references them against a static database to output deposit contents (e.g., `Iron x 3`).
* **Dynamic Click-Through HUD:** The main display overlay is transparent and mouse-blind. It sits cleanly over your HUD without stealing mouse inputs or blocking ship flight controls.
* **Left-ALT Calibration Engine:** Hold down **Left ALT** to temporarily unlock window interactivity. Drag, scale, or reposition elements seamlessly in real time.

https://github.com/user-attachments/assets/7c80ee24-76c3-49d8-b426-cea4a047bb00

* **Cropping-Style UI Adjustment:** Clicking "Unlock UI" reveals semi-transparent layout boxes featuring 8-way interactive bounding handles to adjust your scanning bounds flawlessly.  This should allow for compatability with any resolution and even ultrawide monitors.  I have yet to test with VR.
<img width="1884" height="1132" alt="Screenshot 2026-07-08 114218" src="https://github.com/user-attachments/assets/bf7e4b56-c936-4ca6-8f46-e1fe48729971" />

* **Live Server FPS Telemetry:** Monitors server health using a dynamic traffic-light indicator embedded directly into the control panel headbar.
  * 🟩 **>= 20 FPS:** Stable Server Environment
  * 🟨 **10–19 FPS:** Degrading Performance
  * 🟥 **< 10 FPS:** Critical Server Degradation / Imminent Recovery
* **Sticky Memory Engine:** Intelligent 5-second caching filter keeps server status readings visible even when flying over high-contrast planetary surfaces or blinding dust clouds.
* **In-Cockpit Tool Utilities:** Includes a quick-access button to copy `r_displayinfo = 1` directly to your clipboard for effortless console deployment.

## ⚖️ Cloud Imperium Games Terms of Service & Fair Play Compliance

**SCMB** is fully compliant with Cloud Imperium Games' (CIG) Terms of Service. It operates strictly as an external visual aid and adheres to the following non-intrusive safety principles:

* **Zero Memory Hooking:** The app does not attach to, inject code into, or read from the `StarCitizen.exe` process or memory space. 
* **Easy Anti-Cheat (EAC) Safe:** Because the script treats the game client as a complete black box and never reads or manipulates the active game state, it will **never** trigger an EAC flag, violation, or ban. 
* **Zero Automation / No Macros:** SCMB does not simulate mouse clicks, keystrokes, or send hardware inputs to the game client. It provides zero automated flight or mining functions.
* **Pure Video Capture Technology:** The overlay functions identically to streaming software (like OBS or Discord stream previews). It simply captures a flat image of specific coordinates on your display using standard Windows desktop duplication APIs, parses the visible pixels via OCR, and floats a standard transparent Windows text layer on top of your screen.

Using SCMB is 100% safe, ensuring your account remains in perfect standing while you mine.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your machine. 
The overlay only works in borderless windowed mode.  there is no wat to make it work in full screen without breaking TOS.
This utility requires **Tesseract-OCR** to run screen parsing layers. 
1. Download the Windows installer from the [UB-Mannheim Tesseract Repository](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install it to the default directory: `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 2. Download Font Asset
To display the customized interface styling, download the free **Electrolize** font family from Google Fonts:
1. Visit [Google Fonts - Electrolize](https://fonts.google.com/specimen/Electrolize).
2. Click **Download Family**.
3. Extract `Electrolize-Regular.ttf` and place it directly inside your project folder.

### 3. Install Dependencies
Open your terminal or command prompt inside the project folder and install the required modules:
```bash
pip install opencv-python numpy mss pytesseract
```
Starting the overlay 
```bash
cd  pathtoinstall\SC_miningBuddy
python .\mining_dashboard.py
```
For now I exit the program by CTRL+C or closing the terminal

## ⚠️ Known Issues

Right now there is only some minor things to mention, I hope to hear from you if you find anythign not mentioned here.

* **High Contrast Text Bleed:** Extreme environmental lighting (e.g., staring directly into a star or asteroid belt background) can occasionally cause the OCR engine to misread characters.
* **Tesseract Pathing:** If Tesseract-OCR is installed on a non-standard drive or directory, the path string must currently be updated manually within the config.py script.
* **Unhandeled Signals** Currently debris, FPS minables, ships both derelict and running do not flag for anything
* **The Math** I originally used an algorithm to do math on the signal to calculate the signature.  I liked that method best but it did have issue with occasional noise OCR can pick up so I switched to large database of every possible minable signature.  This is fast and near issue free but I prefer the more elegant method of doing math.  I will work on making it right.
* **OCR catch**  I have found one issue with the mining database.  OCR is looking for signals very fast and the game UI is not static, this is an issue when you scan an Aluminum x 4 (17140) and Borase x 2 (7140).  Currently the algorithm takes a consensus of the signatures it **thinks** it sees and makes a nearly perfect guess.  In debug mode I can see when scanning aluminum x4 the 1 can be clipped off if all the circumstances are perfect.  In which cause you will get a false ID.  Please let me know if you find any other with this behavior.  I am working on eliminating the issue.

---

## 🗺️ Roadmap & Future Direction

I am constantly looking to improve SCMB's utility without compromising account safety, spped, resource use, or breaking TOS. Here are the features currently planned for future releases:

* **Config File Migration:** Moving the hardcoded Tesseract executable path, font configurations, and default bounding box metrics into an external `config.py` or `.env` file for painless user configuration. ✅ **Mostly done**
* **Native Settings GUI:** A dedicated configuration window to save user-defined capture bounds permanently between gaming sessions. ✅ **Mostly done, config is persistant**
* **Linux Adaption** The awkwardness that it was made on Linux to work on Windows, but doesn't work on Linux is not lost on me.  I will port it soon, but my linux box doesn't have xdg-open (command line only, as god intended).
* **Standalone EXE**  🟨 Maybe I should wrap this all up with a pretty bow, but then you'll be dealing with windows defender and all that fun jazz.
* **Asteroid Map**  I believe it possible to create a waypoint system to allow you to pin (or input) a location and return to it precisely later.  I'm not joking, without touching the game client.  The value of this feature would go far beyond that of just mining.  But this feature will likely only come by your support and a lot of coffee.
---

[![Ko-fi](https://shields.io/badge/ko--fi-donate-ff5f5f?logo=ko-fi&style=for-the-badgeKo-fi)](https://ko-fi.com/randm978)
<!-- [![Patreon](https://shields.io)](https://patreon.com)
[![Twitch](https://shields.io)](https://twitch.tv) -->
