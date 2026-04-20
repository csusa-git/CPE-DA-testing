"""
CPE Priority Destination Analysis
----------------------------------
Query 1: Loads that went to their Priority 1 station (correct)
Query 2: Loads that went anywhere other than Priority 1 (exceptions)
         Includes: split/secondary destinations, unlisted stations,
         leases not on any priority list

Mileage logic for Query 2:
  1. If destination matches a known Split Priority 2 entry -> use that mileage
  2. Else use ticket_mileage from the export
  3. Else flag as MISSING (future: history lookup)

Station Name Mapping:
  Priority list station names are abbreviated base names. The export uses
  more specific names (lane numbers, compass directions, etc.) for the same
  physical station. STATION_GROUPS maps each priority base name to all valid
  export destination names for that station.

Data files (place in ../data/):
  CPE_Export.csv                - Mobile platform export, all March 2026 tickets
  CPE_CP.csv                    - CP Energy priority list (Priority 1 stations)
  CPE_VLO.csv                   - Valero priority list (Priority 1 stations)
  CPE_split_destinations.csv    - Special split-volume routing rules
"""

import os
import pandas as pd
from datetime import datetime

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, 'data')
OUT_DIR   = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

EXPORT_FILE = os.path.join(DATA_DIR, 'CPE_Export.csv')
CP_FILE     = os.path.join(DATA_DIR, 'CPE_CP.csv')
VLO_FILE    = os.path.join(DATA_DIR, 'CPE_VLO.csv')
SPLIT_FILE  = os.path.join(DATA_DIR, 'CPE_split_destinations.csv')

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')


# ---------------------------------------------------------------------------
# Station Groups
# Priority list uses base station names; export uses specific lane/sub-names.
# Each entry maps a normalized priority station name -> set of normalized
# export destination names that represent the same physical station.
# ---------------------------------------------------------------------------

STATION_GROUPS = {
    'ARNETT': {
        'ARNETT LANES 1-4',
        'ARNETT STATION (NAVI)',
        'ARNETT STATION (NAVI) LANE 14',
        'ARNETT STATION LANE 1',
        'ARNETT STATION LANE 5',
        'ARNETT STATION LANE 6',
        'ARNETT STATION LANE 7',
        'ARNETT STATION LANE 10',
        'ARNETT STATION LANE 14',
        'ARNETT STATIONS LANES 1-4',
    },
    'BRETCH STATION': {'BRETCH STATION'},
    'CHEROKEE LACT 306': {'CHEROKEE LACT 306'},
    'CLAWSON': {'CP - CLAWSON 1', 'CP - CLAWSON 2', 'CP - CLAWSON 3'},
    'CP - CHILDRESS': {'CP - CHILDRESS'},
    'CP - HIGHWAY 177 STATION': {'CP - HIGHWAY 177 STATION'},
    'CP - HOOKER': {'CP - HOOKER'},
    'CP - MADILL': {'CP - MADILL'},
    'CP - SUNRAY-MCKEE': {'CP - SUNRAY-MCKEE'},
    'CP - VELMA': {'CP - VELMA'},
    'CP - WASSON STATION': {'CP - WASSON STATION'},
    'CP - WASSON STATION VLO': {'CP - WASSON STATION'},
    'DIXIE': {'DIXIE STATION'},
    'GSPM HENNESSEY STATION': {'GSPM HENNESSEY STATION'},
    'GSPM HENNESSEY STATION - LANE 3': {
        'GSPM HENNESSEY STATION',
        'GSPM HENNESSEY STATION LANE 3',
    },
    'LINDSAY STATION': {'LINDSAY STATION'},
    'MERTEN': {'CP - MERTEN NORTH', 'CP - MERTEN SOUTH'},
    'MVP CUSHING 6 WAY': {'MVP CUSHING 6 WAY'},
    'P66 - GOLDSBY': {'GOLDSBY STATION'},
    'P66 - OGG': {'P66 - OGG'},
    'PERRYTON': {
        'CP - PERRYTON 1',
        'CP - PERRYTON 2',
        'CP - PERRYTON 3',
        'CP - PERRYTON 4',
    },
    'PIPER': {
        'CP - PIPER 1',
        'CP - PIPER 2',
        'CP - PIPER 3',
        'CP - PIPER 4',
    },
    'RUBY': {
        'RUBY STATION',
        'RUBY STATION (NAVIGATOR)',
        'SOUTHWEST RUBY STATION',
    },
    'TROJAN': {
        'TROJAN STATION',
        'CP TROJAN 2 - NGL',
        'CP TROJAN 3 - ETC',
    },
}

