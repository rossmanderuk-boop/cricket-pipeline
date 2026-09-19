"""
validate_match35.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Qualifier 2 (Guyana Amazon Warriors vs Jamaica
Kingsmen, Kensington Oval, Bridgetown, 2026-09-18).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match35_amazon_vs_kingsmen.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Guyana Amazon Warriors': {
        'Mohammad Haris': (9, 8, 1, 0, 'run out'),
        'Mavendra Dindyal': (9, 12, 2, 0, 'caught'),
        'Shai Hope': (40, 33, 2, 2, 'caught'),
        'Shimron Hetmyer': (102, 45, 4, 8, 'not out'),
        'Quentin Sampson': (29, 17, 1, 2, 'caught'),
        'Romario Shepherd': (10, 7, 1, 0, 'not out'),
    },
    'Jamaica Kingsmen': {
        'Maaz Sadaqat': (41, 17, 5, 3, 'caught'),
        'Kirk McKenzie': (34, 20, 5, 1, 'caught'),
        'Keacy Carty': (56, 40, 5, 3, 'run out'),
        'Saim Ayub': (23, 17, 1, 2, 'caught'),
        'Rovman Powell': (40, 17, 2, 4, 'not out'),
        'Andre Russell': (2, 5, 0, 0, 'caught'),
        'Hassan Khan': (4, 2, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures keyed under the team that BATTED against them, i.e. the innings the
# bowler bowled in)
EXPECTED_BOWLING = {
    'Guyana Amazon Warriors': {  # bowled by Jamaica Kingsmen
        'Hassan Khan': (4.0, 25, 1),
        'Andre Russell': (3.5, 36, 1),
        'Rovman Powell': (0.1, 0, 0),
        'Hunain Shah': (4.0, 38, 1),
        'Saim Ayub': (3.0, 34, 0),
        'Keemo Paul': (3.0, 38, 0),
        'Vitel Lawes': (2.0, 35, 0),
    },
    'Jamaica Kingsmen': {  # bowled by Guyana Amazon Warriors
        'Dwaine Pretorius': (4.0, 37, 2),
        'Mehidy Hasan Miraz': (4.0, 43, 0),
        'Romario Shepherd': (2.4, 28, 1),
        'Khary Pierre': (3.0, 34, 0),
        'Imran Tahir': (4.0, 34, 1),
        'Shamar Joseph': (2.0, 30, 0),
    },
}

EXPECTED_EXTRAS = {
    'Guyana Amazon Warriors': {'noballs': 2, 'wides': 5},
    'Jamaica Kingsmen': {'legbyes': 1, 'wides': 6},
}


def overs_to_balls(overs_str):
    o, _, b = str(overs_str).partition('.')
    return int(o) * 6 + (int(b) if b else 0)


def main():
    d = json.load(open(JSON_PATH))
    all_ok = True

    for inn in d['innings']:
        team = inn['team']
        print(f'=== {team} (batting) ===')

        runs = defaultdict(int); balls = defaultdict(int)
        fours = defaultdict(int); sixes = defaultdict(int); outs = {}
        bowler_balls = defaultdict(int); bowler_runs = defaultdict(int); bowler_wkts = defaultdict(int)
        extras_total = defaultdict(int)

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})

                for k, v in ex.items():
                    extras_total[k] += v

                legal_ball = 'wides' not in ex and 'noballs' not in ex
                if 'wides' not in ex:
                    balls[b] += 1
                if legal_ball:
                    bowler_balls[bwl] += 1
                bowler_runs[bwl] += deliv['runs']['total'] - ex.get('byes', 0) - ex.get('legbyes', 0)

                if not ex or 'noballs' in ex:
                    runs[b] += deliv['runs']['batter']
                    if deliv['runs']['batter'] == 4: fours[b] += 1
                    if deliv['runs']['batter'] == 6: sixes[b] += 1

                for w in deliv.get('wickets', []):
                    outs[w['player_out']] = w['kind']
                    if w['kind'] not in ('run out', 'retired out'):
                        bowler_wkts[bwl] += 1

        print('-- Batting --')
        for name, (er, eb, ef, es, estatus) in EXPECTED_BATTING[team].items():
            ar, ab, af, aS = runs[name], balls[name], fours[name], sixes[name]
            astatus = outs.get(name, 'not out')
            ok = (ar, ab, af, aS) == (er, eb, ef, es) and estatus in astatus
            all_ok &= ok
            print(f"  {name}: got {ar}({ab}) 4s{af} 6s{aS} [{astatus}] vs expected "
                  f"{er}({eb}) 4s{ef} 6s{es} [{estatus}]", 'OK' if ok else '*** MISMATCH ***')

        print('-- Bowling --')
        for name, (eo, er, ew) in EXPECTED_BOWLING[team].items():
            got_overs = f"{bowler_balls[name] // 6}.{bowler_balls[name] % 6}"
            ok = bowler_balls[name] == overs_to_balls(eo) and bowler_runs[name] == er and bowler_wkts[name] == ew
            all_ok &= ok
            print(f"  {name}: got {got_overs}-{bowler_runs[name]}-{bowler_wkts[name]} vs expected "
                  f"{eo}-{er}-{ew}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Extras --')
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
