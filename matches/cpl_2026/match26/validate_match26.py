"""
validate_match26.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 26 (Jamaica Kingsmen vs Guyana Amazon
Warriors, Providence Stadium, 2026-09-04).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match26_kingsmen_vs_amazon.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Jamaica Kingsmen': {
        'Maaz Sadaqat': (35, 34, 1, 1, 'caught'),
        'Kirk McKenzie': (1, 3, 0, 0, 'lbw'),
        'Keacy Carty': (18, 12, 0, 2, 'lbw'),
        'Usman Khan': (10, 12, 1, 0, 'bowled'),
        'Keemo Paul': (15, 15, 1, 0, 'run out'),
        'Rovman Powell': (0, 1, 0, 0, 'bowled'),
        'Hassan Khan': (62, 29, 2, 6, 'not out'),
        'Odean Smith': (13, 14, 1, 0, 'run out'),
        'Vitel Lawes': (0, 0, 0, 0, 'not out'),
    },
    'Guyana Amazon Warriors': {
        'Rahmanullah Gurbaz': (54, 35, 5, 3, 'caught'),
        'Mavendra Dindyal': (33, 17, 1, 4, 'bowled'),
        'Shai Hope': (39, 35, 2, 1, 'not out'),
        'Shimron Hetmyer': (30, 17, 2, 1, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures are keyed under the team that BATTED against them, i.e. the innings
# the bowler bowled in, per the toolkit's known pitfall about this)
EXPECTED_BOWLING = {
    'Jamaica Kingsmen': {  # bowled by Guyana Amazon Warriors
        'Dwaine Pretorius': (3.0, 20, 2),
        'Mohammad Nabi': (4.0, 25, 1),
        'Shamar Joseph': (4.0, 43, 0),
        'Romario Shepherd': (1.0, 10, 0),
        'Imran Tahir': (4.0, 38, 0),
        'Khary Pierre': (4.0, 21, 2),
    },
    'Guyana Amazon Warriors': {  # bowled by Jamaica Kingsmen
        'Hassan Khan': (4.0, 20, 0),
        'Jediah Blades': (3.2, 31, 0),
        'Keemo Paul': (3.0, 34, 0),
        'Hunain Shah': (3.0, 31, 1),
        'Vitel Lawes': (3.0, 36, 0),
        'Maaz Sadaqat': (1.0, 6, 1),
    },
}

EXPECTED_EXTRAS = {
    'Jamaica Kingsmen': {'legbyes': 2, 'wides': 3},
    'Guyana Amazon Warriors': {'legbyes': 2, 'wides': 2},
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
