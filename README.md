## Demo

Simple link switch or aggregation simulator.

And a cache node controller based on Content-request service (P/S struct).

## Excutable File & Modules

* *Console.py*: Script interface with helper function
* *tap-generator.py*: TAP for customized Random packets
* *Dispatcher.py*: Top-level Stream service at Tx side
* *Terminal.py*: Top-level Stream service at Rx side
* *Utility Module*: Collection of useful functions.

## Console on Dispatcher Side

|  Type   | PARAM1  | PARAM2 | PARAM3  | PARAM4 |
| :-----: | :-----: | :----: | :-----: | :----: |
|   ADD   | WiFi_IP | VLC_IP | RC_FLAG |        |
|   LS    |         |        |         |        |
|   RM    |   ID    |        |         |        |
|   SRC   |   ID    |  TYPE  |  DATA   |        |
|   SRC   |   ID    |  KEY   |  VALUE  |        |
| SRC-NOW |   ID    |        |         |        |
|  IDLE   |   ID    |        |         |        |

## Console on Terminal Side

|   TYPE   | PARAM1 |  PARAM2   | PARAM3 | PARAM4 |
| :------: | :----: | :-------: | :----: | :----: |
| SRC-NOW  |  TYPE  | HASH_NAME |  SIZE  | LENGTH |
|    LS    |        |           |        |        |
| SRC-TYPE |  TYPE  |           |        |        |
|   IDLE   |        |           |        |        |

## Terminal Type

|                      | STREAM REDIST | CONTENT REDIST |
| :------------------: | :-----------: | :------------: |
|  **FINITE COUNTER**  |     relay     |    *cache*     |
| **INFINITE COUNTER** |     relay     |   non-sense    |

