"""
validate_match09.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for WBBL 2026/27 Match 9 (Hobart Hurricanes Women vs
Melbourne Renegades Women, Bellerive Oval, Hobart, 2026-11-04).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match09_hurricanes_vs_renegades.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Hobart Hurricanes Women': {
        'Lizelle Lee': (6, 6, 1, 0, 'lbw'),
        'Chamari Athapaththu': (9, 18, 1, 0, 'caught'),
        'Rachel Trenaman': (0, 2, 0, 0, 'bowled'),
        'Nicola Carey': (62, 43, 10, 0, 'bowled'),
        'Heather Graham': (9, 13, 1, 0, 'caught'),
        'Maddy Green': (17, 16, 1, 0, 'lbw'),
        'Chinelle Henry': (36, 18, 7, 0, 'run out'),
        'Hayley Silver-Holmes': (2, 4, 0, 0, 'not out'),
        'Lauren Smith': (4, 1, 1, 0, 'not out'),
    },
    'Melbourne Renegades Women': {
        'Olivia Porter': (14, 11, 3, 0, 'bowled'),
        'Hayley Matthews': (59, 44, 8, 0, 'bowled'),
        'Courtney Webb': (29, 25, 3, 0, 'bowled'),
        'Sophie Molineux': (6, 4, 1, 0, 'caught and bowled'),
        'Georgia Wareham': (17, 11, 3, 0, 'bowled'),
        'Nicole Faltum': (9, 11, 0, 0, 'not out'),
        'Chloe Tryon': (4, 3, 1, 0, 'bowled'),
        'Deandra Dottin': (15, 11, 2, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Hobart Hurricanes Women': {  # bowled by Melbourne Renegades Women
        'Tayla Vlaeminck': (3.0, 27, 0),
        'Sophie Molineux': (4.0, 22, 4),
        'Hayley Matthews': (4.0, 39, 1),
        'Milly Illingworth': (3.0, 22, 0),
        'Georgia Wareham': (4.0, 23, 1),
        'Chloe Tryon': (2.0, 18, 0),
    },
    'Melbourne Renegades Women': {  # bowled by Hobart Hurricanes Women
        'Molly Strano': (4.0, 22, 1),
        'Nicola Carey': (3.5, 30, 2),
        'Chinelle Henry': (1.0, 14, 0),
        'Heather Graham': (4.0, 24, 3),
        'Isabella Malgioglio': (3.0, 25, 0),
        'Lauren Smith': (2.0, 19, 0),
        'Hayley Silver-Holmes': (1.0, 9, 0),
        'Chamari Athapaththu': (1.0, 12, 0),
    },
}

EXPECTED_EXTRAS = {
    'Hobart Hurricanes Women': {'legbyes': 3, 'noballs': 1, 'wides': 5},
    'Melbourne Renegades Women': {'noballs': 1, 'wides': 1},
}

EXPECTED_TOTALS = {
    'Hobart Hurricanes Women': (154, 7),
    'Melbourne Renegades Women': (155, 6),
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

        tot = sum(dl['runs']['total'] for o in inn['overs'] for dl in o['deliveries'])
        wk = sum(len(dl.get('wickets', [])) for o in inn['overs'] for dl in o['deliveries'])
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"-- Total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team][0]}/{EXPECTED_TOTALS[team][1]}",
              'OK' if ok else '*** MISMATCH ***')

        print('-- Extras --')
        for k in extras_total:
            if k not in EXPECTED_EXTRAS[team]:
                all_ok = False
                print(f"  unexpected extras type {k}: {extras_total[k]} *** MISMATCH ***")
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
