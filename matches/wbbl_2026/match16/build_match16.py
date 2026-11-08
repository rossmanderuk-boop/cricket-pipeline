"""
build_match16.py - WBBL 2026/27, match 16, Melbourne Stars Women vs Perth Scorchers Women, North Sydney Oval, Sydney, 2026-11-08.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Melbourne Stars Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Perth Scorchers Women (batted second)

TEAM1_NAME = 'Melbourne Stars Women'
TEAM2_NAME = 'Perth Scorchers Women'

TEAM1_XI = ['Meg Lanning', 'Rhys McKenna', 'Amy Jones', 'Annabel Sutherland', 'Naomi Stalenberg', 'Dani Gibson', 'Charlie Dean', 'Georgia Prestwidge', 'Kim Garth', 'Maisy Gibson', 'Sophie Day']
TEAM2_XI = ['Katie Mack', 'Beth Mooney', 'Sophie Devine', 'Freya Kemp', 'Mikayla Hinkley', 'Chloe Piparo', 'Fatima Sana', 'Chloe Ainsworth', 'Alana King', 'Lilly Mills', 'Amy Edgar']

NAME_MAP = {
    'Meg Lanning': 'Meg Lanning',
    'Lanning': 'Meg Lanning',
    'Rhys McKenna': 'Rhys McKenna',
    'McKenna': 'Rhys McKenna',
    'Amy Jones': 'Amy Jones',
    'Jones': 'Amy Jones',
    'Annabel Sutherland': 'Annabel Sutherland',
    'Sutherland': 'Annabel Sutherland',
    'Naomi Stalenberg': 'Naomi Stalenberg',
    'Stalenberg': 'Naomi Stalenberg',
    'Dani Gibson': 'Dani Gibson',
    'Gibson': 'Dani Gibson',
    'Charlie Dean': 'Charlie Dean',
    'Dean': 'Charlie Dean',
    'Georgia Prestwidge': 'Georgia Prestwidge',
    'Prestwidge': 'Georgia Prestwidge',
    'Kim Garth': 'Kim Garth',
    'Garth': 'Kim Garth',
    'Maisy Gibson': 'Maisy Gibson',
    'Sophie Day': 'Sophie Day',
    'Day': 'Sophie Day',
    'Katie Mack': 'Katie Mack',
    'Mack': 'Katie Mack',
    'Beth Mooney': 'Beth Mooney',
    'Mooney': 'Beth Mooney',
    'Sophie Devine': 'Sophie Devine',
    'Devine': 'Sophie Devine',
    'Freya Kemp': 'Freya Kemp',
    'Kemp': 'Freya Kemp',
    'Mikayla Hinkley': 'Mikayla Hinkley',
    'Hinkley': 'Mikayla Hinkley',
    'Chloe Piparo': 'Chloe Piparo',
    'Piparo': 'Chloe Piparo',
    'Fatima Sana': 'Fatima Sana',
    'Sana': 'Fatima Sana',
    'Chloe Ainsworth': 'Chloe Ainsworth',
    'Ainsworth': 'Chloe Ainsworth',
    'Alana King': 'Alana King',
    'King': 'Alana King',
    'Lilly Mills': 'Lilly Mills',
    'Mills': 'Lilly Mills',
    'Amy Edgar': 'Amy Edgar',
    'Edgar': 'Amy Edgar',
}

BOWLER_OVERRIDES = {}

MATCH_INFO = {'balls_per_over': 6, 'city': 'Sydney', 'dates': ['2026-11-08'], 'event': {'name': "Women's Big Bash League", 'match_number': 16}, 'gender': 'female', 'match_type': 'T20', 'outcome': {'winner': 'Perth Scorchers Women', 'by': {'wickets': 6}}, 'overs': 20, 'player_of_match': ['Sophie Devine'], 'season': '2026/27', 'team_type': 'club', 'toss': {'winner': 'Melbourne Stars Women', 'decision': 'bat'}, 'venue': 'North Sydney Oval, Sydney', 'officials': {'umpires': ['Mitchell Claydon', 'Roberto Howard'], 'tv_umpires': ['Sharad Patel'], 'reserve_umpires': ['Syed Humayun'], 'match_referees': ['Janine Stainer']}}

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
    out = os.path.join(_HERE, 'wbbl_2026_match16_stars_vs_scorchers.json')
    build_match_json(out)
