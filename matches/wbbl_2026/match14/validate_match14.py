"""
validate_match14.py - diff the built JSON against the official scorecard for
WBBL 2026/27 match 14 (Hobart Hurricanes Women vs Brisbane Heat Women).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match14_hurricanes_vs_heat.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {'Hobart Hurricanes Women': {'Lizelle Lee': (2, 7, 0, 0, 'caught and bowled'), 'Kate Pelle': (9, 9, 1, 0, 'caught'), 'Chamari Athapaththu': (0, 1, 0, 0, 'bowled'), 'Rachel Trenaman': (25, 33, 1, 0, 'bowled'), 'Heather Graham': (21, 23, 1, 0, 'bowled'), 'Maddy Green': (24, 22, 3, 0, 'caught'), 'Chinelle Henry': (1, 3, 0, 0, 'caught'), 'Hayley Silver-Holmes': (12, 10, 1, 0, 'caught'), 'Molly Strano': (9, 10, 0, 0, 'not out'), 'Lauren Smith': (0, 1, 0, 0, 'bowled'), 'Isabella Malgioglio': (1, 1, 0, 0, 'not out')}, 'Brisbane Heat Women': {'Charli Knott': (6, 4, 1, 0, 'caught'), 'Grace Harris': (24, 16, 5, 0, 'bowled'), 'Yastika Bhatia': (22, 23, 3, 0, 'lbw'), 'Orla Prendergast': (11, 11, 2, 0, 'bowled'), 'Georgia Redmayne': (4, 6, 0, 0, 'run out'), 'Lucy Hamilton': (8, 11, 0, 0, 'caught'), "Annie O'Neil": (32, 28, 5, 0, 'not out'), 'Sianna Ginger': (10, 11, 1, 0, 'not out')}}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets), keyed under the BATTING team
EXPECTED_BOWLING = {'Hobart Hurricanes Women': {'Charli Knott': (3.0, 17, 0), 'Lily Bassingthwaighte': (4.0, 16, 3), 'Lucy Hamilton': (4.0, 24, 3), 'Orla Prendergast': (3.0, 14, 2), 'Sarah Glenn': (4.0, 23, 1), 'Catherine White': (1.0, 11, 0), 'Sianna Ginger': (1.0, 7, 0)}, 'Brisbane Heat Women': {'Molly Strano': (3.0, 23, 0), 'Chinelle Henry': (2.0, 21, 1), 'Heather Graham': (4.0, 20, 2), 'Isabella Malgioglio': (3.2, 22, 1), 'Lauren Smith': (3.0, 13, 1), 'Hayley Silver-Holmes': (3.0, 20, 0)}}

EXPECTED_EXTRAS = {'Hobart Hurricanes Women': {'byes': 4, 'wides': 8}, 'Brisbane Heat Women': {'wides': 2}}

EXPECTED_TOTALS = {'Hobart Hurricanes Women': (116, 9), 'Brisbane Heat Women': (119, 6)}

EXPECTED_FOW = {'Hobart Hurricanes Women': [(5, 'Lizelle Lee'), (6, 'Chamari Athapaththu'), (13, 'Kate Pelle'), (56, 'Heather Graham'), (65, 'Rachel Trenaman'), (72, 'Chinelle Henry'), (98, 'Hayley Silver-Holmes'), (111, 'Maddy Green'), (112, 'Lauren Smith')], 'Brisbane Heat Women': [(15, 'Charli Knott'), (42, 'Grace Harris'), (56, 'Orla Prendergast'), (69, 'Georgia Redmayne'), (69, 'Yastika Bhatia'), (89, 'Lucy Hamilton')]}


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
