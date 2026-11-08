"""
validate_match30.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 30 (Antigua and Barbuda Falcons vs Guyana
Amazon Warriors, Providence Stadium, 2026-09-08).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match30_falcons_vs_amazon.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Antigua and Barbuda Falcons': {
        'Karima Gore': (23, 18, 3, 1, 'caught'),
        'Evin Lewis': (22, 18, 1, 2, 'lbw'),
        'Amir Jangoo': (27, 30, 0, 1, 'caught'),
        'Hasan Nawaz': (36, 27, 3, 2, 'caught'),
        'Moeen Ali': (18, 12, 0, 2, 'caught'),
        'Shadab Khan': (30, 9, 2, 3, 'not out'),
        'Fabian Allen': (11, 7, 0, 1, 'not out'),
    },
    'Guyana Amazon Warriors': {
        'Rahmanullah Gurbaz': (18, 8, 0, 3, 'bowled'),
        'Mavendra Dindyal': (25, 13, 2, 2, 'caught'),
        'Shai Hope': (0, 3, 0, 0, 'caught'),
        'Shimron Hetmyer': (4, 7, 0, 0, 'caught'),
        'Mohammad Nabi': (23, 22, 2, 0, 'lbw'),
        'Quentin Sampson': (12, 7, 1, 1, 'bowled'),
        'Romario Shepherd': (6, 3, 0, 1, 'caught'),
        'Dwaine Pretorius': (1, 3, 0, 0, 'bowled'),
        'Shamar Joseph': (5, 6, 1, 0, 'bowled'),
        'Imran Tahir': (8, 14, 1, 0, 'bowled'),
        'Khary Pierre': (0, 1, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures are keyed under the team that BATTED against them, i.e. the innings
# the bowler bowled in, per the toolkit's known pitfall about this)
EXPECTED_BOWLING = {
    'Antigua and Barbuda Falcons': {  # bowled by Guyana Amazon Warriors
        'Dwaine Pretorius': (2.0, 16, 0),
        'Romario Shepherd': (3.0, 51, 1),
        'Khary Pierre': (3.0, 27, 1),
        'Mohammad Nabi': (4.0, 23, 1),
        'Imran Tahir': (4.0, 21, 1),
        'Shamar Joseph': (4.0, 39, 1),
    },
    'Guyana Amazon Warriors': {  # bowled by Antigua and Barbuda Falcons
        'Alzarri Joseph': (4.0, 41, 4),
        'Jayden Seales': (2.0, 21, 0),
        'Joshua James': (1.2, 11, 2),
        'Shadab Khan': (4.0, 19, 2),
        'Sufyan Moqim': (3.0, 18, 2),
    },
}

EXPECTED_EXTRAS = {
    'Antigua and Barbuda Falcons': {'legbyes': 5, 'noballs': 1, 'wides': 9},
    'Guyana Amazon Warriors': {'byes': 4, 'legbyes': 3, 'noballs': 1, 'wides': 7},
}

EXPECTED_TOTAL = {
    'Antigua and Barbuda Falcons': 182,
    'Guyana Amazon Warriors': 117,
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
        grand_total = 0

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})

                grand_total += deliv['runs']['total']

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

        print('-- Total --')
        ok = grand_total == EXPECTED_TOTAL[team]
        all_ok &= ok
        print(f"  total: got {grand_total} vs expected {EXPECTED_TOTAL[team]}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
