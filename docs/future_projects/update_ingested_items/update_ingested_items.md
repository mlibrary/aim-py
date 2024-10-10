# Update Ingested Items
This is how the perl/bash script currently works, not how it should work.

How to figure out the `barcode`:
* for `miua` and `miun` the `htid` is the `barcode`
* for `mdp` the barcode is everything after `mdp.`

```mermaid
flowchart TD
    A[Get list of HT items that<br>have been updated since yesterday] --> B(Iterate over each<br>HT item)
    B --> C[Get Namespace and Barcode]
    C -->D(Ask Alma about barcode)
    D --> E{Was barcode</br>found in Alma?}
    E -- Yes --> F{Does item<br>have item call number<br>that matches htid?}
    E -- No --> G(Increase barcode_not_found counter<br> Go to next item)
    F -- No --> I{Does item<br>have item call number<br>that differs from htid?}
    F -- Yes --> H[Increase no_upd counter;<br>Go to next item]
    I -- Yes --> J[Print Mismatch]
    I -- No --> K[Update Item]
    J --> K
    K --> L{Success?}
    L -- Yes --> M[Increase update_cnt counter;<br>Go to next item]
    L -- No --> N[Print error; Go to Next item]
```
