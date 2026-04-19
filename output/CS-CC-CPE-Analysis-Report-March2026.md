# CPE Priority Destination Analysis — March 2026
**Generated:** 2026-04-19  
**Prepared by:** CSUSA DataLake  
**Data Source:** Wolfpack Mobile Platform Export + CP/VLO Priority Lists

---

## Overview

This report analyzes all completed crude oil haul tickets from the CP Energy Transportation mobile platform for March 2026. It compares each ticket's actual delivery destination against the priority destinations uploaded from the Wolfpack ERP system for CP Energy and Valero, identifies loads that did not go to their Priority 1 station, and flags those missing mileage data for resolution.

---

## Data Sources

| File | Description | Records |
|------|-------------|---------|
| CPE Export (Mobile Platform) | All completed tickets, March 2026 | 11,684 |
| Priority List — CP Energy | Lease → Priority 1 station, CP purchaser | 3,811 leases |
| Priority List — Valero (VLO) | Lease → Priority 1 station, VLO purchaser | 3,915 leases |
| Split Destinations | 4 leases requiring volume splits across 2 stations | 4 leases / 8 rows |

**Date range:** February 9, 2026 – March 31, 2026  
(17 tickets are late-reported February loads; 11,667 are March loads)  
**All 11,684 tickets are status = Completed (C). No rejected or draft tickets included.**

---

## Data Model

```
Split Destinations ──┐
                     ↓
CP Priority List ──→ [Lease Number → Priority 1 Station, Mileage]
VLO Priority List ──→ [Lease Number → Priority 1 Station, Mileage]
         ↑
         └── Join on lease_number
         
Export (Tickets) ── lease_number, destination_name, purchaser_name, barrels_net, load_date
```

The CP and VLO priority lists are **dispatch tables** — given a lease, they define where the load should go (Priority 1 station) and the agreed mileage. The Export records what actually happened.

**Station Name Normalization:** The priority lists use abbreviated base station names
(e.g., "ARNETT", "PERRYTON", "TROJAN") while the mobile platform uses specific
lane/entry names (e.g., "ARNETT STATION LANE 7", "CP - PERRYTON 4", "CP TROJAN 2 - NGL").
These are the same physical stations. The analysis accounts for this mapping.

**Split Destinations** override the CP/VLO priority entry for 4 leases where volume must
be divided between two stations:

| Lease | Operator | Priority 1 Station | Priority 2 Station | Volume Split |
|-------|----------|-------------------|-------------------|-------------|
| SAPPHIRE | Devon Gas Services | TROJAN | RUBY | 250 / 150 bbl |
| SNEE0001 | HRR II Acquisition | CP - SUNRAY-MCKEE | CLAWSON | 110 / 90 bbl |
| MIDC0001 | Mid Con Gas Corp | CHEROKEE LACT 306 | RUBY | 86 / 24 bbl |
| LIBE0002 | Phillips 66 | PERRYTON | CP - HOOKER | 307 / 168 bbl |

---

## Results Summary

| Category | Tickets | Barrels |
|----------|---------|---------|
| **Went to Priority 1 station** | 9,799 | 1,687,175 |
| Non-Priority-1, mileage on file (no action needed) | 1,011 | — |
| **Non-Priority-1, mileage MISSING (actionable)** | **874** | **134,264** |
| **Total** | **11,684** | |

**83.9% of loads went to their Priority 1 station.**  
**874 loads went to a non-priority-1 destination and have no mileage on file** — these are the records requiring manual mileage resolution (currently handled via email).

---

## Query 1 — Loads That Went to Priority 1 (9,799 tickets)

These loads are operating as intended. Full detail in `CS-CC-query1_priority1_correct_*.csv`.

**By Priority List Source:**

| Source | Tickets |
|--------|---------|
| Valero (VLO) | 6,239 |
| CP Energy (CP) | 3,400 |
| Split Destinations | 160 |

**By Purchaser:**

| Purchaser | Tickets |
|-----------|---------|
| CP Energy, LLC | 9,794 |
| CP Energy Transportation, LLC | 5 |

**Output columns:** Ticket Number, Load Date, Lease Number, Lease Name, Operator, Purchaser, Priority Source, Priority 1 Station, Priority 1 Mileage, Actual Destination, Destination Code, Barrels Net

