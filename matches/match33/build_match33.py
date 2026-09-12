"""
build_match33.py - CPL 2026, 33rd Match, Trinbago Knight Riders vs Guyana Amazon Warriors,
Providence Stadium, Guyana, 2026-09-11.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Trinbago Knight Riders (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Guyana Amazon Warriors (chased)

TEAM1_NAME = 'Trinbago Knight Riders'
TEAM2_NAME = 'Guyana Amazon Warriors'

TEAM1_XI = [
    'Colin Munro', 'Alex Hales', 'Nicholas Pooran', 'Justin Greaves', 'Jyd Goolie',
    'Sunil Narine', 'Kieron Pollard', 'Joshua Da Silva', 'Akeal Hosein',
    'Lahiru Kumara', 'Usman Tariq',
]
TEAM2_XI = [
    'Glenn Phillips', 'Mavendra Dindyal', 'Shai Hope', 'Shimron Hetmyer',
    'Mehidy Hasan Miraz', 'Quentin Sampson', 'Romario Shepherd', 'Shamar Joseph',
    'Dwaine Pretorius', 'Imran Tahir', 'Veerasammy Permaul',
]

NAME_MAP = {
    # Trinbago Knight Riders
    'Munro': 'Colin Munro', 'Colin Munro': 'Colin Munro',
    'Hales': 'Alex Hales', 'Alex Hales': 'Alex Hales',
    'Pooran': 'Nicholas Pooran', 'Nicholas Pooran': 'Nicholas Pooran',
    'Greaves': 'Justin Greaves', 'Justin Greaves': 'Justin Greaves',
    'Goolie': 'Jyd Goolie', 'Jyd Goolie': 'Jyd Goolie',
    'Narine': 'Sunil Narine', 'Sunil Narine': 'Sunil Narine',
    'Pollard': 'Kieron Pollard', 'Kieron Pollard': 'Kieron Pollard',
    'Da Silva': 'Joshua Da Silva', 'Joshua Da Silva': 'Joshua Da Silva',
    'Hosein': 'Akeal Hosein', 'Akeal Hosein': 'Akeal Hosein',
    'Lahiru Kumara': 'Lahiru Kumara', 'Kumara': 'Lahiru Kumara',
    'Usman Tariq': 'Usman Tariq',
    # Guyana Amazon Warriors
    'Phillips': 'Glenn Phillips', 'Glenn Phillips': 'Glenn Phillips',
    'Dindyal': 'Mavendra Dindyal', 'Mavendra Dindyal': 'Mavendra Dindyal',
    'Hope': 'Shai Hope', 'Shai Hope': 'Shai Hope',
    'Hetmyer': 'Shimron Hetmyer', 'Shimron Hetmyer': 'Shimron Hetmyer',
    'Mehidy Hasan Miraz': 'Mehidy Hasan Miraz', 'Mehidy': 'Mehidy Hasan Miraz',
    'Miraz': 'Mehidy Hasan Miraz',
    'Sampson': 'Quentin Sampson', 'Quentin Sampson': 'Quentin Sampson',
    'Shepherd': 'Romario Shepherd', 'Romario Shepherd': 'Romario Shepherd',
    'Shamar Joseph': 'Shamar Joseph', 'Joseph': 'Shamar Joseph',
    'Pretorius': 'Dwaine Pretorius', 'Dwaine Pretorius': 'Dwaine Pretorius',
    'Tahir': 'Imran Tahir', 'Imran Tahir': 'Imran Tahir',
    'Permaul': 'Veerasammy Permaul', 'Veerasammy Permaul': 'Veerasammy Permaul',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': '',
    'dates': ['2026-09-11'],
    'event': {'name': 'Caribbean Premier League', 'match_number': 33},
    'gender': 'male',
    'match_type': 'T20',
    'outcome': {'winner': 'Guyana Amazon Warriors', 'by': {'wickets': 6}},
    'overs': 20,
    'player_of_match': ['Mehidy Hasan Miraz'],
    'season': '2026',
    'team_type': 'club',
    'toss': {'winner': 'Guyana Amazon Warriors', 'decision': 'field'},
    'venue': 'Providence Stadium, Guyana',
}

KNOWN_IDS = {}


# =============================================================================
# Reusable logic (copied from build_match_json_template.py)
# =============================================================================

def norm(name):
    return NAME_MAP.get(name.strip(), name.strip())


def normalise_deliveries(deliveries):
    for d in deliveries:
        d['batter'] = norm(d['batter'])
        d['bowler'] = norm(d['bowler'])
        if d['wicket']:
            d['wicket']['player_out'] = norm(d['wicket']['player_out'])
            if d['wicket'].get('fielder'):
                parts = [norm(p) for p in d['wicket']['fielder'].split('/')]
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
                wk['fielders'] = [{'name': n} for n in w['fielder'].split('/')]
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
    d1 = normalise_deliveries(parse_deliveries(t1))
    d2 = normalise_deliveries(parse_deliveries(t2))

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
        wkts = sum(1 for over in inn['overs'] for deliv in over['deliveries'] if deliv.get('wickets'))
        balls = sum(1 for over in inn['overs'] for deliv in over['deliveries'])
        print(f"  {inn['team']}: total {total}, wickets {wkts}, deliveries logged {balls}")

    return match_json


if __name__ == '__main__':
    out = os.path.join(_HERE, 'cpl_2026_match33_tkr_vs_amazon.json')
    build_match_json(out)
