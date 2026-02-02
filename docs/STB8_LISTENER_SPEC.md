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

1. **WebSocket (`ws://...:7682/ws` for commands, `ws://...:7684/ws` for notifications) Behavior**:
    * **Initial Connection / Handshake**: What messages, if any, does the app send immediately after establishing the WebSocket connection to `7682/ws` (command) and `7684/ws` (notification)? Does it send a "subscribe" command to receive events on the notification WebSocket?
    * **Message Parsing**: How does the app parse incoming messages on both WebSockets? Are there handlers for unsolicited events beyond direct command responses on the notification WebSocket?
    * **Command Mapping**: Verify the existing `SEND_KEY`, `GET_STATUS`, `GET_VERSIONS` commands and their payload structures, primarily for the command WebSocket.

2. **UPnP Eventing Implementation**:
    * **Subscription Logic**: Does the app explicitly send HTTP `SUBSCRIBE` requests to the `eventSubURL` (`/devices/uuid:.../Resources/event`)?
    * **Callback Server**: How does the app implement its local HTTP callback server to receive UPnP event notifications?
    * **Event Parsing**: How does the app parse the notifications received for `current_bitrate` and `usage_list`? What is the expected format (e.g., XML, JSON structure within `usage_list`)?
    * **Other UPnP Services**: Are there other UPnP services (beyond `Resources:1`) that the app interacts with for state changes (e.g., related to power, media playback, channel status)? We would look for `serviceType`s like `MediaRenderer`, `AVTransport`, `PowerState`, etc., and their associated `eventSubURL`s.

3. **Alternative Communication Channels**:
    * Are there any other HTTP polling mechanisms (`GET /status`, `GET /events`) that the app uses to periodically fetch state information?
    * Is there any other push notification mechanism (e.g., Firebase Cloud Messaging, custom TCP/UDP sockets)?


## 4. APK Analysis - WebSocket Implementation Details

Target files for analysis: `apk-source/sources/p409qn/C14838c.java` and `apk-source/sources/kn/C12594e.java`.

### `kn/C12594e.java` - WebSocket Orchestrator

This class appears to be the main orchestrator for WebSocket connections.
- It instantiates two `C14838c` objects:
    - One for `InterfaceC14836a.a.COMMAND` (assigned to `this.f19516g`)
    - One for `InterfaceC14836a.a.NOTIFICATION` (assigned to `this.f19517h`)
- This confirms the presence of two distinct WebSocket channels with different purposes, as suggested by the port discovery.
- The constructor for `C14838c` is called with parameters including the WebSocket type, the device IP address, a boolean flag, and an `OkHttpClient` instance.

### `p409qn/C14838c.java` - WebSocket Client Implementation

This class implements the core WebSocket client logic.
- It implements `InterfaceC14836a` and appears to be an `okhttp3.WebSocketListener` wrapper or implementation.
- **Constructor**: `public C14838c(InterfaceC14836a.a webSocketType, String ipAddress, boolean z10, OkHttpClient okHttpClient)`
    - `webSocketType`: Differentiates between COMMAND and NOTIFICATION WebSockets.
    - `ipAddress`: The IP address of the STB8.
    - `z10`: An unknown boolean flag.
    - `okHttpClient`: An instance of OkHttpClient for network operations.
- **Internal State**:
    - `f29517a`: Stores the `webSocketType` (COMMAND or NOTIFICATION).
    - `f29522f`: A boolean flag indicating the open/closed status of the WebSocket.
    - `f29524b`: An external listener (likely implementing `InterfaceC14837b`) which receives WebSocket events (open, close, message, failure).
- **Event Handling (via internal class `b` extending `WebSocketListener`)**:
    - `mo27921a` (onOpen): Sets `f29522f` to `true` and notifies `f29524b` of the connection opening.
    - `mo27922b` (onClosed): Sets `f29522f` to `false` and notifies `f29524b` of the connection closing.
    - `mo27923c` (onFailure): Notifies `f29524b` of a connection failure.
    - `mo27924d` (onMessage - text): Passes the received text message to `f29524b`.

The internal details of how messages are serialized/deserialized are yet to be fully determined, but the presence of `OkHttpClient` and the clear separation of COMMAND and NOTIFICATION channels are crucial.

### WebSocket Event Listeners (`kn/C12594e.java` - classes `d` and `e`)

- The classes `d` and `e` within `kn/C12594e.java` have been identified as implementing `InterfaceC14837b`.
- These classes act as the concrete listeners for the WebSocket events, receiving callbacks from `C14838c` for connection open, close, failure, and incoming text messages (`mo22619a`).
- Due to code obfuscation, directly inspecting the implementation of `mo22619a` within these listener classes for JSON parsing logic has been challenging. The direct search for JSON-related keywords within these specific methods did not yield immediate results. This suggests that JSON processing might be further abstracted or handled by other obscured utility methods.

