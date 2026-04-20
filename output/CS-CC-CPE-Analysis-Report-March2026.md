# CPE Priority Destination Analysis — March 2026
**Generated:** 2026-04-20  
**Prepared by:** CSUSA DataLake  
**Data Source:** Wolfpack Mobile Platform Export + CP/VLO Priority Lists

---

## Overview

This report analyzes all completed crude oil haul tickets from the CP Energy Transportation mobile platform for March 2026. It compares each ticket's actual delivery destination against the priority destinations uploaded from the Wolfpack ERP system for CP Energy and Valero, identifies all loads that did not go to their Priority 1 station, and isolates those with a Priority 1 assignment that delivered elsewhere.

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

| Category | Tickets | % of Total | Barrels | % of Total |
|----------|---------|-----------|---------|-----------|
| **Query 1 — Went to Priority 1** | 9,799 | 83.9% | 1,687,175 | 84.5% |
| **Query 2 — Did NOT go to Priority 1** | 1,885 | 16.1% | 309,732 | 15.5% |
| &nbsp;&nbsp;&nbsp;Query 3 — On-list, wrong destination (subset of Q2) | 383 | 3.3% | 63,559 | 3.2% |
| &nbsp;&nbsp;&nbsp;Not on any priority list (subset of Q2) | 1,502 | 12.9% | 246,173 | 12.3% |
| **Total** | **11,684** | **100%** | **1,996,907** | **100%** |

**Reconciliation:** Q1 (9,799) + Q2 (1,885) = 11,684 ✓ &nbsp;|&nbsp; Q3 (383) + NOT ON ANY PRIORITY LIST (1,502) = Q2 (1,885) ✓

---

## Mileage Status Summary

| Status | Tickets | % of Total | Barrels |
|--------|---------|-----------|---------|
| Priority 1 — mileage on file (Q1) | 9,799 | 83.9% | 1,687,175 |
| Non-Priority-1 — ticket mileage resolved | 988 | 8.5% | — |
| Non-Priority-1 — split P2 mileage resolved | 20 | 0.2% | — |
| Non-Priority-1 — agreement mileage resolved | 3 | 0.0% | — |
| **Non-Priority-1 — mileage MISSING (actionable)** | **874** | **7.5%** | **134,264** |
| **Total** | **11,684** | **100%** | |

**874 tickets (7.5% of all loads) have no mileage on file and require manual resolution.**

---

## Query 1 — Loads That Went to Priority 1 (9,799 tickets | 1,687,175 bbls)

These loads are operating as intended. Full detail in `CS-CC-query1_priority1_correct_*.csv`.

**By Priority List Source:**

| Source | Tickets | % of Q1 |
|--------|---------|---------|
| Valero (VLO) | 6,239 | 63.7% |
| CP Energy (CP) | 3,400 | 34.7% |
| Split Destinations | 160 | 1.6% |
| **Total** | **9,799** | **100%** |

**Output columns:** Ticket Number, Load Date, Lease Number, Lease Name, Operator, Purchaser, Priority Source, Priority 1 Station, Priority 1 Mileage, Actual Destination, Destination Code, Barrels Net

---

## Query 2 — All Non-Priority-1 Loads (1,885 tickets | 309,732 bbls)

All loads that did not deliver to their Priority 1 station. Includes both leases with a Priority 1 assignment that went elsewhere (Query 3) and leases absent from all priority lists. Full detail in `CS-CC-query2_not_priority1_*.csv`.

**By Priority List Source:**

| Source | Tickets | % of Q2 | Barrels | % of Q2 Bbls |
|--------|---------|---------|---------|-------------|
| NOT ON ANY PRIORITY LIST | 1,502 | 79.7% | 246,173 | 79.5% |
| CP Energy (CP) | 232 | 12.3% | 38,566 | 12.5% |
| Valero (VLO) | 95 | 5.0% | 14,158 | 4.6% |
| Split Destinations | 56 | 3.0% | 10,835 | 3.5% |
| **Total** | **1,885** | **100%** | **309,732** | **100%** |

**By Mileage Status:**

