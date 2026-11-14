"""
validate_wbbl_2026_match19.py - reconstruct batter and bowler figures from the built JSON
and diff against the official scorecard for WBBL 2026/27 Match 19 (Melbourne Stars Women vs
Brisbane Heat Women, Junction Oval, Melbourne, 2026-11-12).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match19_stars_vs_heat.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Melbourne Stars Women': {
        'Meg Lanning': (52, 45, 7, 0, 'caught'),
        'Amy Jones': (74, 52, 10, 0, 'stumped'),
        'Annabel Sutherland': (2, 4, 0, 0, 'caught'),
        'Dani Gibson': (7, 9, 0, 0, 'bowled'),
        'Georgia Prestwidge': (20, 8, 2, 1, 'bowled'),
        'Charlie Dean': (3, 2, 0, 0, 'not out'),
        'Naomi Stalenberg': (1, 1, 0, 0, 'not out'),
    },
    'Brisbane Heat Women': {
        'Charli Knott': (30, 24, 6, 0, 'bowled'),
        'Grace Harris': (2, 3, 0, 0, 'caught'),
        'Georgia Redmayne': (74, 50, 12, 0, 'not out'),
        'Orla Prendergast': (52, 36, 6, 1, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
EXPECTED_BOWLING = {
    'Melbourne Stars Women': {  # bowled by Brisbane Heat Women
        'Lucy Hamilton': (4.0, 34, 1),
        'Lily Bassingthwaighte': (2.0, 20, 0),
        'Orla Prendergast': (4.0, 36, 1),
        'Sarah Glenn': (4.0, 21, 1),
        'Sianna Ginger': (3.0, 22, 2),
        'Charli Knott': (3.0, 31, 0),
    },
    'Brisbane Heat Women': {  # bowled by Melbourne Stars Women
        'Sophie Day': (4.0, 26, 0),
        'Kim Garth': (3.5, 40, 1),
        'Annabel Sutherland': (4.0, 32, 1),
        'Charlie Dean': (4.0, 36, 0),
        'Maisy Gibson': (1.0, 17, 0),
        'Dani Gibson': (2.0, 13, 0),
    },
}

EXPECTED_EXTRAS = {
    'Melbourne Stars Women': {'byes': 0, 'legbyes': 1, 'noballs': 1, 'wides': 4},
    'Brisbane Heat Women': {'byes': 1, 'legbyes': 1, 'noballs': 0, 'wides': 6},
}

EXPECTED_TOTALS = {'Melbourne Stars Women': (165, 5), 'Brisbane Heat Women': (166, 2)}


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
