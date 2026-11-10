"""
validate_wbbl_match17.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for WBBL 2026/27 17th Match (Hobart Hurricanes Women vs
Adelaide Strikers Women, Bellerive Oval, Hobart, 2026-11-10).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match17_hurricanes_vs_strikers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Hobart Hurricanes Women': {
        'Lizelle Lee': (19, 18, 4, 0, 'lbw'),
        'Chamari Athapaththu': (10, 26, 0, 0, 'retired out'),
        'Rachel Trenaman': (9, 5, 2, 0, 'caught and bowled'),
        'Nicola Carey': (66, 53, 9, 0, 'not out'),
        'Heather Graham': (14, 13, 1, 0, 'run out'),
        'Chinelle Henry': (6, 5, 0, 0, 'run out'),
    },
    'Adelaide Strikers Women': {
        'Emma de Broughe': (41, 37, 4, 0, 'caught'),
        'Maia Bouchier': (26, 19, 5, 0, 'caught'),
        'Laura Wolvaardt': (27, 27, 2, 0, 'caught'),
        'Tahlia McGrath': (14, 14, 2, 0, 'caught'),
        'Madeline Penna': (14, 13, 2, 0, 'caught'),
        'Ellie Johnston': (3, 5, 0, 0, 'caught'),
        'Amanda-Jade Wellington': (1, 2, 0, 0, 'not out'),
        'Sophie Ecclestone': (9, 3, 2, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Hobart Hurricanes Women': {  # bowled by Adelaide Strikers Women
        'Eleanor Larosa': (2.0, 13, 0),
        'Ella Wilson': (4.0, 12, 0),
        'Megan Schutt': (4.0, 24, 0),
        'Sophie Ecclestone': (4.0, 37, 1),
        'Madeline Penna': (1.0, 14, 1),
        'Tahlia McGrath': (3.0, 23, 0),
        'Amanda-Jade Wellington': (2.0, 10, 0),
    },
    'Adelaide Strikers Women': {  # bowled by Hobart Hurricanes Women
        'Molly Strano': (4.0, 30, 2),
        'Nicola Carey': (4.0, 30, 1),
        'Chinelle Henry': (1.0, 12, 0),
        'Heather Graham': (4.0, 20, 0),
        'Isabella Malgioglio': (3.0, 25, 1),
        'Lauren Smith': (2.0, 6, 2),
        'Hayley Silver-Holmes': (2.0, 15, 0),
    },
}

EXPECTED_EXTRAS = {
    'Hobart Hurricanes Women': {'byes': 2, 'legbyes': 3, 'wides': 9, 'noballs': 0},
    'Adelaide Strikers Women': {'byes': 0, 'legbyes': 1, 'wides': 3, 'noballs': 0},
}

EXPECTED_TOTALS = {
    'Hobart Hurricanes Women': (138, 5),
    'Adelaide Strikers Women': (139, 6),
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

        tot = sum(dv['runs']['total'] for o in inn['overs'] for dv in o['deliveries'])
        wk = sum(len(dv.get('wickets', [])) for o in inn['overs'] for dv in o['deliveries'])
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"-- Total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team][0]}/{EXPECTED_TOTALS[team][1]}", 'OK' if ok else '*** MISMATCH ***')

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
