## Class Diagram
```mermaid
classDiagram
    class Wrapper {
        -Int number_of_days
        +initialize(number_of_days)
        +run()
    }

    class HathiTrustItem{
        -String htid
        +initialize(htid)
        +barcode()
    }
    class AlmaItem{
        -String raw_data
        -String htid
        +.for(barcode,htid)
        +initialize(raw_data)
        +has_no_barcode()
        +item_call_num_htid_mismatch()
        +has_matching_htid_in_item_call_num()
        +body_for_update()
    }
    class EmptyAlmaItem{

    }
    AlmaItem <|-- EmptyAlmaItem
    
    Wrapper -- AlmaClient
    Wrapper -- AlmaItem
    AlmaItem -- AlmaClient
    Wrapper -- Report
    Wrapper -- HathiTrustItem
    
    
    class AlmaClient{
        +get_item()
        +update_item()
    }

    class Report{
        -Dict counters
        +initialize(list_of_counters)
        +update_report(kind, message)
    }

 ```

## Sequence Diagram
```mermaid
sequenceDiagram
    Participant W as Wrapper
    Participant AlmaItem as alma_item:AlmaItem
    Participant AlmaClient as alma_client:AlmaClient
    Participant HTItem as ht_item:HTItem
    Participant HF as HathiFiles DB
    Participant Report as report:Report

    W->>HF: get_updated_items()
    HF-->>W: [list] rows from db
    loop Over list of rows
        W->>HTItem: new(row)
        HTItem-->>W: [HTItem] ht_item 

        W->>AlmaItem: new(ht_item.barcode)
        AlmaItem->>AlmaClient: get(barcode)
        alt Alma has barcode
            AlmaClient-->>AlmaItem: [JSON] response body
            AlmaItem-->>W: [AlmaItem] alma_item
        else Alma does not have barcode
             AlmaClient-->>AlmaItem: No barcode
             AlmaItem-->>W: [EmptyAlmaItem] alma_item
        end
        W->>AlmaItem: alma_item.has_no_barcode()
        alt no barcode
            AlmaItem-->>W: true
            W->>Report: no barcode
        else has barcode
            AlmaItem-->>W: false
        end
        W->>AlmaItem: alma_item.item_call_number_mismatch()
        alt there is a mismatch 
            AlmaItem-->>W: true
            W->>Report: mismatch
        else
            AlmaItem-->>W: false
        end
        W->>AlmaClient: update(alma_item.barcode, alma_item.update_body)
        alt successful update
            AlmaClient-->>W: success
            W->>Report: successful_update
        else unsuccessful update
            AlmaClient-->>W: error
            W->>Report: unsuccessful update
        end
    end
```
