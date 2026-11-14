"""
validate_wbbl_2026_match21.py - reconstruct batter and bowler figures from the built JSON
and diff against the official scorecard for WBBL 2026/27 Match 21 (Hobart Hurricanes Women vs
Brisbane Heat Women, Bellerive Oval, Hobart, 2026-11-14).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match21_hurricanes_vs_heat.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Hobart Hurricanes Women': {
        'Lizelle Lee': (3, 6, 0, 0, 'caught'),
        'Rachel Trenaman': (1, 8, 0, 0, 'caught'),
        'Nicola Carey': (4, 5, 0, 0, 'bowled'),
        'Maddy Green': (11, 13, 1, 0, 'bowled'),
        'Heather Graham': (13, 17, 1, 0, 'caught'),
        'Chinelle Henry': (1, 2, 0, 0, 'bowled'),
        'Molly Strano': (10, 19, 1, 0, 'caught'),
        'Hayley Silver-Holmes': (9, 12, 0, 0, 'caught'),
        'Lauren Smith': (20, 20, 3, 0, 'bowled'),
        'Isabella Malgioglio': (3, 4, 0, 0, 'bowled'),
        'Linsey Smith': (2, 2, 0, 0, 'not out'),
    },
    'Brisbane Heat Women': {
        'Grace Harris': (52, 22, 8, 2, 'not out'),
        'Charli Knott': (34, 12, 4, 2, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
EXPECTED_BOWLING = {
    'Hobart Hurricanes Women': {  # bowled by Brisbane Heat Women
        'Charli Knott': (3.5, 16, 1),
        'Lily Bassingthwaighte': (4.0, 25, 3),
        'Lucy Hamilton': (3.0, 15, 2),
        'Sarah Glenn': (4.0, 16, 2),
        'Orla Prendergast': (1.0, 5, 0),
        'Sianna Ginger': (2.0, 8, 2),
    },
    'Brisbane Heat Women': {  # bowled by Hobart Hurricanes Women
        'Linsey Smith': (1.0, 17, 0),
        'Nicola Carey': (1.0, 18, 0),
        'Chinelle Henry': (1.0, 20, 0),
        'Heather Graham': (1.0, 7, 0),
        'Isabella Malgioglio': (1.0, 13, 0),
        'Hayley Silver-Holmes': (0.4, 13, 0),
    },
}

EXPECTED_EXTRAS = {
    'Hobart Hurricanes Women': {'byes': 0, 'legbyes': 1, 'noballs': 1, 'wides': 7},
    'Brisbane Heat Women': {'byes': 0, 'legbyes': 0, 'noballs': 0, 'wides': 2},
}

EXPECTED_TOTALS = {'Hobart Hurricanes Women': (86, 10), 'Brisbane Heat Women': (88, 0)}


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
