# NinoClicker v2.1 (Quartz Injection Suite)

A high-performance automation utility for macOS designed for low-latency input simulation and system stress testing. NinoClicker bypasses standard library delays by utilizing the `Quartz.CoreGraphics` framework for direct event injection.

## 🚀 Core Features
* **Quartz Direct Injection:** Optimized God Mode capable of 20,000+ CPS by bypassing the system event loop.
* **Performance Telemetry:** Real-time HUD (Mapped to `H` key) monitoring CPS throughput and calculated engine load.
* **Persistence Layer:** Encrypted-style JSON profile management for macros, coordinates, and session history.
* **Safety Protocols:** Global hardware-level Panic Key (`S`) to interrupt high-frequency click buffers.
* **UI Customization:** State-driven CSS skinning system (Hacker, Void, Ruby, Gold).

## 🛠️ Installation
Ensure you have Python 3.9+ installed on your macOS environment.

1. Install dependencies:
   ```bash
   pip install PyQt6 pyautogui pyobjc-framework-Quartz
