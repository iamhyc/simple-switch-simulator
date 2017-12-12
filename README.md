## Demo

Simple link switch or aggregation simulator.

And a cache node controller based on Content-request service (P/S struct).



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

|   TYPE   |  PARAM1   | PARAM2 | PARAM3 | PARAM4 |
| :------: | :-------: | :----: | :----: | :----: |
| SRC-NOW  | HASH_NAME |  SIZE  | LENGTH |        |
|    LS    |           |        |        |        |
| SRC-TYPE |   TYPE    |        |        |        |
|   IDLE   |           |        |        |        |

## Terminal Type

|                      | STREAM REDIST | CONTENT REDIST |
| :------------------: | :-----------: | :------------: |
|  **FINITE COUNTER**  |     relay     |    *cache*     |
| **INFINITE COUNTER** |     relay     |   non-sense    |

