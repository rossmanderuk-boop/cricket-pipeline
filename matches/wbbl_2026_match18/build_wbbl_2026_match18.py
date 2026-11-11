"""
build_wbbl_2026_match18.py - WBBL 2026/27, 18th Match, Sydney Thunder Women vs Perth
Scorchers Women, W.A.C.A, Perth, 2026-11-11.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Sydney Thunder Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Perth Scorchers Women (chased)

TEAM1_NAME = 'Sydney Thunder Women'
TEAM2_NAME = 'Perth Scorchers Women'

TEAM1_XI = [
    'Phoebe Litchfield', 'Georgia Voll', 'Anika Learoyd', 'Heather Knight', 'Laura Harris',
    'Nadine de Klerk', 'Tahlia Wilson', 'Jemma Barsby', 'Hannah Darlington', 'Lauren Bell',
    'Samantha Bates',
]
TEAM2_XI = [
    'Katie Mack', 'Ines Mckeon', 'Sophie Devine', 'Freya Kemp', 'Mikayla Hinkley',
    'Chloe Piparo', 'Fatima Sana', 'Chloe Ainsworth', 'Alana King', 'Lilly Mills',
    'Amy Edgar',
]

NAME_MAP = {
    # Sydney Thunder Women
    'Litchfield': 'Phoebe Litchfield', 'Phoebe Litchfield': 'Phoebe Litchfield',
    'Voll': 'Georgia Voll', 'Georgia Voll': 'Georgia Voll',
    'Learoyd': 'Anika Learoyd', 'Anika Learoyd': 'Anika Learoyd',
    'Knight': 'Heather Knight', 'Heather Knight': 'Heather Knight',
    'Harris': 'Laura Harris', 'Laura Harris': 'Laura Harris',
    'de Klerk': 'Nadine de Klerk', 'Nadine de Klerk': 'Nadine de Klerk',
    'Wilson': 'Tahlia Wilson', 'Tahlia Wilson': 'Tahlia Wilson',
    'Barsby': 'Jemma Barsby', 'Jemma Barsby': 'Jemma Barsby',
    'Darlington': 'Hannah Darlington', 'Hannah Darlington': 'Hannah Darlington',
    'Bell': 'Lauren Bell', 'Lauren Bell': 'Lauren Bell',
    'Bates': 'Samantha Bates', 'Samantha Bates': 'Samantha Bates',
    # Perth Scorchers Women
    'Mack': 'Katie Mack', 'Katie Mack': 'Katie Mack',
    'Mckeon': 'Ines Mckeon', 'Ines Mckeon': 'Ines Mckeon',
    'Devine': 'Sophie Devine', 'Sophie Devine': 'Sophie Devine',
    'Kemp': 'Freya Kemp', 'Freya Kemp': 'Freya Kemp',
    'Hinkley': 'Mikayla Hinkley', 'Mikayla Hinkley': 'Mikayla Hinkley',
    'Piparo': 'Chloe Piparo', 'Chloe Piparo': 'Chloe Piparo',
    'Fatima Sana': 'Fatima Sana',
    'Ainsworth': 'Chloe Ainsworth', 'Chloe Ainsworth': 'Chloe Ainsworth',
    'King': 'Alana King', 'Alana King': 'Alana King',
    'Mills': 'Lilly Mills', 'Lilly Mills': 'Lilly Mills',
    'Edgar': 'Amy Edgar', 'Amy Edgar': 'Amy Edgar',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Perth',
    'dates': ['2026-11-11'],
    'event': {'name': "Women's Big Bash League", 'match_number': 18},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Perth Scorchers Women', 'by': {'wickets': 4}},
    'overs': 20,
    'player_of_match': ['Heather Knight'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Sydney Thunder Women', 'decision': 'bat'},
    'venue': 'Western Australia Cricket Association Ground, Perth',
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
    out = os.path.join(_HERE, 'wbbl_2026_match18_thunder_vs_scorchers.json')
    build_match_json(out)
