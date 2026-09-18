"""
validate_match35.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Qualifier 1 (Guyana Amazon Warriors vs
Antigua and Barbuda Falcons, Kensington Oval, Bridgetown, 2026-09-17).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match35_amazon_vs_falcons.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Guyana Amazon Warriors': {
        'Glenn Phillips': (16, 15, 2, 0, 'caught'),
        'Mavendra Dindyal': (11, 18, 1, 0, 'caught'),
        'Shai Hope': (16, 15, 1, 0, 'lbw'),
        'Mohammad Haris': (1, 3, 0, 0, 'caught'),
        'Shimron Hetmyer': (2, 4, 0, 0, 'caught'),
        'Mehidy Hasan Miraz': (0, 1, 0, 0, 'lbw'),
        'Quentin Sampson': (0, 1, 0, 0, 'bowled'),
        'Khary Pierre': (1, 2, 0, 0, 'bowled'),
        'Imran Tahir': (1, 3, 0, 0, 'bowled'),
        'Romario Shepherd': (14, 13, 1, 1, 'not out'),
        'Shamar Joseph': (7, 15, 1, 0, 'caught'),
    },
    'Antigua and Barbuda Falcons': {
        'Rahkeem Cornwall': (49, 16, 3, 6, 'caught'),
        'Evin Lewis': (23, 13, 2, 2, 'not out'),
        'Amir Jangoo': (4, 4, 1, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures keyed under the team that BATTED against them, i.e. the innings the
# bowler bowled in)
EXPECTED_BOWLING = {
    'Guyana Amazon Warriors': {  # bowled by Antigua and Barbuda Falcons
        'Fabian Allen': (2.0, 14, 0),
        'Alzarri Joseph': (3.0, 19, 0),
        'Joshua James': (1.0, 1, 1),
        'Shadab Khan': (4.0, 16, 4),
        'Sufyan Moqim': (4.0, 13, 4),
        'Shamar Springer': (1.0, 8, 1),
    },
    'Antigua and Barbuda Falcons': {  # bowled by Guyana Amazon Warriors
        'Imran Tahir': (2.0, 20, 1),
        'Mehidy Hasan Miraz': (1.2, 10, 0),
        'Khary Pierre': (1.0, 26, 0),
        'Shamar Joseph': (1.0, 21, 0),
    },
}

EXPECTED_EXTRAS = {
    'Guyana Amazon Warriors': {'byes': 5, 'wides': 2},
    'Antigua and Barbuda Falcons': {'noballs': 1},
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
