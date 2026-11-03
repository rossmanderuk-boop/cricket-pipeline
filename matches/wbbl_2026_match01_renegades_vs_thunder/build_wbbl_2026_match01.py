"""
build_wbbl_2026_match01.py - Women's Big Bash League 2026/27,
Melbourne Renegades Women vs Sydney Thunder Women, Junction Oval, Melbourne, 2026-10-29.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Melbourne Renegades Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Sydney Thunder Women (chased)

TEAM1_NAME = 'Melbourne Renegades Women'
TEAM2_NAME = 'Sydney Thunder Women'

TEAM1_XI = [
    'Courtney Webb', 'Hayley Matthews', 'Sophie Molineux', 'Georgia Wareham',
    'Tess Flintoff', 'Chloe Tryon', 'Deandra Dottin', 'Nicole Faltum',
    'Annie Wikman', 'Milly Illingworth', 'Tayla Vlaeminck',
]
TEAM2_XI = [
    'Georgia Voll', 'Phoebe Litchfield', 'Anika Learoyd', 'Heather Knight',
    'Laura Harris', 'Nadine de Klerk', 'Tahlia Wilson', 'Hannah Darlington',
    'Hasrat Gill', 'Lauren Bell', 'Samantha Bates',
]

NAME_MAP = {
    # Melbourne Renegades Women
    'Webb': 'Courtney Webb', 'Courtney Webb': 'Courtney Webb',
    'Matthews': 'Hayley Matthews', 'Hayley Matthews': 'Hayley Matthews',
    'Molineux': 'Sophie Molineux', 'Sophie Molineux': 'Sophie Molineux',
    'Wareham': 'Georgia Wareham', 'Georgia Wareham': 'Georgia Wareham',
    'Flintoff': 'Tess Flintoff', 'Tess Flintoff': 'Tess Flintoff',
    'Tryon': 'Chloe Tryon', 'Chloe Tryon': 'Chloe Tryon',
    'Dottin': 'Deandra Dottin', 'Deandra Dottin': 'Deandra Dottin',
    'Faltum': 'Nicole Faltum', 'Nicole Faltum': 'Nicole Faltum',
    'Wikman': 'Annie Wikman', 'Annie Wikman': 'Annie Wikman',
    'Illingworth': 'Milly Illingworth', 'MH Illingworth': 'Milly Illingworth',
    'Milly Illingworth': 'Milly Illingworth',
    'Vlaeminck': 'Tayla Vlaeminck', 'Tayla Vlaeminck': 'Tayla Vlaeminck',
    # Sydney Thunder Women
    'Voll': 'Georgia Voll', 'Georgia Voll': 'Georgia Voll',
    'Litchfield': 'Phoebe Litchfield', 'Phoebe Litchfield': 'Phoebe Litchfield',
    'Learoyd': 'Anika Learoyd', 'Anika Learoyd': 'Anika Learoyd',
    'Knight': 'Heather Knight', 'Heather Knight': 'Heather Knight',
    'Harris': 'Laura Harris', 'Laura Harris': 'Laura Harris',
    'de Klerk': 'Nadine de Klerk', 'Nadine de Klerk': 'Nadine de Klerk',
    'Wilson': 'Tahlia Wilson', 'Tahlia Wilson': 'Tahlia Wilson',
    'Darlington': 'Hannah Darlington', 'Hannah Darlington': 'Hannah Darlington',
    'Gill': 'Hasrat Gill', 'Hasrat Gill': 'Hasrat Gill',
    'Bell': 'Lauren Bell', 'Lauren Bell': 'Lauren Bell',
    'Bates': 'Samantha Bates', 'Samantha Bates': 'Samantha Bates',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Melbourne',
    'dates': ['2026-10-29'],
    'event': {'name': "Women's Big Bash League", 'match_number': 1},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Sydney Thunder Women', 'by': {'wickets': 6}},
    'overs': 20,
    'player_of_match': ['Georgia Voll'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Sydney Thunder Women', 'decision': 'field'},
    'venue': 'Junction Oval, Melbourne',
    'officials': {
    'umpires': ['Bede Sajowitz', 'Clare Haysom'],
    'tv_umpires': ['Mitchell Claydon'],
    'reserve_umpires': ['Louise Broadfoot'],
    'match_referees': ['Sarah Elliott'],
    },
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
    out = os.path.join(_HERE, 'wbbl_2026_match01_renegades_vs_thunder.json')
    build_match_json(out)
