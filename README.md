# Star Citizen Mining Buddy (SCMB)

A lightweight, external HUD overlay and telemetry utility designed for Star Citizen miners. **SCMB** uses real-time, non-intrusive Optical Character Recognition (OCR) to track mining deposit signatures and active server performance metrics—completely independent of the game client.

---

## 🚀 Features

* **Instant Signature Identification:** Eliminates manual lookup tables. SCMB instantly reads scanning terminal hashes and cross-references them against an exact static database to output deposit contents (e.g., `Taranite x 3`).
* **Dynamic Click-Through HUD:** The main display overlay is completely transparent and mouse-blind. It sits cleanly over your cockpit crosshairs without stealing mouse inputs or blocking ship flight controls.
* **Left-ALT Calibration Engine:** Hold down **Left ALT** to temporarily unlock window interactivity. Drag, scale, or reposition elements seamlessly in real time.
* **Cropping-Style UI Adjustment:** Clicking "Unlock UI" reveals semi-transparent layout boxes featuring 8-way interactive bounding handles to adjust your scanning bounds flawlessly.
* **Live Server FPS Telemetry:** Monitors server health using a dynamic, whole-number traffic-light indicator embedded directly into the control panel headbar.
  * 🟩 **>= 20 FPS:** Stable Server Environment
  * 🟨 **10–19 FPS:** Degrading Performance
  * 🟥 **< 10 FPS:** Critical Server Degradation / Imminent Recovery
* **Sticky Memory Engine:** Intelligent 5-second caching filter keeps server status readings visible even when flying over high-contrast planetary surfaces or blinding dust clouds.
* **In-Cockpit Tool Utilities:** Includes a quick-access button to copy `r_displayinfo = 1` directly to your clipboard for effortless console deployment.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your machine. 

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
