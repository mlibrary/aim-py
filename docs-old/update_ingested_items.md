```mermaid
flowchart TD
    A[Get list of HT items that\nhave been updated since yesterday] --> B(Iterate over each\nHT item)
    B --> C[Get Namespace and Barcode]
    C -->D(Ask Alma about barcode)
    D --> E{Was barcode\nfound in Alma?}
    E -- Yes --> F{Does item\nhave item call number\nthat matches htid?}
    E -- No --> G(Increase barcode_not_found counter\n Go to next item)
    F -- No --> I{Does item\nhave item call number\nthat differs from htid?}
    F -- Yes --> H[Increase no_upd counter;\nGo to next item]
    I -- Yes --> J[Print Mismatch]
    I -- No --> K[Update Item]
    J --> K
    K --> L{Success?}
    L -- Yes --> M[Increase update_cnt counter;\nGo to next item]
    L -- No --> N[Print error; Go to Next item]
```
This is how the perl/bash script currently works, not how it should work.

How to figure out the `barcode`:
* for `miua` and `miun` the `htid` is the `barcode`
* for `mdp` the barcode is everything after `mdp.`
