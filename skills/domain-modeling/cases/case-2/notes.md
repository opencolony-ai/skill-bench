# Clinic scheduling: words we agreed on

- **Appointment**: a patient's reserved time with one practitioner. We stop saying "booking" and "visit".
- **Slot**: a period a practitioner has made available, which may or may not hold an appointment. Not "opening", not "availability".
- **Patient**: the person being seen. Never "client" or "customer".
- **Practitioner**: anyone who sees patients (doctors, nurses, physios). Avoid "doctor" and "provider" for the general role.

Tech notes from the same meeting: cache the slot list with a 5-minute TTL; the booking endpoint returns JSON.