# Reverse lookup: export destination name -> canonical priority station name
DEST_TO_CANONICAL = {}
for priority_station, export_names in STATION_GROUPS.items():
    for dest in export_names:
        DEST_TO_CANONICAL[dest] = priority_station


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def norm(val):
    """Normalize a string for comparison: uppercase, stripped."""
    if pd.isna(val) or str(val).strip() in ('', '#N/A', 'N/A'):
        return ''
    return str(val).strip().upper()


def safe_mileage(val):
    """Return mileage as string, or empty string if missing/zero."""
    if pd.isna(val):
        return ''
    s = str(val).strip()
    return '' if s in ('', '0', '0.0', '#N/A', 'N/A') else s


def destinations_match(priority_station_norm, actual_dest_norm):
    """
    Returns True if actual_dest is a valid match for the given priority station.
    Checks the STATION_GROUPS mapping, then falls back to exact match.
    """
    valid_dests = STATION_GROUPS.get(priority_station_norm)
    if valid_dests is not None:
        return actual_dest_norm in valid_dests
    return actual_dest_norm == priority_station_norm


# ---------------------------------------------------------------------------
# Load priority lists
# ---------------------------------------------------------------------------

def load_priority_lists():
    """
    Returns a dict keyed by normalized lease_number:
    {
        'priority_1_station':  str (normalized),
        'priority_1_mileage':  str,
        'priority_2_station':  str or '' (split destinations only),
        'priority_2_mileage':  str,
        'lease_name':          str,
        'operator':            str,
        'source':              'CP' | 'VLO' | 'SPLIT',
    }
    Split Destinations take precedence over CP/VLO for those leases.
    """
    priority_map = {}

    for source, filepath in [('CP', CP_FILE), ('VLO', VLO_FILE)]:
        df = pd.read_csv(filepath, encoding='utf-8-sig', dtype=str)
        df.columns = [c.strip() for c in df.columns]
        for _, row in df.iterrows():
            lease_key = norm(row.get('Lease Number', ''))
            station   = norm(row.get('Station Name', ''))
            if not lease_key or not station:
                continue
            if lease_key not in priority_map:
                priority_map[lease_key] = {
                    'priority_1_station':  station,
                    'priority_1_mileage':  safe_mileage(row.get('Mileage', '')),
                    'priority_2_station':  '',
                    'priority_2_mileage':  '',
                    'lease_name':          norm(row.get('Lease Name', '')),
                    'operator':            norm(row.get('OperatorName', '')),
                    'source':              source,
                }

    # Split destinations override (header on row 3)
    split_df = pd.read_csv(SPLIT_FILE, encoding='utf-8-sig', skiprows=3, dtype=str)
    split_df.columns = [c.strip() for c in split_df.columns]
    split_df = split_df[split_df['Priority'].apply(
        lambda x: str(x).strip() in ('1', '2')
    )]

    for lease_key, grp in split_df.groupby(split_df['Lease Number'].apply(norm)):
        if not lease_key:
            continue
        p1 = grp[grp['Priority'].str.strip() == '1']
        p2 = grp[grp['Priority'].str.strip() == '2']
        priority_map[lease_key] = {
            'priority_1_station':  norm(p1.iloc[0]['Station Name']) if len(p1) else '',
            'priority_1_mileage':  safe_mileage(p1.iloc[0]['Mileage']) if len(p1) else '',
            'priority_2_station':  norm(p2.iloc[0]['Station Name']) if len(p2) else '',
            'priority_2_mileage':  safe_mileage(p2.iloc[0]['Mileage']) if len(p2) else '',
            'lease_name':          norm(p1.iloc[0]['Lease Name']) if len(p1) else '',
            'operator':            norm(p1.iloc[0]['OperatorName']) if len(p1) else '',
            'source':              'SPLIT',
        }

    return priority_map


