# Naming session, shipping service

People kept mixing "delivery", "shipment" and "parcel". We settled it:

- **Shipment** is what leaves the warehouse for one customer address. Don't say delivery or parcel for it.
- A shipment holds one or more **Packages**: a package is one physical box. Avoid "box" and "carton".
- The company that moves it (UPS, DHL, ...) is the **Carrier**. Not courier, not shipper.

Also discussed (not naming): the carrier webhook should retry 3 times with exponential backoff, and we
store the carrier's tracking id in the `carrier_ref` column of the shipments table.
