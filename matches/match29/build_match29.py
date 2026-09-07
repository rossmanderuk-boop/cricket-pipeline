"""
build_match29.py - CPL 2026, 29th Match, St Lucia Kings vs Barbados Tridents,
Kensington Oval, Bridgetown, Barbados, 2026-09-06.

Note: 'Clarke' is ambiguous in this match - McKenny Clarke bats for Kings (innings 1)
and Rivaldo Clarke bats for Tridents (innings 2). Within innings1.txt the bare name
'Clarke' is used BOTH as a batter (McKenny Clarke, over 19) AND as a fielder in one
dismissal line ("Matthew Forde c Clarke b Mujeeb Ur Rahman") where it can only mean
Rivaldo Clarke (Tridents' fielder, since Kings are batting). A single global NAME_MAP
can't resolve this, so per-innings/per-role overrides are used below instead.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # St Lucia Kings (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Barbados Tridents (chased)

TEAM1_NAME = 'St Lucia Kings'
TEAM2_NAME = 'Barbados Tridents'

TEAM1_XI = [
    'Tim Seifert', 'Kamil Pooran', 'John Campbell', 'Roston Chase', 'Charith Asalanka',
    'Obus Pienaar', 'Matthew Forde', 'McKenny Clarke', 'Amari Goodridge', 'Joshua Bishop',
    'Maheesh Theekshana',
]
TEAM2_XI = [
    'Brandon King', 'Zachary Carter', 'Rivaldo Clarke', 'Quinton de Kock', 'Chris Green',
    'Sherfane Rutherford', 'Shadrack Descarte', 'Daniel Sams', 'Gudakesh Motie',
    'Mujeeb Ur Rahman', 'Jakeem Pollard',
]

NAME_MAP = {
    # St Lucia Kings
    'Seifert': 'Tim Seifert', 'Tim Seifert': 'Tim Seifert',
    'Kamil Pooran': 'Kamil Pooran',
    'Campbell': 'John Campbell', 'John Campbell': 'John Campbell',
    'Chase': 'Roston Chase', 'Roston Chase': 'Roston Chase',
    'Asalanka': 'Charith Asalanka', 'Charith Asalanka': 'Charith Asalanka',
    'Pienaar': 'Obus Pienaar', 'Obus Pienaar': 'Obus Pienaar',
    'Forde': 'Matthew Forde', 'Matthew Forde': 'Matthew Forde',
    'McKenny Clarke': 'McKenny Clarke',
    'Goodridge': 'Amari Goodridge', 'Amari Goodridge': 'Amari Goodridge',
    'Bishop': 'Joshua Bishop', 'Joshua Bishop': 'Joshua Bishop',
    'Theekshana': 'Maheesh Theekshana', 'Maheesh Theekshana': 'Maheesh Theekshana',
    # Barbados Tridents
    'King': 'Brandon King', 'Brandon King': 'Brandon King',
    'Carter': 'Zachary Carter', 'Zachary Carter': 'Zachary Carter',
    'Rivaldo Clarke': 'Rivaldo Clarke',
    'de Kock': 'Quinton de Kock', 'Quinton de Kock': 'Quinton de Kock',
    'Green': 'Chris Green', 'Chris Green': 'Chris Green',
    'Rutherford': 'Sherfane Rutherford', 'Sherfane Rutherford': 'Sherfane Rutherford',
    'Descarte': 'Shadrack Descarte', 'Shadrack Descarte': 'Shadrack Descarte',
    'Sams': 'Daniel Sams', 'Daniel Sams': 'Daniel Sams',
    'Motie': 'Gudakesh Motie', 'Gudakesh Motie': 'Gudakesh Motie',
    'Mujeeb': 'Mujeeb Ur Rahman', 'Mujeeb Ur Rahman': 'Mujeeb Ur Rahman',
    'Pollard': 'Jakeem Pollard', 'Jakeem Pollard': 'Jakeem Pollard',
}

# 'Clarke' collision - see module docstring.
INNINGS1_OVERRIDE = {'Clarke': 'McKenny Clarke'}          # batter/bowler/non-striker/player_out
INNINGS1_FIELDER_OVERRIDE = {'Clarke': 'Rivaldo Clarke'}  # fielder in a dismissal line
INNINGS2_OVERRIDE = {'Clarke': 'Rivaldo Clarke'}          # batter/bowler/non-striker/player_out

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Bridgetown',
    'dates': ['2026-09-06'],
    'event': {'name': 'Caribbean Premier League', 'match_number': 29},
    'gender': 'male',
    'match_type': 'T20',
    'outcome': {'winner': 'Barbados Tridents', 'by': {'wickets': 8}},
    'overs': 20,
    'player_of_match': ['Mujeeb Ur Rahman'],
    'season': '2026',
    'team_type': 'club',
    'toss': {'winner': 'Barbados Tridents', 'decision': 'field'},
    'venue': 'Kensington Oval, Bridgetown, Barbados',
}

KNOWN_IDS = {}


# =============================================================================
# Reusable logic (adapted from build_match_json_template.py to support
# per-innings/per-role name overrides for the 'Clarke' collision)
# =============================================================================

def norm(name, overrides=None):
    name = name.strip()
    if overrides and name in overrides:
        return overrides[name]
    return NAME_MAP.get(name, name)


def normalise_deliveries(deliveries, overrides=None, fielder_overrides=None):
    fielder_overrides = fielder_overrides or overrides
    for d in deliveries:
        d['batter'] = norm(d['batter'], overrides)
        d['bowler'] = norm(d['bowler'], overrides)
        if d['wicket']:
            d['wicket']['player_out'] = norm(d['wicket']['player_out'], overrides)
            if d['wicket'].get('fielder'):
                parts = [norm(p, fielder_overrides) for p in d['wicket']['fielder'].split('/')]
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
    d1 = normalise_deliveries(parse_deliveries(t1), overrides=INNINGS1_OVERRIDE,
                               fielder_overrides=INNINGS1_FIELDER_OVERRIDE)
    d2 = normalise_deliveries(parse_deliveries(t2), overrides=INNINGS2_OVERRIDE)

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
    out = os.path.join(_HERE, 'cpl_2026_match29_kings_vs_tridents.json')
    build_match_json(out)
