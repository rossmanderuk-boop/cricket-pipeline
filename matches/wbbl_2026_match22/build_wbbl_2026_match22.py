"""
build_wbbl_2026_match22.py - WBBL 2026/27, 22nd Match (D/N), Adelaide Strikers Women vs Perth
Scorchers Women, W.A.C.A, Perth, 2026-11-14.
"""

import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG
# =============================================================================

_HERE = os.path.dirname(__file__)
INNINGS1_FILE = os.path.join(_HERE, 'innings1.txt')   # Adelaide Strikers Women (batted first)
INNINGS2_FILE = os.path.join(_HERE, 'innings2.txt')   # Perth Scorchers Women (chased)

TEAM1_NAME = 'Adelaide Strikers Women'
TEAM2_NAME = 'Perth Scorchers Women'

# XIs in scorecard batting order (build_innings uses this to place not-yet-faced partners).
TEAM1_XI = [
    'Emma de Broughe', 'Maia Bouchier', 'Laura Wolvaardt', 'Tahlia McGrath', 'Madeline Penna',
    'Ellie Johnston', 'Amanda-Jade Wellington', 'Eleanor Larosa', 'Ella Wilson', 'Megan Schutt',
    'Anesu Mushangwe',
]
TEAM2_XI = [
    'Beth Mooney', 'Katie Mack', 'Sophie Devine', 'Freya Kemp', 'Mikayla Hinkley',
    'Chloe Piparo', 'Alana King', 'Chloe Ainsworth', 'Fatima Sana', 'Lilly Mills', 'Amy Edgar',
]

NAME_MAP = {
    # Adelaide Strikers Women
    'de Broughe': 'Emma de Broughe', 'Emma de Broughe': 'Emma de Broughe',
    'Bouchier': 'Maia Bouchier', 'Maia Bouchier': 'Maia Bouchier',
    'Wolvaardt': 'Laura Wolvaardt', 'Laura Wolvaardt': 'Laura Wolvaardt',
    'McGrath': 'Tahlia McGrath', 'Tahlia McGrath': 'Tahlia McGrath',
    'Penna': 'Madeline Penna', 'Madeline Penna': 'Madeline Penna',
    'Johnston': 'Ellie Johnston', 'Ellie Johnston': 'Ellie Johnston',
    'Wellington': 'Amanda-Jade Wellington', 'Amanda-Jade Wellington': 'Amanda-Jade Wellington',
    'Larosa': 'Eleanor Larosa', 'Eleanor Larosa': 'Eleanor Larosa',
    'Wilson': 'Ella Wilson', 'Ella Wilson': 'Ella Wilson',
    'Schutt': 'Megan Schutt', 'Megan Schutt': 'Megan Schutt',
    'Mushangwe': 'Anesu Mushangwe', 'Anesu Mushangwe': 'Anesu Mushangwe',
    # Perth Scorchers Women
    'Mooney': 'Beth Mooney', 'Beth Mooney': 'Beth Mooney',
    'Mack': 'Katie Mack', 'Katie Mack': 'Katie Mack',
    'Devine': 'Sophie Devine', 'Sophie Devine': 'Sophie Devine',
    'Kemp': 'Freya Kemp', 'Freya Kemp': 'Freya Kemp',
    'Hinkley': 'Mikayla Hinkley', 'Mikayla Hinkley': 'Mikayla Hinkley',
    'Piparo': 'Chloe Piparo', 'Chloe Piparo': 'Chloe Piparo',
    'King': 'Alana King', 'Alana King': 'Alana King',
    'Ainsworth': 'Chloe Ainsworth', 'Chloe Ainsworth': 'Chloe Ainsworth',
    'Fatima Sana': 'Fatima Sana',
    'Mills': 'Lilly Mills', 'Lilly Mills': 'Lilly Mills',
    'Edgar': 'Amy Edgar', 'Amy Edgar': 'Amy Edgar',
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': 'Perth',
    'dates': ['2026-11-14'],
    'event': {'name': "Women's Big Bash League", 'match_number': 22},
    'gender': 'female',
    'match_type': 'T20',
    'outcome': {'winner': 'Adelaide Strikers Women', 'by': {'runs': 51}},
    'overs': 20,
    'player_of_match': ['Anesu Mushangwe'],
    'season': '2026/27',
    'team_type': 'club',
    'toss': {'winner': 'Adelaide Strikers Women', 'decision': 'bat'},
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


def build_innings(deliveries, team_name, batting_order=()):
    """batting_order: the team's XI in scorecard batting order (used to place a
    non-striker who hasn't faced yet)."""
    pair = []
    over_list = []
    over_cursor = -1
    cur = None

    dismissed = set()
    seen = set()
    inferred = set()
    for idx, d in enumerate(deliveries):
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
                # Replace a partner we only inferred (hasn't faced yet) before a real one.
                slot = next((i for i, p in enumerate(pair) if p in inferred), len(pair) - 1)
                pair[slot] = batter
        inferred.discard(batter)
        seen.add(batter)
        non_striker = next((p for p in pair if p != batter), None)
        if non_striker is None:
            # Partner hasn't faced yet (an opener, or a new batter after a wicket): it is the
            # next player in the batting order who hasn't batted yet. Without a batting order,
            # fall back to the next not-yet-dismissed batter to appear in the commentary.
            non_striker = next((n for n in batting_order if n not in seen), None) or \
                next((n['batter'] for n in deliveries[idx + 1:]
                      if n['batter'] != batter and n['batter'] not in dismissed), None)
            if non_striker is None:
                non_striker = batter
            else:
                pair.append(non_striker)
                inferred.add(non_striker)
                seen.add(non_striker)

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
            dismissed.add(w['player_out'])
            inferred.discard(w['player_out'])
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

    innings1 = build_innings(d1, TEAM1_NAME, TEAM1_XI)
    innings2 = build_innings(d2, TEAM2_NAME, TEAM2_XI)

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
    out = os.path.join(_HERE, 'wbbl_2026_match22_strikers_vs_scorchers.json')
    build_match_json(out)
