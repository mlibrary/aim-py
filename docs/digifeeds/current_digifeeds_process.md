# Current Digifeeds Process
## Overall Process
flowchart TD
    A[Scanner] -->|creates scans and puts them in| B[Holding Folder]
    C[Zipper Script] --> |pulls items| B
    C --> |puts zipped items| D[Zipped Folder]
    C --> |generates| E[Barcode List] 
    H[Verifier Script] --> |pulls| E
    H--> |moves zipped items| I[Pickup Area]
    F[Person] --> |pulls| E
    F --> |turns barcodes into| G(Alma Set)  
    H --> |checks| J[HathiTrust Bib API]

## Verifier Script
flowchart TD
    A[Barcode List] --> B{Is each item in zephir?}
    B --> |Yes| C[Move items to pickup area]
    B --> |No| D[Ask Lara to Fix]
    D --> |fix| B