### WebSocket Message Handling Call Chain

Analyzing the `mo22619a` implementations in `kn/C12594e.java` reveals the following call chain for received WebSocket messages:

*   **Command WebSocket (via `kn.e$d`):**
    1.  `kn.e$d.mo22619a(type, message)` calls `C12594e.this.m22614j(message)`.
    2.  `C12594e.m22614j(str)` calls `this.f19513d.mo24094e(str, this.f19510a, this.f19512c)`.
*   **Notification WebSocket (via `kn.e$e`):**
    1.  `kn.e$e.mo22619a(type, message)` calls `C12594e.this.m22615k(message)`.
    2.  `C12594e.m22615k(str)` calls `this.f19513d.mo24093d(str, this.f19510a, this.f19512c, callback)`.

The `this.f19513d` field is an instance of `AbstractC13162a`. Based on the constructor of `C12594e`, this can be one of three classes depending on the STB model:
*   `p297ln.C13167f` (for STB8)
*   `p297ln.C13166e` (for STB7)
*   `p297ln.C13164c` (for LaBox)

Therefore, the actual parsing and handling of the WebSocket messages occur within the `mo24094e` and `mo24093d` methods of these specific classes. The next step is to investigate `AbstractC13162a` and its implementations, focusing on `C13167f.java` for STB8.

### `p297ln/AbstractC13162a.java` - Abstract Message Handler

This abstract class defines the interface for handling WebSocket messages depending on the STB model. The relevant abstract methods are:

*   **`mo24094e(String str, C15173a c15173a, InterfaceC12596g interfaceC12596g)`**:
    *   Purpose: Handles messages received from the **Command WebSocket**.
    *   Parameters:
        *   `str`: The raw message string received from the WebSocket.
        *   `c15173a`: An instance of `C15173a` (likely `RemoteControlModel`).
        *   `interfaceC12596g`: An instance of `InterfaceC12596g` (likely `RemoteControlCommandListener`).

*   **`mo24093d(String str, C15173a c15173a, InterfaceC12596g interfaceC12596g, InterfaceC16270a interfaceC16270a)`**:
    *   Purpose: Handles messages received from the **Notification WebSocket**.
    *   Parameters:
        *   `str`: The raw message string received from the WebSocket.
        *   `c15173a`: An instance of `C15173a` (likely `RemoteControlModel`).
        *   `interfaceC12596g`: An instance of `InterfaceC12596g` (likely `RemoteControlCommandListener`).
        *   `interfaceC16270a`: An instance of `InterfaceC16270a` (a callback for additional actions).

The `str` parameter in both methods is the key to understanding the message format. The next step is to examine the concrete implementation of these methods for the STB8, which is `p297ln/C13167f.java`.

### `p297ln/C13167f.java` - STB8 Message Handler Implementation

This class provides the concrete implementation of `AbstractC13162a` for STB8 devices.

*   **`mo24094e` (Command WebSocket Response Handling):**
    *   Takes the `commandResponse` string as input.
    *   Delegates parsing to `this.f20780d.m28789a(commandResponse)`, where `f20780d` is an instance of `p361on.C14160b`. This method is expected to return an object of type `C13163b`.
    *   Checks for an error condition ("KO") within the parsed `C13163b` object (`c13163bM28789a.m24098d()`).
    *   If the command is "getStatus", it further parses `c13163bM28789a.m24096b()` using `this.f20780d.m28790b()`, which returns a `C13165d` object. This `C13165d` object is then used to update the remote control model's power status (`remoteControlModel.m32724j(c13165dM28790b.m24099a())`).

*   **`mo24093d` (Notification WebSocket Handling):**
    *   Takes the `notification` string as input.
    *   Delegates parsing to `this.f20780d.m28791c(notification)`, where `f20780d` is an instance of `p361on.C14160b`. This method is expected to return a `Boolean`.
    *   If a `Boolean` is returned, it is used to update the remote control model's power status (`remoteControlModel.m32724j(boolM28791c.booleanValue())`).

**Key Insight:** The `p361on.C14160b` class is central to parsing both command responses and notifications for STB8. The data structures `C13163b` and `C13165d` are also integral to understanding the parsed content.

The next critical step is to analyze the `p361on.C14160b.java` file to understand the actual message formats (likely JSON) and the parsing logic implemented in its `m28789a`, `m28790b`, and `m28791c` methods. We also need to investigate `C13163b` and `C13165d`.

### `p361on.C14160b.java` - WebSocket Message Parser

This class is responsible for parsing the raw WebSocket message strings into structured data. It confirms that JSON is used for WebSocket communication.

