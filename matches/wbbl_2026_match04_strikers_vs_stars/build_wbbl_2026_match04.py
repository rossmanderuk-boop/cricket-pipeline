"""
build_wbbl_2026_match04.py - Women's Big Bash League 2026/27, Match 4,
Adelaide Strikers Women vs Melbourne Stars Women, Karen Rolton Oval, Adelaide, 2026-10-31.

Note: Cricinfo labels three innings-1 deliveries "6.1" (a wide, then 2 runs, then FOUR) and
the over ends at "6.5". That is still six legal balls + 1 wide, 8 runs; ball labels are not
used for ordering, so no fix is needed.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Adelaide Strikers Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Melbourne Stars Women (chased)

TEAM1_NAME = 'Adelaide Strikers Women'
TEAM2_NAME = 'Melbourne Stars Women'

TEAM1_XI = [
    'Laura Wolvaardt', 'Maia Bouchier', 'Tahlia McGrath', 'Madeline Penna',
    'Bridget Patterson', 'Ellie Johnston', 'Eleanor Larosa', 'Amanda-Jade Wellington',
    'Sophie Ecclestone', 'Ella Wilson', 'Anesu Mushangwe',
]
TEAM2_XI = [
    'Rhys McKenna', 'Meg Lanning', 'Amy Jones', 'Annabel Sutherland', 'Naomi Stalenberg',
    'Dani Gibson', 'Charlie Dean', 'Kim Garth', 'Carly Leeson', 'Maisy Gibson',
    'Sophie Day',
]

# NOTE: "Gibson" is ambiguous (Dani Gibson / Maisy Gibson). As a batter in innings 2 it is
# Dani Gibson (only Gibson to bat). As a bowler in innings 1 it is resolved per over by
# GIBSON_BOWLING_OVERS below.
NAME_MAP = {
    # Adelaide Strikers Women
    'Wolvaardt': 'Laura Wolvaardt', 'Laura Wolvaardt': 'Laura Wolvaardt',
    'Bouchier': 'Maia Bouchier', 'Maia Bouchier': 'Maia Bouchier',
    'McGrath': 'Tahlia McGrath', 'Tahlia McGrath': 'Tahlia McGrath',
    'Penna': 'Madeline Penna', 'Madeline Penna': 'Madeline Penna',
    'Patterson': 'Bridget Patterson', 'Bridget Patterson': 'Bridget Patterson',
    'Johnston': 'Ellie Johnston', 'Ellie Johnston': 'Ellie Johnston',
    'Larosa': 'Eleanor Larosa', 'Eleanor Larosa': 'Eleanor Larosa',
    'Wellington': 'Amanda-Jade Wellington', 'Amanda-Jade Wellington': 'Amanda-Jade Wellington',
    'Ecclestone': 'Sophie Ecclestone', 'Sophie Ecclestone': 'Sophie Ecclestone',
    'Wilson': 'Ella Wilson', 'Ella Wilson': 'Ella Wilson',
    'Mushangwe': 'Anesu Mushangwe', 'Anesu Mushangwe': 'Anesu Mushangwe',
    # Melbourne Stars Women
    'McKenna': 'Rhys McKenna', 'Rhys McKenna': 'Rhys McKenna',
    'Lanning': 'Meg Lanning', 'Meg Lanning': 'Meg Lanning',
    'Jones': 'Amy Jones', 'Amy Jones': 'Amy Jones',
    'Sutherland': 'Annabel Sutherland', 'Annabel Sutherland': 'Annabel Sutherland',
    'Stalenberg': 'Naomi Stalenberg', 'Naomi Stalenberg': 'Naomi Stalenberg',
    'Gibson': 'Dani Gibson', 'Dani Gibson': 'Dani Gibson',
    'ML Gibson': 'Maisy Gibson', 'Maisy Gibson': 'Maisy Gibson',
    'Dean': 'Charlie Dean', 'Charlie Dean': 'Charlie Dean',
    'Garth': 'Kim Garth', 'Kim Garth': 'Kim Garth',
    'Leeson': 'Carly Leeson', 'Carly Leeson': 'Carly Leeson',
    'Day': 'Sophie Day', 'Sophie Day': 'Sophie Day',
}

# Innings-1 overs (0-indexed) bowled by "Gibson". Cricinfo's end-of-over summaries and the
# scorecard agree here: Maisy 1-0-11-0 (over 7), Dani 4-0-47-0 (overs 8, 11, 16, 18).
GIBSON_BOWLING_OVERS = {7: 'Maisy Gibson', 8: 'Dani Gibson', 11: 'Dani Gibson',
                        16: 'Dani Gibson', 18: 'Dani Gibson'}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Adelaide',
    'dates': ['2026-10-31'],
    'event': {'name': "Women's Big Bash League", 'match_number': 4},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Adelaide Strikers Women', 'by': {'runs': 21}},
    'overs': 20,
    'player_of_match': ['Amanda-Jade Wellington'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Melbourne Stars Women', 'decision': 'field'},
    'venue': 'Karen Rolton Oval, Adelaide',
    'officials': {
        'umpires': ['Dhaval Bhatt', 'Kurt Miegel'],
        'tv_umpires': ['Peter George'],
        'reserve_umpires': ['Ali Cheema'],
        'match_referees': ['Steve Davis'],
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
    raw1 = parse_deliveries(t1)
    for d in raw1:
        if d['bowler'] == 'Gibson':
            d['bowler'] = GIBSON_BOWLING_OVERS[d['over']]
    d1 = normalise_deliveries(raw1)
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
    out = os.path.join(_HERE, 'wbbl_2026_match04_strikers_vs_stars.json')
    build_match_json(out)
