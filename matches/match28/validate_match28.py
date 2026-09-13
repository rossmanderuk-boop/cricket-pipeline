"""
validate_match28.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 28 (St Kitts and Nevis Patriots vs Guyana
Amazon Warriors, Providence Stadium, 2026-09-06).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match28_patriots_vs_amazon.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'St Kitts and Nevis Patriots': {
        'Johnson Charles': (13, 15, 1, 1, 'bowled'),
        'Kyle Mayers': (20, 12, 3, 1, 'bowled'),
        'Andre Fletcher': (4, 5, 1, 0, 'caught'),
        'Alick Athanaze': (52, 39, 2, 4, 'caught'),
        'Jason Holder': (7, 13, 0, 0, 'caught'),
        'Wanindu Hasaranga': (4, 6, 0, 0, 'bowled'),
        'Dasun Shanaka': (20, 20, 1, 1, 'caught'),
        'Navin Bidaisee': (1, 2, 0, 0, 'bowled'),
        'Jeremiah Louis': (0, 1, 0, 0, 'caught and bowled'),
        'Ashmead Nedd': (1, 2, 0, 0, 'bowled'),
        'Naseem Shah': (1, 2, 0, 0, 'not out'),
    },
    'Guyana Amazon Warriors': {
        'Rahmanullah Gurbaz': (39, 25, 5, 2, 'bowled'),
        'Mavendra Dindyal': (17, 16, 2, 0, 'caught and bowled'),
        'Shai Hope': (38, 44, 3, 0, 'not out'),
        'Shimron Hetmyer': (1, 5, 0, 0, 'caught'),
        'Mohammad Nabi': (25, 21, 2, 1, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# keyed under the team that BATTED against them, i.e. the innings the bowler bowled in.
EXPECTED_BOWLING = {
    'St Kitts and Nevis Patriots': {  # bowled by Guyana Amazon Warriors
        'Dwaine Pretorius': (3.0, 28, 1),
        'Khary Pierre': (2.0, 16, 0),
        'Romario Shepherd': (3.0, 16, 3),
        'Shamar Joseph': (3.2, 22, 2),
        'Imran Tahir': (4.0, 26, 0),
        'Mohammad Nabi': (4.0, 17, 4),
    },
    'Guyana Amazon Warriors': {  # bowled by St Kitts and Nevis Patriots
        'Ashmead Nedd': (4.0, 23, 0),
        'Jason Holder': (2.0, 31, 0),
        'Naseem Shah': (3.0, 15, 0),
        'Wanindu Hasaranga': (4.0, 23, 1),
        'Navin Bidaisee': (4.0, 20, 2),
        'Jeremiah Louis': (1.3, 15, 0),
    },
}

EXPECTED_EXTRAS = {
    'St Kitts and Nevis Patriots': {'legbyes': 3, 'noballs': 1, 'wides': 1},
    'Guyana Amazon Warriors': {'byes': 4, 'legbyes': 1, 'wides': 7},
}

EXPECTED_TOTALS = {
    'St Kitts and Nevis Patriots': 128,
    'Guyana Amazon Warriors': 132,
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
        total = 0

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})
                total += deliv['runs']['total']

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
        ok = total == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"  got {total} vs expected {EXPECTED_TOTALS[team]}", 'OK' if ok else '*** MISMATCH ***')
        print()

    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