*   **`m28789a(String commandResponse)` - Command Response Parser**:
    *   **Input**: A JSON string representing a command response.
    *   **Parsing Logic**:
        *   Creates a `C15457c` object (likely a JSON object wrapper) from the input `commandResponse` string.
        *   Extracts the following fields:
            *   `"remoteResponseCode"`: String.
            *   `"action"`: String (e.g., "getStatus").
            *   `"deviceId"`: String.
            *   `"data"`: A nested JSON object (`C15457c`).
        *   Returns a `C13163b` object, constructed with these extracted values.
    *   **Inferred JSON Structure for Command Responses**:
        ```json
        {
            "remoteResponseCode": "...",
            "action": "...",
            "deviceId": "...",
            "data": {
                // ... contents depend on the action ...
            }
        }
        ```

*   **`m28790b(C15457c getStatusData)` - "getStatus" Data Parser**:
    *   **Input**: A `C15457c` object, specifically the `"data"` field from a "getStatus" command response.
    *   **Parsing Logic**:
        *   Extracts the value of the `"power"` field from the input `C15457c` object.
        *   Compares the value to `"powerOn"`.
        *   Returns a `C13165d` object, which encapsulates the boolean power status (true if "powerOn", false otherwise).
    *   **Inferred JSON Structure for "getStatus" `data` field**:
        ```json
        {
            "power": "powerOn" | "powerOff" | "..."
        }
        ```

*   **`m28791c(String notification)` - Notification Parser**:
    *   **Input**: A JSON string representing a notification.
    *   **Parsing Logic**:
        *   Creates a `C15457c` object from the input `notification` string.
        *   Extracts the nested `"data"` JSON object.
        *   Extracts the `"status"` field from this `"data"` object.
        *   Checks if the `"status"` is either `"powerOn"` or `"powerOff"`.
        *   Returns a `Boolean` (true if "powerOn", false if "powerOff", null otherwise).
    *   **Inferred JSON Structure for Notifications**:
        ```json
        {
            "data": {
                "status": "powerOn" | "powerOff" | "..."
            }
        }
        ```

### `ss.C15457c.java` and `ss.C15456b.java` - Custom JSON Implementation

*   **`C15457c`**: This class appears to be a custom implementation of a `JSONObject`. It provides methods for getting (`m33926m` for String, `m33923j` for nested JSONObject) and putting (`m33911V`) values, as well as converting to string (`m33921h0`). Its constructor `public C15457c(String str)` indicates it can parse a JSON string. The actual parsing is delegated to `C15460f`.
*   **`C15456b`**: This is a custom exception class, likely serving as the `JSONException` for this custom JSON library.

The discovery that a custom JSON library is being used means that the JSON structures inferred from `C14160b` are highly reliable, as they are being directly manipulated by this custom implementation. The obfuscation is not hiding the field names within the JSON itself.

### `ss.C15460f.java` - JSON Tokenizer/Parser

This class acts as the tokenizer (lexer) and parser for the custom JSON implementation.

*   **Functionality**:
    *   Reads character by character from a `Reader` (e.g., `StringReader`).
    *   Identifies JSON tokens (strings, numbers, booleans, null, `[` `]`, `{` `}`, `:` `,`).
    *   Handles escape sequences within string literals.
    *   Delegates the creation of `C15457c` (JSONObject) and `C15455a` (JSONArray) instances when encountering `{` or `[`.
*   **Error Handling**: Uses `C15456b` for reporting JSON parsing errors.

### Summary of the `ss` Custom JSON Library

The `ss` package (`ss.C15457c`, `ss.C15455a`, `ss.C15460f`, `ss.C15456b`) constitutes a custom, self-contained JSON parsing and manipulation library within the APK. This library is similar in functionality to standard JSON libraries but is obfuscated. The field names extracted (`"remoteResponseCode"`, `"action"`, `"deviceId"`, `"data"`, `"power"`, `"status"`) are consistently used as string literals within this custom library, making them reliable for reverse engineering the message formats.

### `p297ln.C13163b.java` - Parsed Command Response Data Structure

This class serves as a data structure to hold the parsed components of a command response received from the STB8.

*   **Constructor Parameters / Fields**:
    *   `remoteResponseCode` (String): The response code from the remote. Accessible via `m24098d()`.
    *   `action` (String): The action that the command response corresponds to. Accessible via `m24095a()`.
    *   `deviceId` (String): The device ID. Accessible via `m24097c()`.
    *   `data` (`ss.C15457c`): A `JSONObject` (custom `C15457c` type) containing additional data related to the response. Accessible via `m24096b()`.

