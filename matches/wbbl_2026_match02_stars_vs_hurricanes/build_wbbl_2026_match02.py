"""
build_wbbl_2026_match02.py - Women's Big Bash League 2026/27, Match 2,
Melbourne Stars Women vs Hobart Hurricanes Women, Junction Oval, Melbourne, 2026-10-29 (night).
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Melbourne Stars Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Hobart Hurricanes Women (chased)

TEAM1_NAME = 'Melbourne Stars Women'
TEAM2_NAME = 'Hobart Hurricanes Women'

TEAM1_XI = [
    'Rhys McKenna', 'Meg Lanning', 'Amy Jones', 'Annabel Sutherland', 'Dani Gibson',
    'Kim Garth', 'Naomi Stalenberg', 'Charlie Dean', 'Carly Leeson', 'Maisy Gibson',
    'Sophie Day',
]
TEAM2_XI = [
    'Lizelle Lee', 'Chamari Athapaththu', 'Rachel Trenaman', 'Nicola Carey',
    'Heather Graham', 'Maddy Green', 'Chinelle Henry', 'Ruth Johnston', 'Lauren Smith',
    'Molly Strano', 'Ira Aery',
]

# NOTE: "Gibson" is ambiguous (Dani Gibson / Maisy Gibson). As a batter in innings 1 it is
# Dani Gibson (only Gibson to bat). As a bowler in innings 2 it is resolved per over by
# GIBSON_BOWLING_OVERS below, not by NAME_MAP.
NAME_MAP = {
    # Melbourne Stars Women
    'McKenna': 'Rhys McKenna', 'Rhys McKenna': 'Rhys McKenna',
    'Lanning': 'Meg Lanning', 'Meg Lanning': 'Meg Lanning',
    'Jones': 'Amy Jones', 'Amy Jones': 'Amy Jones',
    'Sutherland': 'Annabel Sutherland', 'Annabel Sutherland': 'Annabel Sutherland',
    'Gibson': 'Dani Gibson', 'Dani Gibson': 'Dani Gibson',
    'ML Gibson': 'Maisy Gibson', 'Maisy Gibson': 'Maisy Gibson',
    'Garth': 'Kim Garth', 'Kim Garth': 'Kim Garth',
    'Stalenberg': 'Naomi Stalenberg', 'Naomi Stalenberg': 'Naomi Stalenberg',
    'Dean': 'Charlie Dean', 'Charlie Dean': 'Charlie Dean',
    'Leeson': 'Carly Leeson', 'Carly Leeson': 'Carly Leeson',
    'Day': 'Sophie Day', 'Sophie Day': 'Sophie Day',
    # Hobart Hurricanes Women
    'Lee': 'Lizelle Lee', 'Lizelle Lee': 'Lizelle Lee',
    'Athapaththu': 'Chamari Athapaththu', 'Chamari Athapaththu': 'Chamari Athapaththu',
    'Trenaman': 'Rachel Trenaman', 'Rachel Trenaman': 'Rachel Trenaman',
    'Carey': 'Nicola Carey', 'Nicola Carey': 'Nicola Carey',
    'Graham': 'Heather Graham', 'Heather Graham': 'Heather Graham',
    'Green': 'Maddy Green', 'Maddy Green': 'Maddy Green',
    'Henry': 'Chinelle Henry', 'Chinelle Henry': 'Chinelle Henry',
    'Johnston': 'Ruth Johnston', 'Ruth Johnston': 'Ruth Johnston',
    'Smith': 'Lauren Smith', 'Lauren Smith': 'Lauren Smith',
    'Strano': 'Molly Strano', 'Molly Strano': 'Molly Strano',
    'Aery': 'Ira Aery', 'Ira Aery': 'Ira Aery',
}

# Innings-2 overs (0-indexed) bowled by "Gibson". Resolved from the scorecard bowling
# figures (Dani Gibson 2-0-23-0, Maisy Gibson 3-0-25-2) and the dismissal lines
# ("b ML Gibson" in overs 15 and 19). Only this split fits: Dani = overs 5 & 9 (9+14 = 23),
# Maisy = overs 13, 15, 19 (7+9+9 = 25, both wickets).
# CAVEAT: Cricinfo's end-of-over summaries name these the other way round, and the
# scorecard's 0s column (Dani 9, Maisy 2) also fits the swapped version. See validation.
GIBSON_BOWLING_OVERS = {5: 'Dani Gibson', 9: 'Dani Gibson',
                        13: 'Maisy Gibson', 15: 'Maisy Gibson', 19: 'Maisy Gibson'}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Melbourne',
    'dates': ['2026-10-29'],
    'event': {'name': "Women's Big Bash League", 'match_number': 2},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Melbourne Stars Women', 'by': {'runs': 18}},
    'overs': 20,
    'player_of_match': ['Annabel Sutherland'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Hobart Hurricanes Women', 'decision': 'field'},
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
    raw2 = parse_deliveries(t2)
    for d in raw2:
        if d['bowler'] == 'Gibson':
            d['bowler'] = GIBSON_BOWLING_OVERS[d['over']]
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
    out = os.path.join(_HERE, 'wbbl_2026_match02_stars_vs_hurricanes.json')
    build_match_json(out)
