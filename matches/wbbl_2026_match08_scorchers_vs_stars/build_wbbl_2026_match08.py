"""
build_wbbl_2026_match08.py - Women's Big Bash League 2026/27, Match 8,
Perth Scorchers Women vs Melbourne Stars Women, Junction Oval, Melbourne, 2026-11-02 (night).

Note: 5 penalty runs to Scorchers at 5.2 (ball striking fielding-team helmet), shown by
Cricinfo as "(penalty) 1 wide" (6 runs). Recorded on that delivery as extras
{wides: 1, penalty: 5}; penalty runs are not charged to the bowler.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Perth Scorchers Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Melbourne Stars Women (chased)

TEAM1_NAME = 'Perth Scorchers Women'
TEAM2_NAME = 'Melbourne Stars Women'

TEAM1_XI = [
    'Katie Mack', 'Beth Mooney', 'Sophie Devine', 'Freya Kemp', 'Mikayla Hinkley',
    'Chloe Piparo', 'Fatima Sana', 'Chloe Ainsworth', 'Alana King', 'Lilly Mills',
    'Amy Edgar',
]
TEAM2_XI = [
    'Rhys McKenna', 'Meg Lanning', 'Amy Jones', 'Annabel Sutherland', 'Naomi Stalenberg',
    'Charlie Dean', 'Dani Gibson', 'Georgia Prestwidge', 'Kim Garth', 'Maisy Gibson',
    'Sophie Day',
]

# NOTE: "Gibson" is ambiguous (Dani Gibson / Maisy Gibson) and BOTH bowl and bat here.
# Resolved per over (0-indexed) by GIBSON_BOWLING_OVERS (innings 1) and
# GIBSON_BATTING_OVERS (innings 2) below, before NAME_MAP is applied.
NAME_MAP = {
    # Perth Scorchers Women
    'Mack': 'Katie Mack', 'Katie Mack': 'Katie Mack',
    'Mooney': 'Beth Mooney', 'Beth Mooney': 'Beth Mooney',
    'Devine': 'Sophie Devine', 'Sophie Devine': 'Sophie Devine',
    'Kemp': 'Freya Kemp', 'Freya Kemp': 'Freya Kemp',
    'Hinkley': 'Mikayla Hinkley', 'Mikayla Hinkley': 'Mikayla Hinkley',
    'Piparo': 'Chloe Piparo', 'Chloe Piparo': 'Chloe Piparo',
    'Fatima Sana': 'Fatima Sana', 'Sana': 'Fatima Sana',
    'Ainsworth': 'Chloe Ainsworth', 'Chloe Ainsworth': 'Chloe Ainsworth',
    'King': 'Alana King', 'Alana King': 'Alana King',
    'Mills': 'Lilly Mills', 'Lilly Mills': 'Lilly Mills',
    'Edgar': 'Amy Edgar', 'Amy Edgar': 'Amy Edgar',
    # Melbourne Stars Women
    'McKenna': 'Rhys McKenna', 'Rhys McKenna': 'Rhys McKenna',
    'Lanning': 'Meg Lanning', 'Meg Lanning': 'Meg Lanning',
    'Jones': 'Amy Jones', 'Amy Jones': 'Amy Jones',
    'Sutherland': 'Annabel Sutherland', 'Annabel Sutherland': 'Annabel Sutherland',
    'Stalenberg': 'Naomi Stalenberg', 'Naomi Stalenberg': 'Naomi Stalenberg',
    'Dean': 'Charlie Dean', 'Charlie Dean': 'Charlie Dean',
    'Dani Gibson': 'Dani Gibson', 'DR Gibson': 'Dani Gibson',
    'Maisy Gibson': 'Maisy Gibson', 'ML Gibson': 'Maisy Gibson',
    'Prestwidge': 'Georgia Prestwidge', 'Georgia Prestwidge': 'Georgia Prestwidge',
    'Garth': 'Kim Garth', 'Kim Garth': 'Kim Garth',
    'Day': 'Sophie Day', 'Sophie Day': 'Sophie Day',
}

# Innings 1: Dani bowled over 6 (1-0-3-1, Mooney "b DR Gibson"); Maisy bowled overs 10, 13,
# 16 (3-0-10-2, Fatima Sana & Piparo "b ML Gibson"). Over summaries and scorecard agree.
GIBSON_BOWLING_OVERS = {6: 'Dani Gibson', 10: 'Maisy Gibson', 13: 'Maisy Gibson',
                        16: 'Maisy Gibson'}
# Innings 2: Dani batted from 12.5 until out at 16.2; Maisy came in at 17.2 (b King 17.6).
GIBSON_BATTING_OVERS = {12: 'Dani Gibson', 13: 'Dani Gibson', 14: 'Dani Gibson',
                        15: 'Dani Gibson', 16: 'Dani Gibson', 17: 'Maisy Gibson'}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Melbourne',
    'dates': ['2026-11-02'],
    'event': {'name': "Women's Big Bash League", 'match_number': 8},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Perth Scorchers Women', 'by': {'runs': 15}},
    'overs': 20,
    'player_of_match': ['Sophie Devine'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Melbourne Stars Women', 'decision': 'field'},
    'venue': 'Junction Oval, Melbourne',
    'officials': {
        'umpires': ['Chris Grant', 'Louise Broadfoot'],
        'tv_umpires': ['Bede Sajowitz'],
        'reserve_umpires': ['Malcolm Wood'],
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
        if d.get('penalty_runs'):
            extras['penalty'] = d['penalty_runs']
            extras_total += d['penalty_runs']

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
    raw1 = parse_deliveries(t1)
    for d in raw1:
        if d['bowler'] == 'Gibson':
            d['bowler'] = GIBSON_BOWLING_OVERS[d['over']]
    raw2 = parse_deliveries(t2)
    for d in raw2:
        if d['batter'] == 'Gibson':
            d['batter'] = GIBSON_BATTING_OVERS[d['over']]
    d1 = normalise_deliveries(raw1)
    d2 = normalise_deliveries(raw2)

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
    out = os.path.join(_HERE, 'wbbl_2026_match08_scorchers_vs_stars.json')
    build_match_json(out)
