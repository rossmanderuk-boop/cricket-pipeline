"""
build_match_json_template.py

Template for turning parsed commentary (from parse_cricinfo.py) into a Cricsheet-format
match JSON. Copy this file per match (e.g. matches/matchNN/build_matchNN.py) and fill in the
CONFIG section and the two innings text files - the rest of the logic below is reusable.
"""

import sys, json
sys.path.insert(0, '.')
from parse_cricinfo import parse_deliveries

# =============================================================================
# CONFIG - fill in per match
# =============================================================================

INNINGS1_FILE = 'innings1.txt'   # team batting first
INNINGS2_FILE = 'innings2.txt'   # team batting second

TEAM1_NAME = 'Team A'
TEAM2_NAME = 'Team B'

TEAM1_XI = []  # 11 names, fullest/canonical form you want stored in the JSON
TEAM2_XI = []

NAME_MAP = {
    # 'Munro': 'Colin Munro',
    # 'Colin Munro': 'Colin Munro',   # identity mapping is fine/expected
}

MATCH_INFO = {
    'balls_per_over': 6,
    'city': '',
    'dates': ['YYYY-MM-DD'],
    'event': {'name': '', 'match_number': None},
    'gender': 'male',
    'match_type': 'T20',
    'outcome': {'winner': '', 'by': {'runs': None}},  # or {'wickets': N}; add 'method': 'D/L' if applicable
    'overs': 20,
    'player_of_match': [],
    'season': '',
    'team_type': 'club',
    'toss': {'winner': '', 'decision': ''},
    'venue': '',
}

KNOWN_IDS = {
    # 'Colin Munro': 'af2c687b',
}


# =============================================================================
# Reusable logic - shouldn't need to change per match
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
        print(f"  {inn['team']}: total {total}")

    return match_json


def validate_from_json(json_path, expected_by_team):
    """expected_by_team: {team_name: {player_name: (runs, balls, fours, sixes, status)}}"""
    from collections import defaultdict
    d = json.load(open(json_path))
    all_ok = True
    for inn in d['innings']:
        team = inn['team']
        if team not in expected_by_team:
            continue
        runs = defaultdict(int); balls = defaultdict(int)
        fours = defaultdict(int); sixes = defaultdict(int); outs = {}
        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                ex = deliv.get('extras', {})
                if 'wides' not in ex:
                    balls[b] += 1
                if not ex or 'noballs' in ex:
                    runs[b] += deliv['runs']['batter']
                    if deliv['runs']['batter'] == 4: fours[b] += 1
                    if deliv['runs']['batter'] == 6: sixes[b] += 1
                for w in deliv.get('wickets', []):
                    outs[w['player_out']] = w['kind']
        print(f'--- {team} ---')
        for name, (er, eb, ef, es, estatus) in expected_by_team[team].items():
            ar, ab, af, aS = runs[name], balls[name], fours[name], sixes[name]
            astatus = outs.get(name, 'not out')
            ok = (ar, ab, af, aS) == (er, eb, ef, es) and estatus in astatus
            if not ok:
                all_ok = False
            print(f"  {name}: got {ar}({ab}) 4s{af} 6s{aS} [{astatus}] vs expected "
                  f"{er}({eb}) 4s{ef} 6s{es} [{estatus}]", 'OK' if ok else '*** MISMATCH ***')
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    build_match_json('match_output.json')
