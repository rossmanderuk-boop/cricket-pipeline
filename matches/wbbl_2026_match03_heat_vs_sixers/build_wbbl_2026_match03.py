"""
build_wbbl_2026_match03.py - Women's Big Bash League 2026/27, Match 3,
Brisbane Heat Women vs Sydney Sixers Women, Allan Border Field, Brisbane, 2026-10-30.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Brisbane Heat Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Sydney Sixers Women (chased)

TEAM1_NAME = 'Brisbane Heat Women'
TEAM2_NAME = 'Sydney Sixers Women'

TEAM1_XI = [
    'Charli Knott', 'Grace Harris', 'Georgia Redmayne', 'Orla Prendergast', "Annie O'Neil",
    'Lucy Hamilton', 'Sianna Ginger', 'Lucinda Bourke', 'Sarah Glenn',
    'Lily Bassingthwaighte', 'Ayaka Kato-Stafford',
]
TEAM2_XI = [
    'Ellyse Perry', 'Sophia Dunkley', 'Melie Kerr', 'Ashleigh Gardner', 'Alice Capsey',
    'Eva Ragg', 'Erin Burns', 'Sarah Coyte', 'Lauren Cheatle', 'Caoimhe Bray',
    'Frankie Nicklin',
]

NAME_MAP = {
    # Brisbane Heat Women
    'Knott': 'Charli Knott', 'Charli Knott': 'Charli Knott',
    'Harris': 'Grace Harris', 'Grace Harris': 'Grace Harris',
    'Redmayne': 'Georgia Redmayne', 'Georgia Redmayne': 'Georgia Redmayne',
    'Prendergast': 'Orla Prendergast', 'O Prendergast': 'Orla Prendergast',
    'Orla Prendergast': 'Orla Prendergast',
    "O'Neil": "Annie O'Neil", "Annie O'Neil": "Annie O'Neil",
    'Hamilton': 'Lucy Hamilton', 'Lucy Hamilton': 'Lucy Hamilton',
    'Ginger': 'Sianna Ginger', 'Sianna Ginger': 'Sianna Ginger',
    'Bourke': 'Lucinda Bourke', 'Lucinda Bourke': 'Lucinda Bourke',
    'Glenn': 'Sarah Glenn', 'Sarah Glenn': 'Sarah Glenn',
    'Bassingthwaighte': 'Lily Bassingthwaighte', 'L Bassingthwaighte': 'Lily Bassingthwaighte',
    'Lily Bassingthwaighte': 'Lily Bassingthwaighte',
    'Kato-Stafford': 'Ayaka Kato-Stafford', 'A Kato-Stafford': 'Ayaka Kato-Stafford',
    'Ayaka Kato-Stafford': 'Ayaka Kato-Stafford',
    # Sydney Sixers Women
    'Perry': 'Ellyse Perry', 'Ellyse Perry': 'Ellyse Perry',
    'Dunkley': 'Sophia Dunkley', 'Sophia Dunkley': 'Sophia Dunkley',
    'Kerr': 'Melie Kerr', 'Melie Kerr': 'Melie Kerr',
    'Gardner': 'Ashleigh Gardner', 'Ashleigh Gardner': 'Ashleigh Gardner',
    'Capsey': 'Alice Capsey', 'Alice Capsey': 'Alice Capsey',
    'Ragg': 'Eva Ragg', 'Eva Ragg': 'Eva Ragg',
    'Burns': 'Erin Burns', 'Erin Burns': 'Erin Burns',
    'Coyte': 'Sarah Coyte', 'Sarah Coyte': 'Sarah Coyte',
    'Cheatle': 'Lauren Cheatle', 'Lauren Cheatle': 'Lauren Cheatle',
    'Bray': 'Caoimhe Bray', 'Caoimhe Bray': 'Caoimhe Bray',
    'Nicklin': 'Frankie Nicklin', 'Frankie Nicklin': 'Frankie Nicklin',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Brisbane',
    'dates': ['2026-10-30'],
    'event': {'name': "Women's Big Bash League", 'match_number': 3},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Sydney Sixers Women', 'by': {'wickets': 4}},
    'overs': 20,
    'player_of_match': ['Ellyse Perry'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Sydney Sixers Women', 'decision': 'field'},
    'venue': 'Allan Border Field, Brisbane',
    'officials': {
        'umpires': ['Kylie White', 'Nathan James'],
        'tv_umpires': ['Riki Wessels'],
        'reserve_umpires': ['Benjamin Farrell'],
        'match_referees': ['Joanne Broadbent'],
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
    out = os.path.join(_HERE, 'wbbl_2026_match03_heat_vs_sixers.json')
    build_match_json(out)
