"""
validate_wbbl_2026_match20.py - reconstruct batter and bowler figures from the built JSON
and diff against the official scorecard for WBBL 2026/27 Match 20 (Sydney Sixers Women vs
Melbourne Renegades Women, Junction Oval, Melbourne, 2026-11-12).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match20_sixers_vs_renegades.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Sydney Sixers Women': {
        'Ellyse Perry': (30, 41, 2, 0, 'run out'),
        'Sophia Dunkley': (20, 18, 2, 1, 'caught'),
        'Ashleigh Gardner': (22, 21, 2, 0, 'caught'),
        'Melie Kerr': (53, 34, 7, 0, 'caught'),
        'Alice Capsey': (4, 2, 1, 0, 'stumped'),
        'Erin Burns': (1, 2, 0, 0, 'run out'),
        'Eva Ragg': (1, 2, 0, 0, 'not out'),
    },
    'Melbourne Renegades Women': {
        'Olivia Porter': (11, 12, 1, 0, 'run out'),
        'Hayley Matthews': (1, 4, 0, 0, 'caught'),
        'Courtney Webb': (7, 9, 1, 0, 'caught'),
        'Sophie Molineux': (18, 21, 1, 0, 'caught'),
        'Nicole Faltum': (21, 21, 2, 0, 'caught'),
        'Georgia Wareham': (17, 16, 1, 0, 'bowled'),
        'Tess Flintoff': (44, 31, 5, 1, 'bowled'),
        'Chloe Tryon': (0, 2, 0, 0, 'caught'),
        'Deandra Dottin': (4, 2, 1, 0, 'caught'),
        'Milly Illingworth': (1, 1, 0, 0, 'not out'),
        'Tayla Vlaeminck': (1, 1, 0, 0, 'run out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
EXPECTED_BOWLING = {
    'Sydney Sixers Women': {  # bowled by Melbourne Renegades Women
        'Tayla Vlaeminck': (4.0, 26, 0),
        'Sophie Molineux': (4.0, 31, 0),
        'Milly Illingworth': (3.0, 24, 2),
        'Georgia Wareham': (4.0, 21, 1),
        'Tess Flintoff': (1.0, 13, 0),
        'Hayley Matthews': (3.0, 19, 1),
        'Chloe Tryon': (1.0, 4, 0),
    },
    'Melbourne Renegades Women': {  # bowled by Sydney Sixers Women
        'Caoimhe Bray': (3.0, 17, 1),
        'Lauren Cheatle': (4.0, 20, 2),
        'Melie Kerr': (4.0, 29, 1),
        'Ashleigh Gardner': (3.0, 13, 3),
        'Frankie Nicklin': (3.0, 30, 0),
        'Sarah Coyte': (3.0, 19, 1),
    },
}

EXPECTED_EXTRAS = {
    'Sydney Sixers Women': {'byes': 0, 'legbyes': 2, 'noballs': 0, 'wides': 7},
    'Melbourne Renegades Women': {'byes': 1, 'legbyes': 0, 'noballs': 0, 'wides': 3},
}

EXPECTED_TOTALS = {'Sydney Sixers Women': (140, 6), 'Melbourne Renegades Women': (129, 10)}


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