| Mileage Source | Tickets | % of Q2 |
|----------------|---------|---------|
| Ticket (resolved) | 988 | 52.4% |
| **MISSING — needs history lookup** | **874** | **46.4%** |
| Split Priority 2 (resolved) | 20 | 1.1% |
| Agreement (resolved) | 3 | 0.2% |
| **Total** | **1,885** | **100%** |

**Top 20 Actual Destinations:**

| Destination | Tickets | Unique Leases | Barrels |
|-------------|---------|--------------|---------|
| ARNETT LANES 1-4 | 230 | 61 | 41,511 |
| HWY 81 STATION | 178 | 36 | 32,513 |
| CHISHOLM STATION | 112 | 29 | 20,113 |
| NAV CALUMET STATION | 105 | 40 | 15,317 |
| CP - HOOKER | 90 | 40 | 13,192 |
| NAVIGATOR OMEGA CDP | 81 | 21 | 10,086 |
| TROJAN STATION | 79 | 21 | 13,303 |
| NAVIGATOR TUTTLE TERMINAL | 75 | 31 | 12,796 |
| CP TROJAN 2 - NGL | 66 | 6 | 12,269 |
| CP - PERRYTON 4 | 60 | 45 | 9,584 |
| CP TROJAN 3 - ETC | 51 | 4 | 9,320 |
| CP - WASSON STATION | 50 | 27 | 7,992 |
| RED STAG STATION | 49 | 26 | 8,207 |
| CP - CLAWSON 3 | 43 | 16 | 7,909 |
| CP - PIPER 4 | 39 | 26 | 6,425 |
| CP - MERTEN NORTH | 38 | 19 | 5,472 |
| OMEGA 6 LACT | 33 | 25 | 5,945 |
| ARNETT STATION LANE 5 | 33 | 15 | 5,998 |
| ARNETT STATIONS LANES 1-4 | 32 | 13 | 5,873 |
| ARNETT STATION LANE 6 | 31 | 14 | 5,813 |

**Output columns:** Ticket Number, Load Date, Lease Number, Lease Name, Operator, Purchaser, Actual Destination, Destination Code, Barrels Net, Priority Source, Priority 1 Station, Mileage, Mileage Source, Notes

---

## Query 3 — On-List Leases That Went to Wrong Destination (383 tickets | 63,559 bbls)

Subset of Query 2. These leases have a Priority 1 station assigned in the CP, VLO, or Split priority lists but delivered to a different destination. Full detail in `CS-CC-query3_priority1_wrong_destination_*.csv`.

**By Priority List Source:**

| Source | Tickets | % of Q3 | Barrels | % of Q3 Bbls |
|--------|---------|---------|---------|-------------|
| CP Energy (CP) | 232 | 60.6% | 38,566 | 60.7% |
| Valero (VLO) | 95 | 24.8% | 14,158 | 22.3% |
| Split Destinations | 56 | 14.6% | 10,835 | 17.0% |
| **Total** | **383** | **100%** | **63,559** | **100%** |

**By Mileage Status:**

| Mileage Source | Tickets | % of Q3 |
|----------------|---------|---------|
| **MISSING — needs history lookup** | **243** | **63.4%** |
| Ticket (resolved) | 117 | 30.5% |
| Split Priority 2 (resolved) | 20 | 5.2% |
| Agreement (resolved) | 3 | 0.8% |
| **Total** | **383** | **100%** |

**Top 15 Actual Destinations:**

| Destination | Tickets | Unique Leases | Barrels |
|-------------|---------|--------------|---------|
| CP - PERRYTON 4 | 45 | 30 | 7,637 |
| CP - CLAWSON 3 | 42 | 15 | 7,724 |
| CP - WASSON STATION | 42 | 22 | 6,749 |
| CP - HOOKER | 28 | 10 | 5,230 |
| CP - PIPER 4 | 27 | 14 | 4,553 |
| CP - MADILL | 25 | 19 | 4,572 |
| SOUTHWEST RUBY STATION | 23 | 2 | 3,483 |
| CP - PERRYTON 1 | 16 | 13 | 2,606 |
| CP - SUNRAY-MCKEE | 13 | 10 | 2,385 |
| CP - CLAWSON 1 | 13 | 4 | 2,222 |
| CP - CLAWSON 2 | 12 | 6 | 2,109 |
| CP - PERRYTON 2 | 12 | 12 | 1,994 |
| TROJAN STATION | 10 | 8 | 1,156 |
| ARNETT LANES 1-4 | 8 | 7 | 1,211 |
| CP - PIPER 3 | 8 | 6 | 1,044 |

