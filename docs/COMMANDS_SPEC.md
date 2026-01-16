# SFR Box Command & Payload Specification

## 1. Objective

This document defines the command and control architecture for all supported SFR Box models. Its purpose is to document the abstract command system, the specific JSON payloads for each model, and any shared constants or data structures, ensuring a flexible and maintainable implementation.

## 2. Core Architectural Principles

The control system is built on two core principles:

- **Command Abstraction**: A common set of abstract command names (defined by the `CommandType` enum in `sfr_box_core/constants.py`) will be used across the library (e.g., `SEND_KEY`, `GET_STATUS`). This provides a consistent API for any client using the library, regardless of the box model being controlled.
- **Polymorphic Implementation (Strategy Pattern)**: Each box-specific driver (`stb8_driver.py`, `stb7_driver.py`, `labox_driver.py`, etc.) is responsible for translating these abstract commands into the correct JSON payload required by its specific hardware model. The `base_driver.py` will provide the common interface for executing these commands (e.g., `send_command(command, **params)`).

### 3.1 KeyCodes

The abstract `KeyCode` names (e.g., `POWER`, `VOL_UP`) are shared across box models. However, the *values* sent in the payload are different. This is a perfect use case for a polymorphic implementation. A shared `KeyCode` Enum will be used, and each driver will map its enum members to the correct value (string or int).

#### STB8 KeyCode Values

The following **string** values are used for STB8.

| Abstract Name | String Value     |
| :------------ | :--------------- |
| `VOL_UP`      | `volUp`          |
... *(table remains the same)*
| `NUM_9`       | `9`              |

#### STB7 KeyCode Values

The following **integer** values are used for STB7. Note that `STOP` and `OK` have different values than standard ASCII.

| Abstract Name | Integer Value |
| :------------ | :------------ |
| `VOL_UP`      | `308`         |
| `VOL_DOWN`    | `307`         |
| `CHAN_UP`     | `290`         |
| `CHAN_DOWN`   | `291`         |
| `HOME`        | `292`         |
| `BACK`        | `27`          |
| `POWER`       | `303`         |
| `FFWD`        | `305`         |
| `REWIND`      | `304`         |
| `PLAY_PAUSE`  | `306`         |
| `STOP`        | `19`          |
| `RECORD`      | `309`         |
| `MUTE`        | `302`         |
| `UP`          | `297`         |
| `LEFT`        | `293`         |
| `RIGHT`       | `222`         |
| `DOWN`        | `294`         |
| `OK`          | `13`          |
| `NUM_0`       | `48`          |
... *(and so on for 1-9)*
| `NUM_9`       | `57`          |
| `DELETE`      | `8`           |
| `OPTIONS`     | `301`         |

#### LaBox KeyCode Values

The following **integer** values are used for LaBox. Note that many are different from STB7.

| Abstract Name | Integer Value |
| :------------ | :------------ |
| `VOL_UP`      | `63234`       |
| `VOL_DOWN`    | `63235`       |
| `CHAN_UP`     | `63237`       |
| `CHAN_DOWN`   | `63236`       |
| `HOME`        | `63270`       |
| `BACK`        | `63271`       |
| `POWER`       | `63232`       |
| `FFWD`        | `63244`       |
| `REWIND`      | `63243`       |
| `PLAY_PAUSE`  | `63241`       |
| `STOP`        | `63238`       |
| `RECORD`      | `63242`       |
| `MUTE`        | `63233`       |
| `UP`          | `38`          |
| `LEFT`        | `37`          |
| `RIGHT`       | `39`          |
| `DOWN`        | `40`          |
| `OK`          | `13`          |
| `NUM_0`       | `48`          |
... *(and so on for 1-9)*
| `NUM_9`       | `57`          |
| `DELETE`      | `8`           |
| `OPTIONS`     | `63273`       |

## 4. Command Specification by Model

