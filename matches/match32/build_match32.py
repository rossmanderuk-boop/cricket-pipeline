"""
build_match32.py - CPL 2026, 32nd Match, Barbados Tridents vs St Kitts and Nevis Patriots,
Kensington Oval, Bridgetown, 2026-09-10.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # St Kitts and Nevis Patriots (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Barbados Tridents (chased)

TEAM1_NAME = 'St Kitts and Nevis Patriots'
TEAM2_NAME = 'Barbados Tridents'

TEAM1_XI = [
    'Johnson Charles', 'Kyle Mayers', 'Andre Fletcher', 'Alick Athanaze', 'Jason Holder',
    'Dasun Shanaka', 'Wanindu Hasaranga', 'Navin Bidaisee', 'Naseem Shah', 'Jeremiah Louis',
    'Waqar Salamkheil',
]
TEAM2_XI = [
    'Brandon King', 'Zachary Carter', 'Rivaldo Clarke', 'Quinton de Kock', 'Shadrack Descarte',
    'Sherfane Rutherford', 'Chris Green', 'Daniel Sams', 'AM Ghazanfar', 'Gudakesh Motie',
    'Jakeem Pollard',
]

NAME_MAP = {
    # St Kitts and Nevis Patriots
    'Charles': 'Johnson Charles', 'Johnson Charles': 'Johnson Charles',
    'Mayers': 'Kyle Mayers', 'Kyle Mayers': 'Kyle Mayers',
    'Fletcher': 'Andre Fletcher', 'Andre Fletcher': 'Andre Fletcher',
    'Athanaze': 'Alick Athanaze', 'Alick Athanaze': 'Alick Athanaze',
    'Holder': 'Jason Holder', 'Jason Holder': 'Jason Holder',
    'Shanaka': 'Dasun Shanaka', 'Dasun Shanaka': 'Dasun Shanaka',
    'Hasaranga': 'Wanindu Hasaranga', 'Wanindu Hasaranga': 'Wanindu Hasaranga',
    'Bidaisee': 'Navin Bidaisee', 'Navin Bidaisee': 'Navin Bidaisee',
    'Naseem Shah': 'Naseem Shah',
    'Louis': 'Jeremiah Louis', 'Jeremiah Louis': 'Jeremiah Louis',
    'Waqar': 'Waqar Salamkheil', 'Waqar Salamkheil': 'Waqar Salamkheil',
    # Barbados Tridents
    'King': 'Brandon King', 'Brandon King': 'Brandon King',
    'Carter': 'Zachary Carter', 'Zachary Carter': 'Zachary Carter',
    'Clarke': 'Rivaldo Clarke', 'Rivaldo Clarke': 'Rivaldo Clarke',
    'de Kock': 'Quinton de Kock', 'Quinton de Kock': 'Quinton de Kock', 'QDK': 'Quinton de Kock',
    'Descarte': 'Shadrack Descarte', 'Shadrack Descarte': 'Shadrack Descarte',
    'Rutherford': 'Sherfane Rutherford', 'Sherfane Rutherford': 'Sherfane Rutherford',
    'Green': 'Chris Green', 'Chris Green': 'Chris Green',
    'Sams': 'Daniel Sams', 'Daniel Sams': 'Daniel Sams',
    'Ghazanfar': 'AM Ghazanfar', 'AM Ghazanfar': 'AM Ghazanfar',
    'Motie': 'Gudakesh Motie', 'Gudakesh Motie': 'Gudakesh Motie',
    'Pollard': 'Jakeem Pollard', 'Jakeem Pollard': 'Jakeem Pollard',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Bridgetown',
    'dates': ['2026-09-10'],
    'event': {'name': 'Caribbean Premier League', 'match_number': 32},
    'gender': 'male',
    'match_type': 'T20',
    'outcome': {'winner': 'Barbados Tridents', 'by': {'wickets': 4}},
    'overs': 20,
    'player_of_match': ['Chris Green'],
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
        wkts = sum(1 for over in inn['overs'] for deliv in over['deliveries'] for _ in deliv.get('wickets', []))
        n_balls = sum(1 for over in inn['overs'] for deliv in over['deliveries'])
        print(f"  {inn['team']}: total {total}, wickets {wkts}, deliveries logged {n_balls}")

    return match_json


if __name__ == '__main__':
    out = os.path.join(_HERE, 'cpl_2026_match32_tridents_vs_patriots.json')
    build_match_json(out)