---

## Query 2 — Non-Priority-1 Loads, Mileage Missing (874 tickets)

These are the actionable records. Full detail in `CS-CC-query2_not_priority1_*.csv`.

**By Priority List Source:**

| Source | Tickets | Meaning |
|--------|---------|---------|
| NOT ON LIST | 631 | Lease does not appear on any CP or VLO priority list |
| CP Energy (CP) | 123 | Lease is on CP list but went elsewhere, no mileage |
| Valero (VLO) | 84 | Lease is on VLO list but went elsewhere, no mileage |
| Split Destinations | 36 | Split lease went to unexpected destination, no mileage |

**Top Actual Destinations (non-Priority-1, missing mileage):**

| Destination | Tickets | Unique Leases |
|-------------|---------|--------------|
| ARNETT LANES 1-4 | 141 | 48 |
| TROJAN STATION | 72 | 17 |
| CP TROJAN 2 - NGL | 66 | 6 |
| CP - PERRYTON 4 | 60 | 45 |
| CP TROJAN 3 - ETC | 49 | 3 |
| CP - HOOKER | 44 | 29 |
| CP - CLAWSON 3 | 42 | 15 |
| CP - PIPER 4 | 39 | 26 |
| ARNETT STATION LANE 7 | 27 | 21 |
| ARNETT STATION LANE 5 | 26 | 14 |
| CP - PERRYTON 1 | 24 | 21 |
| ARNETT STATIONS LANES 1-4 | 22 | 10 |
| ARNETT STATION (NAVI) | 20 | 15 |
| ARNETT STATION LANE 6 | 20 | 10 |
| CP - PERRYTON 2 | 19 | 19 |
| CP - CLAWSON 1 | 18 | 8 |
| CP - PIPER 3 | 15 | 13 |
| RED STAG STATION | 15 | 14 |
| NAV CALUMET STATION | 15 | 12 |
| CP - CLAWSON 2 | 14 | 8 |

**Top Leases with Missing Mileage:**

| Lease Number | Lease Name | Tickets Missing Mileage |
|-------------|------------|------------------------|
| AMBA1931 | AMBASSADOR INN 19/31 DM #1H | 105 |
| MON18192 | MONTGOMERY 18/19 DM 2H | 63 |
| KLEIN031 | KLEIN 3 BO #1H | 54 |
| WATER718 | WATERLOO 7 18 15N-23W 1H | 42 |
| SNEE0001 | SNEED PLANT | 36 |
| SOLO0018 | SOLO 1-8H | 15 |
| HEMP0003 | HEMPHILL PLANT (SUPERIOR) | 13 |
| 513730 | MILLER FIELDER CTB | 11 |
| BERR0074 | BERRYMAN CTB | 11 |
| 513507 | MILLER 6 CTB | 9 |

**Output columns:** Ticket Number, Load Date, Lease Number, Lease Name, Operator, Purchaser, Priority Source, Priority 1 Station, Actual Destination, Destination Code, Barrels Net, Notes

---

## Key Observations

1. **631 of 874 missing-mileage tickets (72%) involve leases not on any priority list.**
   These leases exist in the mobile platform but were not included in either the CP or VLO
   priority upload for March. They may represent new leases, temporary hauls, or leases
   that should have been on the list.

2. **The top 5 leases account for 299 of 874 records (34%).**
   Resolving mileage for AMBA1931, MON18192, KLEIN031, WATER718, and SNEE0001 alone
   would close out a third of the backlog.

3. **ARNETT-family destinations account for 279 of 874 tickets (32%).**
   Loads going to any Arnett lane without a matching priority assignment are the single
   largest destination group. Many of these may share the same mileage from the lease.

4. **The future history lookup** (querying 10–15K prior monthly tickets for matching
   lease → destination combinations) would resolve the majority of these automatically,
   eliminating the current email workflow.

---

## Output Files

| File | Description |
|------|-------------|
| `CS-CC-query1_priority1_correct_*.csv` | All 9,799 loads that went to Priority 1 |
| `CS-CC-query2_not_priority1_*.csv` | 874 non-priority-1 loads with no mileage |
| `CS-CC-analysis_report_*.txt` | Machine-generated summary report |
| `CS-CC-CPE-Analysis-Report-March2026.md` | This document |