This section contains the detailed command specifications for each model.

### 4.1 STB8 Commands

All STB8 commands share a base structure with **camelCase** keys:

```json
{
    "action": "...",
    "deviceId": "...",
    "requestId": 1678886400000
}
```

---
**Commands:**

| Abstract Command | Parameters                  | Payload (`action` & `params` object)                                 |
| :--------------- | :-------------------------- | :------------------------------------------------------------------- |
| `SEND_KEY`       | `key: KeyCode` (Enum)       | `{"action": "buttonEvent", "params": {"key": "{key.value}"}}`          |
| `GET_STATUS`     | None                        | `{"action": "getStatus"}`                                            |
| `GET_VERSIONS`   | `device_name: str`          | `{"action": "getVersions", "params": {"deviceName": "{device_name}"}}` |

---

### 4.2 STB7 Commands

All STB7 commands are wrapped in a `Params` object and use **PascalCase** keys.
The base `Params` object looks like this:

```json
{
    "Params": {
        "Action": "...",
        "Token": "LAN",
        "DeviceModel": "...",
        "DeviceSoftVersion": "...",
        "DeviceId": "..."
    }
}
```

---
**Commands:**

| Abstract Command | Parameters            | Payload (`Action` & inner `Press` object)                     |
| :--------------- | :-------------------- | :-------------------------------------------------------------- |
| `SEND_KEY`       | `key: KeyCode` (Enum) | `{"Action": "ButtonEvent", "Press": ["{key.value}"]}` (Note: keycode is in an array) |
| `GET_STATUS`     | None                  | `{"Action": "GetSessionsStatus"}`                               |
| `GET_VERSIONS`   | None                  | `{"Action": "GetVersions"}`                                     |

---

### 4.3 LaBox & EVO Commands

**LaBox:** The command architecture for LaBox is **identical to STB7**. It uses the same `{"Params": ...}` wrapper, `PascalCase` keys, and `Action` names. The command executor for LaBox is found in `p297ln/C13164c.java`. The only difference is the set of integer values used for the `KeyCode` parameter in the `SEND_KEY` command (documented in Section 3.1).

**EVO:** *(This section will be populated with findings from the EVO source files.)*

## 5. Response & Notification Payloads

### 5.1 STB8 Responses & Notifications

#### 5.1 STB8 Generic Response Wrapper

```json
{
    "remoteResponseCode": "OK" | "KO",
    "action": "...",
    "deviceId": "...",
    "data": {}
}
```

(Note: "KO" was found as a consistent failure code across STB8, STB7, and LaBox. "OK" is inferred for success.)

#### 5.1 STB8 `GET_STATUS` Response Data

The `data` object contains `{"power": "powerOn"}`.

#### Power State Notification

Unsolicited notifications about power state changes have this structure:

```json
{
    "data": {
        "status": "powerOn"
    }
}
```

(Note: "powerOff" is also a confirmed value)

### 5.2 STB7 & LaBox Responses & Notifications

#### 5.2 STB7 & LaBox Generic Response Wrapper

Keys use **PascalCase**. The structure is identical for both STB7 and LaBox.

```json
{
    "RemoteResponseCode": "OK" | "KO",
    "Action": "...",
    "DeviceId": "...",
    "Data": {}
}
```

(Note: "KO" was found as a consistent failure code across STB8, STB7, and LaBox. "OK" is inferred for success.)

#### 5.2 STB7 & LaBox `GET_STATUS` Response Data

The `Data` object for a `GetSessionsStatus` response contains `{"CurrentApplication": "En Veille"}` to indicate the standby state. If not in standby, this key may have a different value or be absent.

#### Notification

The payload is wrapped in a top-level `Notification` key: `{"Notification": ...}`.

## 6. Open Questions

- What are all possible values for STB7/LaBox `CurrentApplication` status (besides `"En Veille"`)? (Currently, we assume any other value means the box is "active".)
