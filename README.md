## Demo

Simple link switch or aggregation simulator. And a cache node controller based on content-request service (P/S struct).

![structure](./structure.png)

## Backend Structure

**Cache** registers at **Dispatcher**.

(should disattach *data source* from **Distributor** to the control of **Dispatcher**)

|        SERVER SIDE        |     FILES      |       CACHE SIDE        |     FILES     |
| :-----------------------: | :------------: | :---------------------: | :-----------: |
| **Content Publish Layer** |  Publisher.py  | **Content Proxy Layer** |   Proxy.py    |
|   **Convergence Layer**   | Dispatcher.py  |                         |               |
|    **Data Flow Layer**    | Distributor.py |   **Data Flow Layer**   | Aggregator.py |
|                           |                |                         |               |

## Frontend Structure

**Client** registers at **Publisher**.

|     SCHEMA     |        REQUEST        |               RESPONSE                |
| :------------: | :-------------------: | :-----------------------------------: |
|  Dual-Request  | at most twice/content | lack of popular statistical  feedback |
| Request-Proxy  |     once/content      |     lack of cache uplink control      |
| Request-Redist |     once/content      |      overhead if request redist       |
|                |                       |                                       |

## TODO

* **Distributor** window control for failure safe re-transmission
* solve order error at **Aggregator**
* modify and build the **content service** and **cache node** structure
* determine the client request schema