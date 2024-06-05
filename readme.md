# Foxsy Tournament Manager

## Introduction

Foxsy Tournament Manager is a system that can manage the tournament of Soccer Simulation Game.

## Workflow

```mermaid
flowchart TD
    subgraph Computer1
        RM[RunnerManager]
        RMDB[RMDatabase]
        MQ[MessageQueue]
    end
    subgraph Computer2
        R1[Runner1]
    end
    subgraph Computer3
        R2[Runner2]
    end
    subgraph Computer4
        S[Storage]
    end
    R1 <--> MQ
    R2 <--> MQ
    RM <--> RMDB
    RM <--> MQ
    RM <--> S
    R1 <--> S
    R2 <--> S
```

```mermaid
sequenceDiagram
    participant A as API | TournamentManager
    participant RM as RunnerManager
    participant RMDB as RMDatabase
    participant MQ as MessageQueue
    participant R as Runner
    participant S as Storage
    A->>RM: GameInfo
    RM->>RMDB: Add GameInfo
    Note over RM: Add Game Id to GameInfo
    RM->>MQ: GameInfo
    MQ-->>R: GameInfo
    R->>S: GetTeamConfig
    S->>R: TeamConfig
    R->>MQ: Game Status
    Note over R: Running Game
    MQ-->>RM: Game Status
    RM->>RMDB: Update Game
    R->>S: SaveGameLog
    R->>MQ: Game Status
    MQ-->>RM: Game Status
    RM->>RMDB: Update Game
    RM->>A: Game Status
    A->>S: GetGameLog
    S->>A: GameLog
```

- GameInfo: GameId, Left Team Name, Right Team Name, Left Team Config, Right Team Config, Server Config

- Team Config:

```json
{
    "TeamBase": "CYRUS",
    "Config":{
        "Version": "1"
    },
    // or
    "Config":{
        "Formation": "4-4-2",
        "Offensive": "0 - 10",
        "Defensive": "0 - 10",
        "Risk": "0 - 10"
    },
    // or
    "Config":"config id: path to config dir"
}
```

## RunnerManager

RunnerManager is a fastAPI application that can receive GameInfo or list of GameInfo and send the GameInfo to the Runner by using RabitMQ or calling API of the Runner.

RunnerManager is responsible for managing the GameInfo and GameStatus. It will store the GameInfo and GameStatus in the database.

RunnerManager is also responsible to validate the team config and server config.

## Runner

Runner is a fastAPI application or is able to read messages from RabitMQ.
Runner is respopnsible for running the game and sending the game status to the RunnerManager, also saves the game log to the storage.
If the Runner is a fastAPI application, it should call the RunnerManager API to update the game status and register itself to the RunnerManager.

## Tournament Manager

```mermaid
flowchart TD
    subgraph Computer0
        TM[TournamentManager]
    end
    subgraph Computer1
        RM[RunnerManager]
        RMDB[RMDatabase]
        MQ[MessageQueue]
    end
    subgraph Computer2
        R1[Runner1]
    end
    subgraph Computer4
        S[Storage]
    end
    TM <--> RM
    R1 <--> MQ
    RM <--> RMDB
    RM <--> MQ
    RM <--> S
    R1 <--> S
```

```mermaid
sequenceDiagram
    participant U as User
    participant TM as TournamentManager
    participant RM as RunnerManager
    participant MQ as MessageQueue
    participant R as Runner
    U->>TM: CreateTournament
    U->>TM: AddTeam
    U->>TM: AddTeam
    U->>TM: StartTournament
    TM->>RM: List[GameInfo]
    Note over RM: Add Game Id to GameInfo
    RM->>MQ: GameInfo
    MQ-->>R: GameInfo
    R->>MQ: Game Status
    Note over R: Running Game
    MQ-->>RM: Game Status
    R->>MQ: Game Status
    MQ-->>RM: Game Status
    RM->>TM: Game Status
    TM->>U: Game Status
```