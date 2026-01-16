# STB8 Listener Specification & APK Analysis Plan

## 1. Objective

This document outlines the current understanding of STB8 eventing mechanisms, confirms WebSocket behavior, and details the plan for re-auditing the SFR TV APK to uncover sources of unsolicited messages and status updates from the STB8. The primary goal is to identify how the official application obtains real-time state changes (e.g., power status, current channel, user interactions).

## 2. Current Findings (UPnP Eventing)

Based on the `ssdp-discover` output and the fetched `description.xml` and `scpd.xml`, the STB8 exposes a UPnP service with eventing capabilities:

* **Device Name**: `SFR_STB8_3918`
* **Device IP**: `192.168.1.133`
* **UPnP Port**: `49153`
* **Description XML**: `http://192.168.1.133:49153/uuid:857c3e16-c85b-435a-9022-aa8a31f0afe8/description.xml`
* **Event Subscription URL**: `http://192.168.1.133:49153/devices/uuid:857c3e16-c85b-435a-9022-aa8a31f0afe8/SetTopBox/MultiroomDevice/Resources/event`
* **Service Description URL (SCPD)**: `http://192.168.1.133:49153/devices/uuid:857c3e16-c85b-435a-9022-aa8a31f0afe8/SetTopBox/MultiroomDevice/Resources/scpd.xml`

**Key Discovery from `scpd.xml`**:
The `scpd.xml` for the `urn:neufboxtv-org:service:Resources:1` service lists two `stateVariable`s with `sendEvents="yes"`:

1. `current_bitrate` (dataType: `int`)
2. `usage_list` (dataType: `string`)

**Conclusion from UPnP Analysis**:
The STB8 *does* support UPnP Eventing. This is the most promising mechanism identified so far for receiving unsolicited notifications. The WebSocket endpoint (`ws://...:7682/ws`) does not appear to send real-time events for user interactions, suggesting its primary role is for command/response.

## 3. Next Steps: APK Re-audit for WebSocket and UPnP Eventing

The next step is to perform a targeted re-audit of the SFR TV APK to confirm and expand upon these findings.

* **Goal**: To understand precisely how the official SFR TV app obtains real-time state changes and event notifications from the STB8.
* **Required Information**: The STB8 SFR TV APK file.

### Areas of Investigation within the APK

1. **WebSocket (`ws://...:7682/ws`) Behavior**:
    * **Initial Connection / Handshake**: What messages, if any, does the app send immediately after establishing the WebSocket connection to `7682/ws`? Does it send a "subscribe" command to receive events?
    * **Message Parsing**: How does the app parse incoming messages on this WebSocket? Are there handlers for unsolicited events beyond direct command responses?
    * **Command Mapping**: Verify the existing `SEND_KEY`, `GET_STATUS`, `GET_VERSIONS` commands and their payload structures.

2. **UPnP Eventing Implementation**:
    * **Subscription Logic**: Does the app explicitly send HTTP `SUBSCRIBE` requests to the `eventSubURL` (`/devices/uuid:.../Resources/event`)?
    * **Callback Server**: How does the app implement its local HTTP callback server to receive UPnP event notifications?
    * **Event Parsing**: How does the app parse the notifications received for `current_bitrate` and `usage_list`? What is the expected format (e.g., XML, JSON structure within `usage_list`)?
    * **Other UPnP Services**: Are there other UPnP services (beyond `Resources:1`) that the app interacts with for state changes (e.g., related to power, media playback, channel status)? We would look for `serviceType`s like `MediaRenderer`, `AVTransport`, `PowerState`, etc., and their associated `eventSubURL`s.

3. **Alternative Communication Channels**:
    * Are there any other HTTP polling mechanisms (`GET /status`, `GET /events`) that the app uses to periodically fetch state information?
    * Is there any other push notification mechanism (e.g., Firebase Cloud Messaging, custom TCP/UDP sockets)?

### Keywords for APK Analysis

When decompiling the APK, search for these keywords in relevant Java/Kotlin files:

* `WebSocket`, `OkHttpClient` (for WebSocket connections)
* `UpnpService`, `Subscription`, `EventSub`, `ControlPoint` (for UPnP)
* `current_bitrate`, `usage_list` (for parsing known events)
* `Power`, `Channel`, `Volume`, `Status` (for state variables)
* `7682` (the WebSocket port)
* `49153` (the UPnP port)
* `description.xml`, `scpd.xml` (for UPnP metadata parsing)
* `subscribe`, `notify` (HTTP methods for UPnP eventing)
