# Foxsy Tournament Manager

## Introduction

Foxsy Tournament Manager is a system that can manage the tournament of Soccer Simulation Game.

## Workflow

```mermaid
flowchart TD
    subgraph Computer1
        TM[TournamanetManager]
        TMDB[TMDatabase]
        MQ[MessageQueue]
        S((MinioStorage))
    end
    subgraph Computer2
        R1[Runner1]
    end
    subgraph Computer3
        R2[Runner2]
    end
    TM -- GameInfo --> MQ
    MQ -- GameInfo --> R1
    MQ -- GameInfo --> R2
    TM <--> TMDB
    R1 <--> S
    R2 <--> S
    R1 -.-> TM
    R2 -.-> TM
```

```mermaid
sequenceDiagram
    participant A as API | SmartContract
    participant TM as TournamanetManager
    participant RMDB as RMDatabase
    participant MQ as MessageQueue
    participant R as Runner
    participant S as Storage
    A->>TM: TournamentInfo
    Note over TM: Create Tournament
    TM->>RMDB: Add Tournament
    TM->>RMDB: Add Teams
    TM->>RMDB: Add Games
    TM->>MQ: GameInfo
    MQ-->>R: GameInfo
    R->>S: Get TeamConfig, Bases, Server
    S->>R: TeamConfig, Bases, Server
    R->>TM: Game Status (GameStarted)
    TM->>RMDB: Update Game
    Note over R: Running Game
    R->>S: SaveGameLog
    R->>TM: Game Status (GameFinished)
    TM->>RMDB: Update Game
```
