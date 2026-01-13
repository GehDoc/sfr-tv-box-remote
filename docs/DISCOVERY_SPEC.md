# SFR Box Discovery Protocol Specification

## 1. Objective
This document outlines the proposed mechanism for discovering all supported SFR Box models (STB8, STB7, LaBox) on the local network. The goal is to create a robust process that reliably gathers all necessary information to establish a connection and display the device in a user interface.

## 2. Proposed Data Structure
The discovery process for any box should yield a structured object containing the following information:

| Field                        | Type   | Description                                                                                             | Example                          |
|------------------------------|--------|---------------------------------------------------------------------------------------------------------|----------------------------------|
| `identifier`                 | `str`  | A machine-readable model identifier (e.g., STB8, STB7, LaBox).                                            | `STB8`                           |
| `name`                       | `str`  | A user-friendly name for the device.                                                                    | `Décodeur TV Salon`              |
| `ip_address`                 | `str`  | The local IP address of the box.                                                                        | `192.168.1.25`                   |
| `port`                       | `int`  | The WebSocket port for the control protocol.                                                            | `8080`                           |
| `icon_url`                   | `str`  | A URL to a device icon, suitable for a UI.                                                              | `http://.../icon.png`            |
| `service_name_prefix_avahi`  | `str`  | The prefix used in the mDNS service instance name to identify the box model (from `dn/i.java`).         | `STB8`                           |

## 3. Proposed Discovery Mechanism

The discovery process happens in two distinct stages:

### Stage 1: Initial IP & Model Discovery
The app uses three parallel methods to find a box's IP address on the local network.

#### A) mDNS (Zeroconf) Method
*   **How it works**: Listens for the `_ws._tcp.local.` service type.
*   **Result**: Provides **IP Address** and **Model Type** (by matching `STB7`, `STB8`, `ws_server` prefixes in the service name).

#### B) DNS Method (LaBox Only)
*   **How it works**: Performs a DNS lookup for the hostname `websocket.labox`.
*   **Result**: Provides **IP Address** for `LABOX` devices.

#### C) Router API Method ("GET_HOST_LIST")
*   **How it works**: Queries the local network gateway (e.g., `http://192.168.1.1/lan.getHostsList`) for an XML list of all connected LAN clients.
*   **Result**: Provides **IP Address** and **Model Type** for STB7/STB8 by finding "stb7" or "stb8" in client hostnames.

### Stage 2: Detailed Information Fetching (Hypothesis)
**Crucially, none of the Stage 1 methods provide the rich details** like `name`, `port`, or `icon_url`.

Once a box's IP address is found in Stage 1, a second step **must** occur:
1.  A direct HTTP request is likely made to an endpoint on the box itself (e.g., `http://<box_ip>/info`).
2.  The response to this request is the **JSON data** you have for the STB8. This JSON contains the final, detailed information needed.

## 4. ❗ Action Items & Challenges for You

We have now fully mapped Stage 1. To complete the specification, we must prove the hypothesis for Stage 2.

1.  **STB8 JSON Announce**: **This is the #1 priority.** Please provide the full JSON data you have for the STB8. It is the key to everything else.

2.  **Context for the JSON**: Along with the data, how was this JSON obtained? Was it from a tool like `mitmproxy` intercepting traffic from the app after it discovered a box? Knowing the **HTTP endpoint** it was fetched from (e.g., `/getInfo`, `/api/system`) is as important as the JSON itself.

3.  **Java Code Analysis (JSON Parsing)**: To find the code that performs this Stage 2 request, please search the **entire Java source code** for keys you expect to be in your JSON data (e.g., `"friendlyName"`, `"productName"`, `"wsPort"`). This will lead us directly to the class that parses the JSON and reveals the HTTP endpoint it was fetched from.