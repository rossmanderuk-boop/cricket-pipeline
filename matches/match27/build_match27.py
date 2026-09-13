"""
build_match27.py - CPL 2026, 27th Match, Trinbago Knight Riders vs Barbados Tridents,
Kensington Oval, Bridgetown, Barbados, 2026-09-05.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Trinbago Knight Riders (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Barbados Tridents (chased)

TEAM1_NAME = 'Trinbago Knight Riders'
TEAM2_NAME = 'Barbados Tridents'

TEAM1_XI = [
    'Colin Munro', 'Sunil Narine', 'Nicholas Pooran', 'Kieron Pollard', 'Alex Hales',
    'Jyd Goolie', 'Joshua Da Silva', 'Akeal Hosein', 'Dexter Sween', 'Usman Tariq',
    'Lahiru Kumara',
]
TEAM2_XI = [
    'Brandon King', 'Zachary Carter', 'Quinton de Kock', 'Rivaldo Clarke', 'Chris Green',
    'Sherfane Rutherford', 'Shadrack Descarte', 'Daniel Sams', 'Gudakesh Motie',
    'Mujeeb Ur Rahman', 'Jakeem Pollard',
]

NAME_MAP = {
    # Trinbago Knight Riders
    'Munro': 'Colin Munro', 'Colin Munro': 'Colin Munro',
    'Narine': 'Sunil Narine', 'Sunil Narine': 'Sunil Narine',
    'Pooran': 'Nicholas Pooran', 'Nicholas Pooran': 'Nicholas Pooran', 'N Pooran': 'Nicholas Pooran',
    # NOTE: bare 'Pollard' is deliberately NOT mapped here - it is ambiguous between
    # Kieron Pollard (TKR batter) and Jakeem Pollard (BT bowler/batter), both of whom
    # appear as bare "Pollard" in this match's commentary. Resolved per-role/per-innings
    # in the POLLARD_OVERRIDES below instead.
    'Kieron Pollard': 'Kieron Pollard',
    'Hales': 'Alex Hales', 'Alex Hales': 'Alex Hales',
    'Goolie': 'Jyd Goolie', 'Jyd Goolie': 'Jyd Goolie',
    'Da Silva': 'Joshua Da Silva', 'Joshua Da Silva': 'Joshua Da Silva',
    'Hosein': 'Akeal Hosein', 'Akeal Hosein': 'Akeal Hosein', 'AJ Hosein': 'Akeal Hosein',
    'Sween': 'Dexter Sween', 'Dexter Sween': 'Dexter Sween',
    'Usman Tariq': 'Usman Tariq',
    'Lahiru Kumara': 'Lahiru Kumara', 'Kumara': 'Lahiru Kumara',
    # Barbados Tridents
    'King': 'Brandon King', 'Brandon King': 'Brandon King',
    'Carter': 'Zachary Carter', 'Zachary Carter': 'Zachary Carter',
    'de Kock': 'Quinton de Kock', 'Quinton de Kock': 'Quinton de Kock', 'QDK': 'Quinton de Kock',
    'Clarke': 'Rivaldo Clarke', 'Rivaldo Clarke': 'Rivaldo Clarke', 'RA Clarke': 'Rivaldo Clarke',
    'Green': 'Chris Green', 'Chris Green': 'Chris Green',
    'Rutherford': 'Sherfane Rutherford', 'Sherfane Rutherford': 'Sherfane Rutherford',
    'SE Rutherford': 'Sherfane Rutherford',
    'Descarte': 'Shadrack Descarte', 'Shadrack Descarte': 'Shadrack Descarte',
    'S Descarte': 'Shadrack Descarte',
    'Sams': 'Daniel Sams', 'Daniel Sams': 'Daniel Sams',
    'Motie': 'Gudakesh Motie', 'Gudakesh Motie': 'Gudakesh Motie',
    'Mujeeb': 'Mujeeb Ur Rahman', 'Mujeeb Ur Rahman': 'Mujeeb Ur Rahman',
    'Jakeem Pollard': 'Jakeem Pollard',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Bridgetown',
    'dates': ['2026-09-05'],
    'event': {'name': 'Caribbean Premier League', 'match_number': 27},
    'gender': 'male',
    'match_type': 'T20',
    'outcome': {'winner': 'Trinbago Knight Riders', 'by': {'runs': 35}},
    'overs': 20,
    'player_of_match': ['Sunil Narine'],
    'season': '2026',
    'team_type': 'club',
    'toss': {'winner': 'Barbados Tridents', 'decision': 'field'},
    'venue': 'Kensington Oval, Bridgetown, Barbados',
}

KNOWN_IDS = {}


# =============================================================================
# Reusable logic (copied from build_match_json_template.py)
# =============================================================================

def norm(name):
    return NAME_MAP.get(name.strip(), name.strip())


# Bare "Pollard" is ambiguous in this match: Kieron Pollard (TKR) bats in innings 1 and
# fields in innings 2; Jakeem Pollard (BT) bowls/fields in innings 1 and bats in innings 2.
# Resolve it per role, per innings, instead of via the flat NAME_MAP.
POLLARD_OVERRIDES = {
    1: {'bowler': 'Jakeem Pollard', 'batter': 'Kieron Pollard', 'fielder': 'Jakeem Pollard'},
    2: {'bowler': 'Kieron Pollard', 'batter': 'Jakeem Pollard', 'fielder': 'Kieron Pollard'},
}


def norm_role(name, role, innings_no):
    name = name.strip()
    if name == 'Pollard':
        return POLLARD_OVERRIDES[innings_no][role]
    return norm(name)


def normalise_deliveries(deliveries, innings_no):
    for d in deliveries:
        d['batter'] = norm_role(d['batter'], 'batter', innings_no)
        d['bowler'] = norm_role(d['bowler'], 'bowler', innings_no)
        if d['wicket']:
            d['wicket']['player_out'] = norm_role(d['wicket']['player_out'], 'batter', innings_no)
            if d['wicket'].get('fielder'):
                parts = [norm_role(p, 'fielder', innings_no) for p in d['wicket']['fielder'].split('/')]
                d['wicket']['fielder'] = '/'.join(parts)
    return deliveries


def build_innings(deliveries, team_name):
    pair = []
    over_list = []
    over_cursor = -1
    cur = None

    for d in deliveries:
        if d['over'] != over_cursor:
            if cur is not None:
                over_list.append({'over': over_cursor, 'deliveries': cur})
            over_cursor = d['over']
            cur = []

        batter = d['batter']
        if batter not in pair:
            if len(pair) < 2:
                pair.append(batter)
            else:
                pair[-1] = batter
        non_striker = next((p for p in pair if p != batter), batter)

        extras = {}
        extras_total = 0
        if d['extra_type']:
            extras[d['extra_type']] = d['extra_runs']
            extras_total = d['extra_runs']

        deliv = {
            'batter': batter, 'bowler': d['bowler'], 'non_striker': non_striker,
            'runs': {'batter': d['runs_batter'], 'extras': extras_total,
                     'total': d['runs_batter'] + extras_total},
        }
        if extras:
            deliv['extras'] = extras
        if d['wicket']:
            w = d['wicket']
            wk = {'kind': w['kind'], 'player_out': w['player_out']}
            if w.get('fielder'):
                names = w['fielder'].split('/')
                if w.get('substitute') and len(names) == 1:
                    wk['fielders'] = [{'name': names[0], 'substitute': True}]
                else:
                    wk['fielders'] = [{'name': n} for n in names]
            deliv['wickets'] = [wk]
            if w['player_out'] in pair:
                pair.remove(w['player_out'])

        cur.append(deliv)

    if cur is not None:
        over_list.append({'over': over_cursor, 'deliveries': cur})
    return {'team': team_name, 'overs': over_list}


def build_match_json(out_path):
    t1 = open(INNINGS1_FILE).read()
    t2 = open(INNINGS2_FILE).read()
    d1 = normalise_deliveries(parse_deliveries(t1), 1)
    d2 = normalise_deliveries(parse_deliveries(t2), 2)

    innings1 = build_innings(d1, TEAM1_NAME)
    innings2 = build_innings(d2, TEAM2_NAME)

    registry = {name: pid for name, pid in KNOWN_IDS.items() if name in TEAM1_XI + TEAM2_XI}

    info = dict(MATCH_INFO)
    info['players'] = {TEAM1_NAME: TEAM1_XI, TEAM2_NAME: TEAM2_XI}
    info['registry'] = {'people': registry}
    info['teams'] = [TEAM1_NAME, TEAM2_NAME]

    match_json = {
        'meta': {'data_version': '1.2.0', 'revision': 1,
                  'source_note': 'Reconstructed from ball-by-ball commentary + scorecard. '
                                  'Not an official Cricsheet file. Cross-validate all figures '
                                  'against the scorecard before use.'},
        'info': info,
        'innings': [innings1, innings2],
    }

    with open(out_path, 'w') as f:
        json.dump(match_json, f, indent=2)
    print('Saved', out_path)

    for inn in match_json['innings']:
        total = sum(deliv['runs']['total'] for over in inn['overs'] for deliv in over['deliveries'])
        wkts = sum(1 for over in inn['overs'] for deliv in over['deliveries'] for _ in deliv.get('wickets', []))
        n_balls = sum(1 for over in inn['overs'] for deliv in over['deliveries'])
        print(f"  {inn['team']}: total {total}, wickets {wkts}, deliveries logged {n_balls}")

    return match_json


if __name__ == '__main__':
    out = os.path.join(_HERE, 'cpl_2026_match27_tkr_vs_tridents.json')
    build_match_json(out)
