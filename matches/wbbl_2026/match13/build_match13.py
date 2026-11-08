"""
build_match13.py - WBBL 2026/27, match 13, Melbourne Renegades Women vs Adelaide Strikers Women, Junction Oval, Melbourne, 2026-11-07.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Melbourne Renegades Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Adelaide Strikers Women (batted second)

TEAM1_NAME = 'Melbourne Renegades Women'
TEAM2_NAME = 'Adelaide Strikers Women'

TEAM1_XI = ['Olivia Porter', 'Hayley Matthews', 'Courtney Webb', 'Sophie Molineux', 'Georgia Wareham', 'Tess Flintoff', 'Nicole Faltum', 'Chloe Tryon', 'Deandra Dottin', 'Milly Illingworth', 'Tayla Vlaeminck']
TEAM2_XI = ['Emma de Broughe', 'Maia Bouchier', 'Laura Wolvaardt', 'Tahlia McGrath', 'Madeline Penna', 'Bridget Patterson', 'Amanda-Jade Wellington', 'Sophie Ecclestone', 'Eleanor Larosa', 'Megan Schutt', 'Anesu Mushangwe']

NAME_MAP = {
    'Olivia Porter': 'Olivia Porter',
    'Porter': 'Olivia Porter',
    'Hayley Matthews': 'Hayley Matthews',
    'Matthews': 'Hayley Matthews',
    'Courtney Webb': 'Courtney Webb',
    'Webb': 'Courtney Webb',
    'Sophie Molineux': 'Sophie Molineux',
    'Molineux': 'Sophie Molineux',
    'Georgia Wareham': 'Georgia Wareham',
    'Wareham': 'Georgia Wareham',
    'Tess Flintoff': 'Tess Flintoff',
    'Flintoff': 'Tess Flintoff',
    'Nicole Faltum': 'Nicole Faltum',
    'Faltum': 'Nicole Faltum',
    'Chloe Tryon': 'Chloe Tryon',
    'Tryon': 'Chloe Tryon',
    'Deandra Dottin': 'Deandra Dottin',
    'Dottin': 'Deandra Dottin',
    'Milly Illingworth': 'Milly Illingworth',
    'Illingworth': 'Milly Illingworth',
    'Tayla Vlaeminck': 'Tayla Vlaeminck',
    'Vlaeminck': 'Tayla Vlaeminck',
    'Emma de Broughe': 'Emma de Broughe',
    'Broughe': 'Emma de Broughe',
    'Maia Bouchier': 'Maia Bouchier',
    'Bouchier': 'Maia Bouchier',
    'Laura Wolvaardt': 'Laura Wolvaardt',
    'Wolvaardt': 'Laura Wolvaardt',
    'Tahlia McGrath': 'Tahlia McGrath',
    'McGrath': 'Tahlia McGrath',
    'Madeline Penna': 'Madeline Penna',
    'Penna': 'Madeline Penna',
    'Bridget Patterson': 'Bridget Patterson',
    'Patterson': 'Bridget Patterson',
    'Amanda-Jade Wellington': 'Amanda-Jade Wellington',
    'Wellington': 'Amanda-Jade Wellington',
    'Sophie Ecclestone': 'Sophie Ecclestone',
    'Ecclestone': 'Sophie Ecclestone',
    'Eleanor Larosa': 'Eleanor Larosa',
    'Larosa': 'Eleanor Larosa',
    'Megan Schutt': 'Megan Schutt',
    'Schutt': 'Megan Schutt',
    'Anesu Mushangwe': 'Anesu Mushangwe',
    'Mushangwe': 'Anesu Mushangwe',
    'MH Illingworth': 'Milly Illingworth',
    'de Broughe': 'Emma de Broughe',
}

BOWLER_OVERRIDES = {}

MATCH_INFO = {'balls_per_over': 6, 'city': 'Melbourne', 'dates': ['2026-11-07'], 'event': {'name': "Women's Big Bash League", 'match_number': 13}, 'gender': 'female', 'match_type': 'T20', 'outcome': {'winner': 'Melbourne Renegades Women', 'by': {'runs': 36}}, 'overs': 20, 'player_of_match': ['Georgia Wareham'], 'season': '2026/27', 'team_type': 'club', 'toss': {'winner': 'Adelaide Strikers Women', 'decision': 'field'}, 'venue': 'Junction Oval, Melbourne', 'officials': {'umpires': ['Chris Grant', 'Malcolm Wood'], 'tv_umpires': ['Clare Haysom'], 'reserve_umpires': ['Ashfaq Ali'], 'match_referees': ['Bob Parry']}}

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
    for inn_no, dels in ((1, d1), (2, d2)):
        for d in dels:
            if (inn_no, d['over']) in BOWLER_OVERRIDES:
                d['bowler'] = BOWLER_OVERRIDES[(inn_no, d['over'])]

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
    out = os.path.join(_HERE, 'wbbl_2026_match13_renegades_vs_strikers.json')
    build_match_json(out)
