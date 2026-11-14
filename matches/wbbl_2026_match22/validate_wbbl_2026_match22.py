"""
validate_wbbl_2026_match22.py - reconstruct batter and bowler figures from the built JSON
and diff against the official scorecard for WBBL 2026/27 Match 22 (Adelaide Strikers Women vs
Perth Scorchers Women, W.A.C.A, Perth, 2026-11-14).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match22_strikers_vs_scorchers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Adelaide Strikers Women': {
        'Emma de Broughe': (51, 40, 8, 0, 'bowled'),
        'Maia Bouchier': (9, 7, 2, 0, 'caught'),
        'Laura Wolvaardt': (83, 45, 7, 4, 'not out'),
        'Tahlia McGrath': (2, 5, 0, 0, 'bowled'),
        'Madeline Penna': (44, 19, 6, 2, 'caught'),
        'Ellie Johnston': (9, 5, 1, 0, 'not out'),
    },
    'Perth Scorchers Women': {
        'Beth Mooney': (7, 9, 1, 0, 'caught'),
        'Katie Mack': (14, 15, 2, 0, 'bowled'),
        'Sophie Devine': (0, 2, 0, 0, 'caught'),
        'Freya Kemp': (28, 15, 0, 3, 'caught'),
        'Mikayla Hinkley': (41, 30, 5, 0, 'caught'),
        'Chloe Piparo': (10, 11, 1, 0, 'caught'),
        'Alana King': (12, 9, 2, 0, 'bowled'),
        'Chloe Ainsworth': (7, 8, 0, 0, 'caught'),
        'Fatima Sana': (10, 10, 1, 0, 'caught and bowled'),
        'Lilly Mills': (4, 7, 0, 0, 'not out'),
        'Amy Edgar': (3, 4, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
EXPECTED_BOWLING = {
    'Adelaide Strikers Women': {  # bowled by Perth Scorchers Women
        'Chloe Ainsworth': (4.0, 23, 1),
        'Fatima Sana': (3.0, 29, 1),
        'Sophie Devine': (4.0, 34, 1),
        'Alana King': (4.0, 41, 1),
        'Lilly Mills': (3.0, 42, 0),
        'Amy Edgar': (2.0, 32, 0),
    },
    'Perth Scorchers Women': {  # bowled by Adelaide Strikers Women
        'Megan Schutt': (4.0, 32, 1),
        'Ella Wilson': (4.0, 27, 1),
        'Anesu Mushangwe': (4.0, 11, 5),
        'Eleanor Larosa': (2.0, 19, 0),
        'Amanda-Jade Wellington': (4.0, 31, 1),
        'Tahlia McGrath': (2.0, 22, 1),
    },
}

EXPECTED_EXTRAS = {
    'Adelaide Strikers Women': {'byes': 0, 'legbyes': 1, 'noballs': 1, 'wides': 2},
    'Perth Scorchers Women': {'byes': 1, 'legbyes': 8, 'noballs': 0, 'wides': 6},
}

EXPECTED_TOTALS = {'Adelaide Strikers Women': (202, 4), 'Perth Scorchers Women': (151, 9)}


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

        tot = sum(dl['runs']['total'] for o in inn['overs'] for dl in o['deliveries'])
        wk = sum(len(dl.get('wickets', [])) for o in inn['overs'] for dl in o['deliveries'])
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"-- Total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team]}", 'OK' if ok else '*** MISMATCH ***')
        extra_names = (set(balls) - set(EXPECTED_BATTING[team])) | (set(bowler_balls) | set(bowler_runs)) - set(EXPECTED_BOWLING[team])
        if extra_names:
            all_ok = False
            print('  *** Unexpected names (NAME_MAP gap?):', sorted(extra_names))

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
