# Proposed Digifeeds Process
## Overview
```mermaid
flowchart TD
    A[Folder with Scans]
    B[Argo Events]
    C[New item workflow]
    D[Is item in DB?]
    E[Has it been added to an Alma set?]
    F[Add to DB]
    G[Add to digifeeds set\nAdd status of added_to_digifeeds_set]

    B --Notices there's a new file--> A
    B --> C
    C --> D
    F --> E
    D --No --> F
    D --Yes--> E
    E --No --> G
    E --Yes--> U[Skip]

    L[Daily, Get items where in_zephir is false] --> M[Check zephir for item. Is it there?]
    M --No -->O[Skip]
    M --Yes -->P[Add in_zephir status]

    H[Daily, check the Folder with Scans] --> I[For every barcode,\ndoes it have an in_zephir status?\nAND \nhas it been two weeks since the in_zephir status got created?]
    I --No --> N[Skip]
    I --Yes--> J[Add start copying status;\nZip and Copy it to pickup location;\nAdd finished copying status]
    J --> K[Rename or move item in Folder with Scans;\nAdd pending_deletion status]

    Q[Monthly or less frequent, Get the digifeeds set] --> R[Does the item have an item call number?]
    R -- No --> S[Do nothing]
    R --Yes --> T[Remove from digifeeds set]
```
## Database tables
```mermaid
erDiagram
    ITEM ||--o{ ITEM_STATUS : has_many
    ITEM {
        string barcode
    
    }

    ITEM_STATUS {
        string item_barcode
        string status_name
        date date
    }

    STATUS {
        string name
        string description
    }
    STATUS ||--o{ ITEM_STATUS: has_many
```

## CLI scripts
```
aim digifeeds check_zephir
aim digifeeds zip_and_move_to_pickup
aim digifeeds add_to_db BARCODE
aim digifeeds purge_digifeeds_alma_set
```
