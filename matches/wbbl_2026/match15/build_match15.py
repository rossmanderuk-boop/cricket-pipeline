"""
build_match15.py - WBBL 2026/27, match 15, Sydney Sixers Women vs Sydney Thunder Women, North Sydney Oval, Sydney, 2026-11-08.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Sydney Sixers Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Sydney Thunder Women (batted second)

TEAM1_NAME = 'Sydney Sixers Women'
TEAM2_NAME = 'Sydney Thunder Women'

TEAM1_XI = ['Sophia Dunkley', 'Ellyse Perry', 'Melie Kerr', 'Ashleigh Gardner', 'Alice Capsey', 'Erin Burns', 'Eva Ragg', 'Lauren Cheatle', 'Sarah Coyte', 'Caoimhe Bray', 'Frankie Nicklin']
TEAM2_XI = ['Phoebe Litchfield', 'Georgia Voll', 'Anika Learoyd', 'Heather Knight', 'Nadine de Klerk', 'Laura Harris', 'Tahlia Wilson', 'Jemma Barsby', 'Hannah Darlington', 'Lauren Bell', 'Samantha Bates']

NAME_MAP = {
    'Sophia Dunkley': 'Sophia Dunkley',
    'Dunkley': 'Sophia Dunkley',
    'Ellyse Perry': 'Ellyse Perry',
    'Perry': 'Ellyse Perry',
    'Melie Kerr': 'Melie Kerr',
    'Kerr': 'Melie Kerr',
    'Ashleigh Gardner': 'Ashleigh Gardner',
    'Gardner': 'Ashleigh Gardner',
    'Alice Capsey': 'Alice Capsey',
    'Capsey': 'Alice Capsey',
    'Erin Burns': 'Erin Burns',
    'Burns': 'Erin Burns',
    'Eva Ragg': 'Eva Ragg',
    'Ragg': 'Eva Ragg',
    'Lauren Cheatle': 'Lauren Cheatle',
    'Cheatle': 'Lauren Cheatle',
    'Sarah Coyte': 'Sarah Coyte',
    'Coyte': 'Sarah Coyte',
    'Caoimhe Bray': 'Caoimhe Bray',
    'Bray': 'Caoimhe Bray',
    'Frankie Nicklin': 'Frankie Nicklin',
    'Nicklin': 'Frankie Nicklin',
    'Phoebe Litchfield': 'Phoebe Litchfield',
    'Litchfield': 'Phoebe Litchfield',
    'Georgia Voll': 'Georgia Voll',
    'Voll': 'Georgia Voll',
    'Anika Learoyd': 'Anika Learoyd',
    'Learoyd': 'Anika Learoyd',
    'Heather Knight': 'Heather Knight',
    'Knight': 'Heather Knight',
    'Nadine de Klerk': 'Nadine de Klerk',
    'Klerk': 'Nadine de Klerk',
    'Laura Harris': 'Laura Harris',
    'Harris': 'Laura Harris',
    'Tahlia Wilson': 'Tahlia Wilson',
    'Wilson': 'Tahlia Wilson',
    'Jemma Barsby': 'Jemma Barsby',
    'Barsby': 'Jemma Barsby',
    'Hannah Darlington': 'Hannah Darlington',
    'Darlington': 'Hannah Darlington',
    'Lauren Bell': 'Lauren Bell',
    'Bell': 'Lauren Bell',
    'Samantha Bates': 'Samantha Bates',
    'Bates': 'Samantha Bates',
    'de Klerk': 'Nadine de Klerk',
}

BOWLER_OVERRIDES = {}

MATCH_INFO = {'balls_per_over': 6, 'city': 'Sydney', 'dates': ['2026-11-08'], 'event': {'name': "Women's Big Bash League", 'match_number': 15}, 'gender': 'female', 'match_type': 'T20', 'outcome': {'winner': 'Sydney Sixers Women', 'by': {'runs': 9}, 'method': 'D/L'}, 'overs': 16, 'player_of_match': ['Ashleigh Gardner'], 'season': '2026/27', 'team_type': 'club', 'toss': {'winner': 'Sydney Thunder Women', 'decision': 'field'}, 'venue': 'North Sydney Oval, Sydney', 'officials': {'umpires': ['Mitchell Claydon', 'Roberto Howard'], 'tv_umpires': ['Sharad Patel'], 'reserve_umpires': ['Syed Humayun'], 'match_referees': ['Dave Gilbert']}}

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
    out = os.path.join(_HERE, 'wbbl_2026_match15_sixers_vs_thunder.json')
    build_match_json(out)
