"""
validate_match15.py - diff the built JSON against the official scorecard for
WBBL 2026/27 match 15 (Sydney Sixers Women vs Sydney Thunder Women).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match15_sixers_vs_thunder.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {'Sydney Sixers Women': {'Sophia Dunkley': (15, 15, 2, 0, 'caught'), 'Ellyse Perry': (59, 41, 11, 0, 'not out'), 'Melie Kerr': (14, 17, 1, 0, 'retired out'), 'Ashleigh Gardner': (64, 25, 5, 5, 'not out')}, 'Sydney Thunder Women': {'Phoebe Litchfield': (8, 5, 0, 1, 'bowled'), 'Georgia Voll': (8, 7, 0, 0, 'caught'), 'Anika Learoyd': (14, 9, 3, 0, 'run out'), 'Heather Knight': (6, 8, 0, 0, 'caught'), 'Nadine de Klerk': (30, 24, 5, 0, 'caught'), 'Laura Harris': (35, 10, 2, 4, 'caught'), 'Tahlia Wilson': (12, 6, 2, 0, 'caught'), 'Jemma Barsby': (0, 1, 0, 0, 'caught'), 'Hannah Darlington': (14, 8, 1, 1, 'bowled'), 'Lauren Bell': (11, 8, 2, 0, 'not out'), 'Samantha Bates': (10, 7, 2, 0, 'run out')}}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets), keyed under the BATTING team
EXPECTED_BOWLING = {'Sydney Sixers Women': {'Samantha Bates': (4.0, 48, 0), 'Lauren Bell': (3.0, 26, 1), 'Hannah Darlington': (3.0, 25, 0), 'Georgia Voll': (2.0, 10, 0), 'Nadine de Klerk': (2.0, 24, 0), 'Jemma Barsby': (2.0, 25, 0)}, 'Sydney Thunder Women': {'Lauren Cheatle': (3.0, 28, 0), 'Caoimhe Bray': (4.0, 28, 4), 'Melie Kerr': (2.0, 26, 0), 'Frankie Nicklin': (2.0, 14, 0), 'Sarah Coyte': (2.3, 21, 2), 'Ashleigh Gardner': (2.0, 37, 2)}}

EXPECTED_EXTRAS = {'Sydney Sixers Women': {'legbyes': 4, 'noballs': 2, 'wides': 4}, 'Sydney Thunder Women': {'legbyes': 4, 'wides': 6}}

EXPECTED_TOTALS = {'Sydney Sixers Women': (162, 2), 'Sydney Thunder Women': (158, 10)}

EXPECTED_FOW = {'Sydney Sixers Women': [(22, 'Sophia Dunkley'), (65, 'Melie Kerr')], 'Sydney Thunder Women': [(12, 'Phoebe Litchfield'), (34, 'Anika Learoyd'), (34, 'Georgia Voll'), (56, 'Heather Knight'), (108, 'Nadine de Klerk'), (115, 'Laura Harris'), (121, 'Tahlia Wilson'), (128, 'Jemma Barsby'), (137, 'Hannah Darlington'), (158, 'Samantha Bates')]}


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
