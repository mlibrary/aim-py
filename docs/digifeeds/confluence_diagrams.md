# Diagrams in Confluence

These are backups of the diagrams in confluence, so we can more easily edit them.

## High level overview

```mermaid
flowchart TD
    A(Digifeeds Process) --> B@{ shape: disk, label: "Folder on Mayhem"}
    A --> C@{shape: cloud, label: "Google SFTP Server"}    

    style B fill:#f7daf7,stroke:#333,stroke-width:4px
    style C fill:#f7daf7,stroke:#333,stroke-width:4px
```

## Digifeeds Process in more detail

```mermaid
flowchart LR
    A(Cronjob on Tang) --> B@{ shape: disk, label: "Folder on Mayhem"}
    A --> S3@{shape: cloud, label: "S3 Bucket"}
    

    Workflow(Workflow in K8s)--> S3  
    Workflow--> |Adds or checks<br>status for barcode| DB@{shape: database, label: "Digifeeds DB"} 
    Workflow --> |Adds barcode to| Alma(Alma Set)
    Workflow --> |Checks if barcode exists| Z(Zephir Bib API) 
    Workflow --> G@{shape: cloud, label: "Google SFTP Server"} 
    

    style B fill:#f7daf7,stroke:#333
    style DB fill:#c6ffff,stroke:#333
    style S3 fill:#f7daf7,stroke:#333
    style G fill:#f7daf7,stroke:#333
```

## Overview of Digifeeds Process CronWorkflow

```mermaid
      flowchart TD
  A(Get list of barcodes from zips in S3 Bucket) 
  B(Divide barcodes into batches of 50 barcodes)
  
  C1{Is there another barcode in the list?} 
  C2(Add Barcode to Digifeeds Alma Set)
  C3(Check Zephir for Barcode)
  C4(Move zip from S3 to Google SFTP Pickup if Ready)

  D1{Is there another barcode in the list?}
  D2(Add Barcode to Digifeeds Alma Set)
  D3(Check Zephir for Barcode)
  D4(Move zip from S3 to Google SFTP Pickup if Ready)

  Z(Send metrics to Prometheus)
  
  A --> B
  B --> C1
  B --> D1

  subgraph \"batch of 50 barcodes\"
    C1 -- yes --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C1
  end
  

  subgraph \"batch of 50 barcodes\"
    D1 -- yes --> D2
    D2 --> D3
    D3 --> D4
    D4 --> D1
  end

C1 -- no --> Z
D1 -- no --> Z

```

## Process Digifeeds Add Item to Digifeeds Set

```mermaid

sequenceDiagram
      Workflow ->> Digifeeds DB: Get or add item for the given Barcode
      Digifeeds DB -->> Workflow: Returns Item information
      alt Item has added_to_digifeeds_set status
        Workflow ->> Workflow: Succeed and continue
      else Item does not have added_to_digifeeds_set status
        critical Add Barcode to digifeeds Alma Set
          Workflow->>Alma API: Add Barcode to Alma Set
        option Barcode Doesn't exist
          Alma API ->> Workflow: Returns Barcode not found error
          Workflow ->> Digifeeds DB: Add not_found_in_alma status to Item
          Workflow ->> Workflow: Error and exit for this barcode
        option Barcode is already there
          Alma API ->> Workflow: Returns Barcode already exists in set error
          Workflow ->> Digifeeds DB: Adds added_to_digifeeds_set status to Item
        option Success
          Alma API ->> Workflow: Successfully added to set
          Workflow->>Digifeeds DB: Adds added_to_digifeeds_set status to item
        end
      end 
```

## Check Zephir for Barcode

```mermaid
      sequenceDiagram
    Workflow ->> Digifeeds DB: Get or add item for the given Barcode
    Digifeeds DB -->> Workflow: Returns Item information
    Workflow ->> Workflow: Does item have in_zephir status?
    alt Item has in_zephir status
      Workflow ->> Workflow: Exit successfully 
    else It does not 
      Workflow ->> Zephir Bib API: Does Zephir have a corresponding record for the Barcode?
      alt It does not
        Zephir Bib API -->> Workflow: 404 or some other error
        Workflow ->> Workflow: Log that the Item is not in Zephir.<br>Exit successfully 
      else It does
        Zephir Bib API -->> Workflow: 200 Success
        Workflow ->> Digifeeds DB: add in_zephir status to Item
        Workflow ->> Workflow: Exit successfully 
      end
    end
```

## Move Zip from S3 to Google SFTP for pickup

```mermaid

sequenceDiagram
    Workflow ->> Digifeeds DB: Get or add item for the given Barcode
    Digifeeds DB -->> Workflow: Returns Item information
    Workflow ->> Workflow: Has the item had an in_zephir status for more than 2 weeks?

    alt It does not meet those conditions
        Workflow ->> Workflow: Log that the Item is not in Zephir.<br> Exit successfully
      else It does meet those conditions
        Workflow ->> Digifeeds DB: Add copying_start status to Item
        Workflow ->> Google SFTP: Copy the corresponding zip from S3 to the Google SFTP
        Workflow ->> Digifeeds DB: Add copying_end status to Item
        Workflow ->> Input S3 Folder: Move the corresponding zip<br> to the Processed Folder in the bucket
        Workflow ->> Digifeeds DB: Add pending_deletion status to Item
      end
```

## Cronjob on Tang

```mermaid

  sequenceDiagram
    Script->>+Input Folder: Gets list of volumes
    loop For every volume folder
      Script->>Input Folder: Copies volume folder to working folder
      Script->>Working Folder: verifies file order
      alt Missing image
        Script-->>Script: Log error and move on to next volume
      else All images are there
        Script->>Working Folder: Zips the appropriate files in the volume folder 
      end
      Script->>+S3 Bucket: Copies zipped file in Working Folder to the S3 Bucket
      Script->>+Processed Folder: Copies the zipped and unzipped volume directory from the working directory to the processed folder
      Script->>Working Folder: Deletes the zipped and unzipped volume directory
      Script->>Input Folder: Deletes the volume directory 
    end
    Script->>Script: Logs summary of process
    Script->>+Prometheus Pushgateway: Sends completions time metric

```
