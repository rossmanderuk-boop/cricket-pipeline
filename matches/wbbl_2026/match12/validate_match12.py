"""
validate_match12.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for WBBL 2026/27 Match 12 (Sydney Sixers Women vs
Melbourne Stars Women, Junction Oval, Melbourne, 2026-11-06).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match12_sixers_vs_stars.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Sydney Sixers Women': {
        'Ellyse Perry': (84, 57, 13, 1, 'not out'),
        'Sophia Dunkley': (1, 7, 0, 0, 'caught'),
        'Melie Kerr': (3, 4, 0, 0, 'caught'),
        'Ashleigh Gardner': (34, 23, 1, 2, 'stumped'),
        'Alice Capsey': (3, 8, 0, 0, 'bowled'),
        'Erin Burns': (29, 21, 3, 1, 'run out'),
    },
    'Melbourne Stars Women': {
        'Rhys McKenna': (0, 1, 0, 0, 'bowled'),
        'Meg Lanning': (2, 6, 0, 0, 'lbw'),
        'Amy Jones': (28, 26, 4, 0, 'bowled'),
        'Annabel Sutherland': (22, 15, 2, 1, 'caught'),
        'Naomi Stalenberg': (19, 17, 0, 0, 'run out'),
        'Charlie Dean': (25, 21, 2, 0, 'lbw'),
        'Dani Gibson': (31, 20, 2, 2, 'caught'),
        'Georgia Prestwidge': (21, 13, 1, 0, 'not out'),
        'Kim Garth': (1, 1, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Sydney Sixers Women': {  # bowled by Melbourne Stars Women
        'Charlie Dean': (4.0, 27, 1),
        'Kim Garth': (4.0, 37, 0),
        'Sophie Day': (4.0, 20, 1),
        'Maisy Gibson': (2.0, 18, 1),
        'Annabel Sutherland': (4.0, 34, 1),
        'Dani Gibson': (2.0, 23, 0),
    },
    'Melbourne Stars Women': {  # bowled by Sydney Sixers Women
        'Lauren Cheatle': (4.0, 29, 1),
        'Caoimhe Bray': (3.0, 28, 0),
        'Melie Kerr': (3.0, 21, 1),
        'Ashleigh Gardner': (4.0, 37, 1),
        'Ellyse Perry': (1.0, 5, 1),
        'Frankie Nicklin': (2.0, 10, 1),
        'Sarah Coyte': (3.0, 27, 1),
    },
}

EXPECTED_EXTRAS = {
    'Sydney Sixers Women': {'legbyes': 1, 'wides': 5},
    'Melbourne Stars Women': {'legbyes': 2, 'wides': 8},
}

EXPECTED_TOTALS = {
    'Sydney Sixers Women': (160, 5),
    'Melbourne Stars Women': (159, 7),
}

# Fall of wickets: (score, player) in order
EXPECTED_FOW = {
    'Sydney Sixers Women': [(11, 'Sophia Dunkley'), (25, 'Melie Kerr'), (92, 'Ashleigh Gardner'),
                            (98, 'Alice Capsey'), (160, 'Erin Burns')],
    'Melbourne Stars Women': [(0, 'Rhys McKenna'), (29, 'Meg Lanning'), (54, 'Annabel Sutherland'),
                              (62, 'Amy Jones'), (97, 'Naomi Stalenberg'), (134, 'Charlie Dean'),
                              (154, 'Dani Gibson')],
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

        fow = []; running = 0
        for o in inn['overs']:
            for dl in o['deliveries']:
                running += dl['runs']['total']
                for w in dl.get('wickets', []):
                    fow.append((running, w['player_out']))
        ok = fow == EXPECTED_FOW[team]
        all_ok &= ok
        print(f"-- Fall of wickets: {fow}", 'OK' if ok else f'*** MISMATCH *** expected {EXPECTED_FOW[team]}')

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
