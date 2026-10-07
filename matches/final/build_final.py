"""
build_final.py - CPL 2026 Final, Jamaica Kingsmen vs Antigua and Barbuda Falcons,
Kensington Oval, Bridgetown, 2026-09-20.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Jamaica Kingsmen (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Antigua and Barbuda Falcons (chased)

TEAM1_NAME = 'Jamaica Kingsmen'
TEAM2_NAME = 'Antigua and Barbuda Falcons'

TEAM1_XI = [
    'Maaz Sadaqat', 'Kirk McKenzie', 'Keacy Carty', 'Saim Ayub', 'Rovman Powell',
    'Romaine Morris', 'Hassan Khan', 'Keemo Paul', 'Andre Russell', 'Hunain Shah',
    'Vitel Lawes',
]
TEAM2_XI = [
    'Rahkeem Cornwall', 'Evin Lewis', 'Amir Jangoo', 'Hasan Nawaz', 'Moeen Ali',
    'Shadab Khan', 'Shamar Springer', 'Joshua James', 'Alzarri Joseph', 'Sufyan Moqim',
    'Jayden Seales',
]

NAME_MAP = {
    # Jamaica Kingsmen
    'Sadaqat': 'Maaz Sadaqat', 'Maaz Sadaqat': 'Maaz Sadaqat',
    'McKenzie': 'Kirk McKenzie', 'Kirk McKenzie': 'Kirk McKenzie',
    'Carty': 'Keacy Carty', 'Keacy Carty': 'Keacy Carty',
    'Saim Ayub': 'Saim Ayub', 'Ayub': 'Saim Ayub',
    'Powell': 'Rovman Powell', 'Rovman Powell': 'Rovman Powell',
    'Morris': 'Romaine Morris', 'Romaine Morris': 'Romaine Morris',
    'Hassan': 'Hassan Khan', 'Hassan Khan': 'Hassan Khan',
    'Paul': 'Keemo Paul', 'Keemo Paul': 'Keemo Paul',
    'Russell': 'Andre Russell', 'Andre Russell': 'Andre Russell',
    'Hunain Shah': 'Hunain Shah',
    'Lawes': 'Vitel Lawes', 'Vitel Lawes': 'Vitel Lawes',
    # Antigua and Barbuda Falcons
    'Cornwall': 'Rahkeem Cornwall', 'Rahkeem Cornwall': 'Rahkeem Cornwall',
    'Lewis': 'Evin Lewis', 'Evin Lewis': 'Evin Lewis',
    'Jangoo': 'Amir Jangoo', 'Amir Jangoo': 'Amir Jangoo',
    'Hasan Nawaz': 'Hasan Nawaz', 'Nawaz': 'Hasan Nawaz',
    'Moeen Ali': 'Moeen Ali',
    'Shadab': 'Shadab Khan', 'Shadab Khan': 'Shadab Khan',
    'Springer': 'Shamar Springer', 'Shamar Springer': 'Shamar Springer',
    'James': 'Joshua James', 'Joshua James': 'Joshua James',
    'Alzarri Joseph': 'Alzarri Joseph', 'Joseph': 'Alzarri Joseph',
    'Sufyan Moqim': 'Sufyan Moqim', 'Moqim': 'Sufyan Moqim',
    'Seales': 'Jayden Seales', 'Jayden Seales': 'Jayden Seales',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Bridgetown',
    'dates': ['2026-09-20'],
    'event': {'name': 'Caribbean Premier League', 'stage': 'Final'},
    'gender': 'male',
    'match_type': 'T20',
    'outcome': {'winner': 'Antigua and Barbuda Falcons', 'by': {'wickets': 8}},
    'overs': 20,
    'player_of_match': ['Sufyan Moqim'],
    'season': '2026',
    'team_type': 'club',
    'toss': {'winner': 'Antigua and Barbuda Falcons', 'decision': 'field'},
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
    out = os.path.join(_HERE, 'cpl_2026_final_kingsmen_vs_falcons.json')
    build_match_json(out)
