"""
validate_match33.py - reconstructs batter and bowler figures from cpl_2026_match33_tkr_vs_amazon.json
and diffs them against the official scorecard.
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match33_tkr_vs_amazon.json')

# expected batter figures: (runs, balls, fours, sixes, status_substr)
EXPECTED_BATTERS = {
    'Trinbago Knight Riders': {
        'Colin Munro': (26, 16, 4, 1, 'bowled'),
        'Alex Hales': (22, 26, 3, 0, 'caught'),
        'Nicholas Pooran': (0, 1, 0, 0, 'bowled'),
        'Justin Greaves': (35, 37, 1, 1, 'bowled'),
        'Jyd Goolie': (4, 10, 0, 0, 'bowled'),
        'Sunil Narine': (7, 5, 1, 0, 'bowled'),
        'Kieron Pollard': (10, 11, 1, 0, 'caught'),
        'Joshua Da Silva': (4, 5, 0, 0, 'caught'),
        'Akeal Hosein': (12, 9, 2, 0, 'not out'),
        'Lahiru Kumara': (1, 1, 0, 0, 'not out'),
    },
    'Guyana Amazon Warriors': {
        'Glenn Phillips': (11, 18, 1, 0, 'bowled'),
        'Mavendra Dindyal': (19, 14, 1, 2, 'lbw'),
        'Shai Hope': (42, 35, 1, 2, 'not out'),
        'Shimron Hetmyer': (28, 19, 0, 3, 'caught'),
        'Mehidy Hasan Miraz': (2, 14, 0, 0, 'caught'),
        'Quentin Sampson': (12, 12, 2, 0, 'not out'),
    },
}

# expected bowler figures keyed under the team they bowled AGAINST (the batting team),
# as (overs, maidens, runs, wickets)
EXPECTED_BOWLERS = {
    'Trinbago Knight Riders': {  # bowled by GAW
        'Dwaine Pretorius': (3.0, 0, 24, 1),
        'Shamar Joseph': (4.0, 0, 27, 2),
        'Veerasammy Permaul': (4.0, 0, 19, 0),
        'Mehidy Hasan Miraz': (4.0, 0, 23, 4),
        'Imran Tahir': (4.0, 0, 21, 1),
        'Romario Shepherd': (1.0, 0, 10, 0),
    },
    'Guyana Amazon Warriors': {  # bowled by TKR
        'Sunil Narine': (4.0, 1, 13, 1),
        'Akeal Hosein': (4.0, 0, 31, 1),
        'Usman Tariq': (4.0, 0, 19, 1),
        'Jyd Goolie': (1.0, 0, 10, 0),
        'Lahiru Kumara': (4.0, 0, 30, 1),
        'Justin Greaves': (1.4, 0, 21, 0),
    },
}

# expected extras per innings: (byes, legbyes, wides, noballs)
EXPECTED_EXTRAS = {
    'Trinbago Knight Riders': {'byes': 0, 'legbyes': 2, 'wides': 2, 'noballs': 1},
    'Guyana Amazon Warriors': {'byes': 1, 'legbyes': 2, 'wides': 10, 'noballs': 0},
}


def overs_to_balls(overs_float):
    o = int(overs_float)
    b = round((overs_float - o) * 10)
    return o * 6 + b


def main():
    d = json.load(open(JSON_PATH))
    all_ok = True

    for inn in d['innings']:
        team = inn['team']
        print(f'=== {team} — batters ===')
        runs = defaultdict(int); balls = defaultdict(int)
        fours = defaultdict(int); sixes = defaultdict(int); outs = {}
        bowl_balls = defaultdict(int); bowl_runs = defaultdict(int)
        bowl_wkts = defaultdict(int)
        extras_tally = defaultdict(int)

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bowler = deliv['bowler']
                ex = deliv.get('extras', {})
                is_wide = 'wides' in ex
                is_nb = 'noballs' in ex

                if not is_wide:
                    balls[b] += 1
                if not is_wide and not is_nb:
                    bowl_balls[bowler] += 1
                if not ex or is_nb:
                    runs[b] += deliv['runs']['batter']
                    if deliv['runs']['batter'] == 4: fours[b] += 1
                    if deliv['runs']['batter'] == 6: sixes[b] += 1

                # byes/leg-byes are not charged to the bowler; wides/no-balls and
                # runs off the bat are.
                if 'byes' in ex or 'legbyes' in ex:
                    bowl_runs[bowler] += 0
                else:
                    bowl_runs[bowler] += deliv['runs']['total']
                for k, v in ex.items():
                    extras_tally[k] += v

                for w in deliv.get('wickets', []):
                    outs[w['player_out']] = w['kind']
                    if w['kind'] not in ('run out', 'retired out'):
                        bowl_wkts[bowler] += 1

        for name, (er, eb, ef, es, estatus) in EXPECTED_BATTERS.get(team, {}).items():
            ar, ab, af, aS = runs[name], balls[name], fours[name], sixes[name]
            astatus = outs.get(name, 'not out')
            ok = (ar, ab, af, aS) == (er, eb, ef, es) and estatus in astatus
            if not ok:
                all_ok = False
            print(f"  {name}: got {ar}({ab}) 4s{af} 6s{aS} [{astatus}] vs expected "
                  f"{er}({eb}) 4s{ef} 6s{es} [{estatus}]", 'OK' if ok else '*** MISMATCH ***')

        print(f'--- {team} — extras ---')
        exp_ex = EXPECTED_EXTRAS[team]
        for k in ('byes', 'legbyes', 'wides', 'noballs'):
            a = extras_tally.get(k, 0)
            e = exp_ex[k]
            ok = a == e
            if not ok:
                all_ok = False
            print(f'  {k}: got {a} vs expected {e}', 'OK' if ok else '*** MISMATCH ***')

        print(f'--- bowlers (bowled against {team}) ---')
        for name, (eov, emaid, erun, ewkt) in EXPECTED_BOWLERS.get(team, {}).items():
            aov_balls = bowl_balls[name]
            eov_balls = overs_to_balls(eov)
            arun, awkt = bowl_runs[name], bowl_wkts[name]
            ok = aov_balls == eov_balls and arun == erun and awkt == ewkt
            if not ok:
                all_ok = False
            print(f"  {name}: got {aov_balls}b {arun}r {awkt}w vs expected {eov_balls}b(="
                  f"{eov}ov) {erun}r {ewkt}w", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
