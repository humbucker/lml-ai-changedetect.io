# Venue Change Status API

A read-only API that returns the change status for all LML-monitored venue websites.
One entry per venue, deduplicated by LML UUID.

The venues covered are all venues listed in **LML Admin Central** that have a public website URL — sourced directly from the Admin Central spreadsheet tabs for Geelong, Fitzroy/Yarra, St Kilda, Queenscliff, Goldfields, and Surf Coast. Facebook-only and Instagram-only venues are excluded as they cannot be reliably monitored. 250 venues in total.

## Base URL

```
https://venue-status.thorpes.org
```

No authentication required. Publicly accessible.

---

## Endpoints

### `GET /venue-change-status`

Returns the change status for every monitored venue.

**Response:** JSON array, one object per venue, sorted by location then name.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `lml_uuid` | string | Optional. Filter to a single venue by LML UUID. Returns a single object instead of an array. Use `all` or omit for all venues. |
| `changed_since` | YYYY-MM-DD | Optional. Return only venues where a change was detected on or after this date. |

**Examples:**

All venues:
```
https://venue-status.thorpes.org/venue-change-status
```

Single venue by LML UUID:
```
https://venue-status.thorpes.org/venue-change-status?lml_uuid=1a51e558-1f5b-4329-9dc7-79fcb55dccad
```

All venues that changed since a given date:
```
https://venue-status.thorpes.org/venue-change-status?changed_since=2026-07-01
```

All venues in a location that changed since a date *(filter client-side on `location` field)*:
```
https://venue-status.thorpes.org/venue-change-status?changed_since=2026-07-01
```

Single venue — did it change since a given date?:
```
https://venue-status.thorpes.org/venue-change-status?lml_uuid=1a51e558-1f5b-4329-9dc7-79fcb55dccad&changed_since=2026-07-01
```

Health check:
```
https://venue-status.thorpes.org/health
```

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `lml_uuid` | string or null | LML venue ID. Null for venues not yet in LML. |
| `name` | string | Venue name |
| `location` | string | Region — Geelong, Fitzroy, St Kilda, Queenscliff, Goldfields, Surf Coast |
| `status` | string | `changed` or `no_change` |
| `since` | YYYY-MM-DD | For `no_change`: date of last detected change (start of no-change streak). For `changed`: date the change was detected. |
| `last_changed` | YYYY-MM-DD or null | Date of the most recent detected change. Null if the page has never changed since monitoring began. |
| `last_checked` | YYYY-MM-DD | Date the page was last fetched |
| `url` | string | The venue website URL being monitored |

**Status logic:**
- `changed` — the page changed within the last 7 days
- `no_change` — no change detected in the last 7 days

**Example response:**
```json
[
  {
    "lml_uuid": "1a51e558-1f5b-4329-9dc7-79fcb55dccad",
    "name": "The Barwon Club Hotel",
    "location": "Geelong",
    "status": "no_change",
    "since": "2026-04-12",
    "last_changed": "2026-04-12",
    "last_checked": "2026-07-01",
    "url": "https://www.barwonclub.com.au/gig-guide/"
  },
  {
    "lml_uuid": "0f7d1c80-f3cf-4250-ba14-6ff5fa1a397a",
    "name": "Tote Hotel",
    "location": "Fitzroy",
    "status": "changed",
    "since": "2026-06-28",
    "last_changed": "2026-06-28",
    "last_checked": "2026-07-01",
    "url": "https://thetotehotel.com/gig-guide/"
  }
]
```

---

### `GET /health`

Health check.

```
GET https://venue-status.thorpes.org/health
```

```json
{"status": "ok"}
```

---

## Coverage

250 venues monitored across 6 regions:

| Region | Description |
|---|---|
| Geelong | Geelong and Bellarine Peninsula |
| Fitzroy | Fitzroy, Collingwood, Richmond and inner north/east Melbourne |
| St Kilda | St Kilda, Port Melbourne and inner south Melbourne |
| Queenscliff | Queenscliff and Bellarine coast |
| Goldfields | Bendigo, Castlemaine, Maldon, Ballarat and surrounds |
| Surf Coast | Torquay, Anglesea, Lorne and Great Ocean Road |

---

## Notes

- Checks run every **Monday at 8am AEST** (scheduled via changedetection.io)
- Underlying infrastructure: [changedetection.io](https://changedetection.thorpes.org) running on a Raspberry Pi 400, exposed via Cloudflare Tunnel
- Some venues have two URLs monitored (e.g. main website + Eventbrite page). The API deduplicates by `lml_uuid`, returning the result for whichever URL changed most recently
- Venues with `lml_uuid: null` are being monitored but are not yet in the LML database
- `status: changed` means something on the page changed — it does not indicate whether the change is gig-related. A human still needs to review the diff.
- The 7-day change window resets each Monday after the weekly check runs

---

## Related

- changedetection.io UI: https://changedetection.thorpes.org
- changedetection.io API: https://changedetection.thorpes.org/api/v1/watch *(requires API key)*
- LML API: `https://api.lml.live/gigs/query?location=geelong&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
