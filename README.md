# PULSAR - Simple Denial of Service Test Tool

💖 If you find PULSAR useful, please consider giving it a star ⭐ on its GitHub repository! Your support is greatly appreciated.

**⚠️ IMPORTANT WARNING & USAGE GUIDELNES ⚠️**

## Disclaimer

This tool, "PULSAR" (hereinafter "the Software"), is provided for **educational and ethical testing purposes ONLY**. The author(s) of this Software are not responsible for any misuse or damage caused by this Software. By using this Software, you agree to take full responsibility for your actions.

## Legal and Ethical Use

*   **DO NOT USE THIS SOFTWARE ON ANY SYSTEM, WEBSITE, OR NETWORK THAT YOU DO NOT OWN OR HAVE EXPLICIT, WRITTEN PERMISSION TO TEST.** Unauthorized use of this Software against systems you do not have permission to test is **ILLEGAL** in most jurisdictions and can lead to severe legal consequences, including fines and imprisonment.
*   This Software is intended for testing the resilience of your **OWN** servers, networks, and applications, or those for which you have obtained clear, unambiguous, and verifiable consent from the owner.
*   Always respect the terms of service of any platform or hosting provider. Testing your own website on a shared hosting environment might affect other users and could violate your hosting agreement.
*   Be aware of the potential impact of your tests. Even when testing your own systems, high loads can cause instability, service disruption, or data loss if not handled carefully. Monitor your systems closely during testing.

## How to Use Responsibly

1.  **Obtain Permission:** Always get explicit, written permission before testing any system that is not your own.
2.  **Understand the Target:** Know the limits and capabilities of the system you are testing.
3.  **Start Small:** Begin with a low number of threads and a short duration. Gradually increase the load while monitoring the target system's performance and your own system's resources.
4.  **Monitor:** Closely monitor both the target system (server logs, resource usage, responsiveness) and the machine running PULSAR (CPU, memory, network usage).
5.  **Inform Stakeholders:** If testing a system used by others (even if it's your own), inform them about planned tests to avoid disruptions.
6.  **Cease Immediately if Issues Arise:** If the target system shows signs of instability or unintended negative impact, stop the test immediately.

## No Warranty

This Software is provided "as-is" without any warranty of any kind, express or implied. The author(s) make no warranties regarding the performance, merchantability, fitness for a particular purpose, or non-infringement of this Software.

## Contribution

If you wish to contribute to this project, please ensure your contributions also adhere to ethical guidelines and promote responsible use.

---

## Description
PULSAR is a simple Python script designed to simulate a Denial of Service (DoS) attack by sending a large number of HTTPS (including HTTP) or DNS (UDP flood) requests to a specified target. It allows users to specify the attack type, target domain/IP, port (for HTTPS/HTTP), duration of the test, and the number of concurrent workers.

## Features
*   Interactive mode for easy parameter input.
*   Command-line argument support.
*   HTTPS/HTTP (ports 443/80) and DNS (UDP flood on port 53) attack types.
*   Multi-threaded request generation.
*   Real-time progress display.
*   **Ctrl+C** to stop an ongoing attack.
*   Post-attack menu for repeating, starting new, or closing.
*   Console title updates.
*   Basic traffic and PC overload estimation/warnings.

## Prerequisites
*   **Python 3.6+ installed and configured:** Ensure Python is added to your system's PATH environment variable, so `.py` files are associated with the Python interpreter.
    *(No external libraries are required for the core functionality.)*

## Installation
1.  Clone this repository or download `PULSAR.py`.
2.  No further installation steps are required for the core script.

## Usage

PULSAR can be launched in two primary ways:

**1. Interactive Mode (Recommended for ease of use):**

Simply run the script without any arguments. The program will guide you through setting up the attack parameters.
*   On many systems (like Windows), if Python is correctly installed and associated with `.py` files, you might be able to **double-click the `PULSAR.py` file** to run it. A console window should open.
*   Alternatively, you can always open a terminal/command prompt, navigate to the script's directory (e.g., `cd path/to/PULSAR_DoS`), and then execute `python PULSAR.py` or `python3 PULSAR.py`.

**2. Command-Line Arguments:**

For more direct control or for scripting, you can specify all parameters via the command line:

```bash
python PULSAR.py [--attack_type <TYPE>] [target] [port_for_https] [duration] [-t threads] [-i]