# ---------------------------------------------------------------------------
# Load export tickets
# ---------------------------------------------------------------------------

def load_export():
    usecols = [
        'number', 'load_date', 'lease_number', 'lease_name',
        'operator_name', 'purchaser_name', 'destination_name',
        'destination_code', 'barrels_net', 'ticket_mileage',
        'agreement_mileage', 'status',
    ]
    df = pd.read_csv(EXPORT_FILE, encoding='utf-8-sig', dtype=str, usecols=usecols)
    df.columns = [c.strip() for c in df.columns]
    df = df[~df['status'].isin(['R', 'D'])]  # exclude Rejected, Draft
    return df


# ---------------------------------------------------------------------------
# Mileage resolution for Query 2
# ---------------------------------------------------------------------------

def resolve_mileage(ticket, pdata, actual_dest_norm):
    """
    Returns (mileage, source, notes) for a Query 2 ticket.
    Priority: split destination mileage > ticket mileage > agreement mileage > MISSING
    """
    notes = 'Non-priority destination'

    if pdata and pdata.get('priority_2_station') and actual_dest_norm == pdata['priority_2_station']:
        notes = 'Went to scheduled split destination (Priority 2)'
        if pdata['priority_2_mileage']:
            return pdata['priority_2_mileage'], 'Split Priority 2', notes

    ticket_mil = safe_mileage(ticket.get('ticket_mileage', ''))
    if ticket_mil:
        return ticket_mil, 'Ticket', notes

    agreement_mil = safe_mileage(ticket.get('agreement_mileage', ''))
    if agreement_mil:
        return agreement_mil, 'Agreement', notes

    return '', 'MISSING — needs history lookup', notes


# ---------------------------------------------------------------------------
# Build result rows
# ---------------------------------------------------------------------------