This confirms the high-level structure of command responses: they contain metadata about the response itself (`remoteResponseCode`, `action`, `deviceId`) and a nested `data` object for specific command results.

### `p297ln.C13165d.java` - Parsed "getStatus" Data Structure

This class serves as a data structure to hold the parsed power status information from a "getStatus" command response.

*   **Constructor Parameters / Fields**:
    *   `isPowerOn` (boolean): A boolean indicating whether the device is powered on. Accessible via `m24099a()`.

This confirms that the "getStatus" command response's `data` field contains a simple boolean indicating the power state of the STB8.

### `p297ln.C13165d.java` - Parsed "getStatus" Data Structure

This class serves as a data structure to hold the parsed power status information from a "getStatus" command response.

*   **Constructor Parameters / Fields**:
    *   `isPowerOn` (boolean): A boolean indicating whether the device is powered on. Accessible via `m24099a()`.

This confirms that the "getStatus" command response's `data` field contains a simple boolean indicating the power state of the STB8.

## 5. Command Generation Details

This section details how command JSON messages are constructed and sent to the STB8, based on the analysis of `p361on.C14159a.java`. The methods within this class are responsible for generating the specific JSON payloads for various remote control commands.

### `p361on.C14159a.java` - Command JSON Generator

This class is central to generating the JSON requests sent to the STB8's Command WebSocket.

*   **Command Mapping (`p361on.C14159a.a`)**:
    *   An internal `HashMap` (`f26860d`) maps `C12595f.a` enum values (representing abstract remote control commands like `VOLUME_MORE`, `POWER`, `HOME`) to their specific string representations used in the JSON payloads (e.g., `"volUp"`, `"power"`, `"home"`).

*   **Base Command JSON Construction (`m28776b(String action)`)**:
    *   This private helper method creates the foundational JSON structure for most commands.
    *   **JSON Structure**:
        ```json
        {
            "action": "...",        // The specific command action (e.g., "buttonEvent", "getStatus")
            "deviceId": "...",      // The unique identifier of the STB8
            "requestId": <timestamp> // A unique timestamp for each request
        }
        ```

*   **"buttonEvent" Command Generation (`m28777a(C12595f.a cmd)`)**:
    *   Generates JSON for remote button presses.
    *   Uses the base command JSON with `"action": "buttonEvent"`.
    *   Includes a `"params"` object containing the specific key string.
    *   **JSON Structure**:
        ```json
        {
            "action": "buttonEvent",
            "deviceId": "...",
            "requestId": <timestamp>,
            "params": {
                "key": "volUp" // Example: "volUp", "power", "home", "ok", "0", etc.
            }
        }
        ```

*   **"getStatus" Command Generation (`m28778c()`)**:
    *   Generates JSON to request the STB8's status.
    *   Uses the base command JSON with `"action": "getStatus"`.
    *   **JSON Structure**:
        ```json
        {
            "action": "getStatus",
            "deviceId": "...",
            "requestId": <timestamp>
        }
        ```

*   **"getVersions" Command Generation (`m28779d(String deviceName)`)**:
    *   Generates JSON to request version information from the STB8.
    *   Uses the base command JSON with `"action": "getVersions"`.
    *   Includes a `"params"` object containing the `deviceName`.
    *   **JSON Structure**:
        ```json
        {
            "action": "getVersions",
            "deviceId": "...",
            "requestId": <timestamp>,
            "params": {
                "deviceName": "..." // The user-friendly name of the device
            }
        }
        ```

**Summary of WebSocket Message Structures (Request & Response)**

Combining the analysis of command generation and parsing, we have a clear picture of the JSON structures for interacting with the STB8 via WebSocket:

*   **Command Request Structure (e.g., "buttonEvent", "getStatus", "getVersions")**:
    ```json
    {
        "action": "<command_name>",
        "deviceId": "<device_id>",
        "requestId": <timestamp>,
        "params": {             // Optional, depending on the command
            "<param_key>": "<param_value>"
        }
    }
    ```

*   **Command Response Structure (parsed into `p297ln.C13163b`)**:
    ```json
    {
        "remoteResponseCode": "OK" | "KO", // Response status
        "action": "<command_name>",         // The action this response is for
        "deviceId": "<device_id>",
        "data": {                          // Response data, structure depends on the action
            // For "getStatus" command response:
            "power": "powerOn" | "powerOff"
        }
    }
    ```
    *Note: The `data` field for "getStatus" is parsed into `p297ln.C13165d` which provides an `isPowerOn` boolean.*

*   **Notification Structure (parsed from `ss.C15457c`)**:
    ```json
    {
        "data": {
            "status": "powerOn" | "powerOff" // Current power status
        }
    }
    ```
    *Note: The `status` field in notifications directly indicates the power state.*