**Top 15 Leases:**

| Lease Number | Lease Name | Tickets | Barrels |
|-------------|------------|---------|---------|
| SNEE0001 | SNEED PLANT | 36 | 6,861 |
| RUBY0005 | RUBY | 22 | 3,323 |
| LIBE0002 | LIBERAL RBO | 16 | 3,182 |
| HEMP0003 | HEMPHILL PLANT (SUPERIOR) | 13 | 2,397 |
| DUMA0001 | DUMAS SWD | 8 | 1,535 |
| GRAY0005 | GRAYCON | 8 | 770 |
| HUTC0001 | HUTCHCON | 6 | 1,159 |
| RORA117H | ROSE RANCH 1-17H16X21X28 | 5 | 925 |
| TWOM0224 | TWOMBLY 2-24 (SMU) | 5 | 930 |
| SHER0013 | SHERMAN PLANT | 5 | 945 |
| PETT0019 | PETTIJOHN COMPRESSOR STATION | 5 | 938 |
| SPEAR001 | SPEARMAN (ETC) | 4 | 761 |
| LONG0003 | LONG SWD #1 | 4 | 768 |
| LILA0007 | LILA 2 - 18H17 / LILA 3 - 18H1 | 4 | 750 |
| MIDC0001 | MID CON MEDICINE LODGE | 4 | 793 |

**Output columns:** Ticket Number, Load Date, Lease Number, Lease Name, Operator, Purchaser, Actual Destination, Destination Code, Barrels Net, Priority Source, Priority 1 Station, Mileage, Mileage Source, Notes

---

## Leases Not on Any Priority List (1,502 tickets | 246,173 bbls)

These leases exist in the mobile platform but were absent from the CP, VLO, and Split priority uploads for March. They are included in Query 2 but excluded from Query 3.

| Mileage Status | Tickets | % |
|----------------|---------|---|
| Ticket (resolved) | 871 | 58.0% |
| **MISSING** | **631** | **42.0%** |
| **Total** | **1,502** | **100%** |

Top NOT ON ANY PRIORITY LIST destinations mirror the full Query 2 list (ARNETT LANES 1-4, HWY 81 STATION, CHISHOLM STATION, NAV CALUMET STATION) since these leases make up 79.7% of Q2 volume.

---

## Key Observations

1. **83.9% of loads (9,799 of 11,684) went to their Priority 1 station** — 84.5% of barrels.

2. **383 loads (3.3%) had a Priority 1 assignment but delivered elsewhere (Query 3).** These represent confirmed routing exceptions where dispatch overrode the priority assignment. 243 of these (63.4%) have no mileage on file.

3. **1,502 loads (12.9%) involve leases absent from all priority lists.** These leases exist operationally but were not included in the March priority upload. They may represent new leases, temporary hauls, or omissions from the upload. 631 have no mileage on file.

4. **874 total tickets (7.5% of all loads, 134,264 barrels) require mileage resolution** — 243 from Q3 (on-list, wrong destination) and 631 from NOT ON ANY PRIORITY LIST leases.

5. **The history lookup** (querying 10–15K prior monthly tickets for matching lease → destination combinations) would resolve the majority of the 874 missing-mileage records automatically, eliminating the current email workflow.

---

## Output Files

| File | Description | Rows |
|------|-------------|------|
| `CS-CC-query1_priority1_correct_*.csv` | Loads that went to Priority 1 | 9,799 |
| `CS-CC-query2_not_priority1_*.csv` | All non-Priority-1 loads | 1,885 |
| `CS-CC-query3_priority1_wrong_destination_*.csv` | On-list leases that went to wrong destination | 383 |
| `CS-CC-analysis_report_*.txt` | Machine-generated summary report | — |
| `CS-CC-CPE-Analysis-Report-March2026.md` | This document | — |

**Total tickets across Q1 + Q2 = 11,684 ✓**  
**Q3 is a subset of Q2: Q3 (383) + NOT ON ANY PRIORITY LIST (1,502) = Q2 (1,885) ✓**