def build_results(export_df, priority_map):
    query1_rows = []
    query2_rows = []  # all loads that did NOT go to their Priority 1 station

    for _, ticket in export_df.iterrows():
        lease_key  = norm(ticket.get('lease_number', ''))
        actual_dst = norm(ticket.get('destination_name', ''))

        base = {
            'Ticket Number':      str(ticket.get('number', '')).strip(),
            'Load Date':          str(ticket.get('load_date', '')).strip(),
            'Lease Number':       str(ticket.get('lease_number', '')).strip(),
            'Lease Name':         str(ticket.get('lease_name', '')).strip(),
            'Operator':           str(ticket.get('operator_name', '')).strip(),
            'Purchaser':          str(ticket.get('purchaser_name', '')).strip(),
            'Actual Destination': str(ticket.get('destination_name', '')).strip(),
            'Destination Code':   str(ticket.get('destination_code', '')).strip(),
            'Barrels Net':        str(ticket.get('barrels_net', '')).strip(),
        }

        if lease_key not in priority_map:
            mileage, mil_src, _ = resolve_mileage(ticket, None, actual_dst)
            query2_rows.append({
                **base,
                'Priority Source':    'NOT ON ANY PRIORITY LIST',
                'Priority 1 Station': '',
                'Mileage':            mileage,
                'Mileage Source':     mil_src,
                'Notes':              'Lease not found on CP or VLO priority list',
            })
            continue

        pdata      = priority_map[lease_key]
        p1_station = pdata['priority_1_station']

        if destinations_match(p1_station, actual_dst):
            query1_rows.append({
                **base,
                'Priority Source':    pdata['source'],
                'Priority 1 Station': str(ticket.get('destination_name', '')).strip(),
                'Priority 1 Mileage': pdata['priority_1_mileage'],
            })
        else:
            mileage, mil_src, notes = resolve_mileage(ticket, pdata, actual_dst)
            query2_rows.append({
                **base,
                'Priority Source':    pdata['source'],
                'Priority 1 Station': p1_station.title(),
                'Mileage':            mileage,
                'Mileage Source':     mil_src,
                'Notes':              notes,
            })

    q2 = pd.DataFrame(query2_rows)
    q3 = q2[q2['Priority Source'] != 'NOT ON ANY PRIORITY LIST'].reset_index(drop=True) if not q2.empty else pd.DataFrame()
    return pd.DataFrame(query1_rows), q2, q3


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(q1, q2, q3):
    lines = []
    lines.append('=' * 70)
    lines.append('CPE PRIORITY DESTINATION ANALYSIS — MARCH 2026')
    lines.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('=' * 70)
    lines.append('')

    total = len(q1) + len(q2)
    lines.append('SUMMARY')
    lines.append('-' * 40)
    lines.append(f'  Total tickets analyzed:          {total:,}')
    lines.append(f'  Went to Priority 1 (Query 1):    {len(q1):,}')
    lines.append(f'  Did NOT go to Priority 1 (Query 2):         {len(q2):,}')
    lines.append(f'  On-list, wrong destination (Query 3):       {len(q3):,}')
    lines.append('')

    if not q2.empty:
        lines.append('QUERY 2 — TOP DESTINATIONS WITHOUT MILEAGE')
        lines.append('-' * 40)
        for dest, cnt in q2['Actual Destination'].value_counts().head(20).items():
            lines.append(f'  {cnt:5,}  {dest}')
        lines.append('')

        lines.append('QUERY 2 — TOP LEASES WITHOUT MILEAGE')
        lines.append('-' * 40)
        top = q2.groupby(['Lease Number', 'Lease Name']).size().sort_values(ascending=False).head(20)
        for (num, name), cnt in top.items():
            lines.append(f'  {cnt:5,}  {num:<12}  {name}')
        lines.append('')

    lines.append('OUTPUT FILES')
    lines.append('-' * 40)
    lines.append(f'  Query 1 CSV:  output/CS-CC-query1_priority1_correct_{TIMESTAMP}.csv')
    lines.append(f'  Query 2 CSV:  output/CS-CC-query2_not_priority1_{TIMESTAMP}.csv')
    lines.append(f'  Query 3 CSV:  output/CS-CC-query3_priority1_wrong_destination_{TIMESTAMP}.csv')
    lines.append(f'  This report:  output/CS-CC-analysis_report_{TIMESTAMP}.txt')
    lines.append('')
    lines.append('=' * 70)

    report_text = '\n'.join(lines)
    report_path = os.path.join(OUT_DIR, f'CS-CC-analysis_report_{TIMESTAMP}.txt')
    with open(report_path, 'w') as f:
        f.write(report_text)
    print(report_text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('Loading priority lists...')
    priority_map = load_priority_lists()
    print(f'  {len(priority_map):,} leases on priority lists (CP + VLO + Split)')

    print('Loading export tickets...')
    export_df = load_export()
    print(f'  {len(export_df):,} tickets loaded')

    print('Running queries...')
    q1, q2, q3 = build_results(export_df, priority_map)

    q1_path = os.path.join(OUT_DIR, f'CS-CC-query1_priority1_correct_{TIMESTAMP}.csv')
    q2_path = os.path.join(OUT_DIR, f'CS-CC-query2_not_priority1_{TIMESTAMP}.csv')
    q3_path = os.path.join(OUT_DIR, f'CS-CC-query3_priority1_wrong_destination_{TIMESTAMP}.csv')
    q1.to_csv(q1_path, index=False)
    q2.to_csv(q2_path, index=False)
    q3.to_csv(q3_path, index=False)
    print(f'  Query 1: {len(q1):,} rows -> {q1_path}')
    print(f'  Query 2: {len(q2):,} rows -> {q2_path}')
    print(f'  Query 3: {len(q3):,} rows -> {q3_path}')

    write_report(q1, q2, q3)


if __name__ == '__main__':
    main()
