"""
validate_match16.py - diff the built JSON against the official scorecard for
WBBL 2026/27 match 16 (Melbourne Stars Women vs Perth Scorchers Women).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match16_stars_vs_scorchers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {'Melbourne Stars Women': {'Meg Lanning': (56, 46, 10, 0, 'caught'), 'Rhys McKenna': (12, 18, 2, 0, 'bowled'), 'Amy Jones': (4, 7, 0, 0, 'lbw'), 'Annabel Sutherland': (14, 9, 3, 0, 'bowled'), 'Naomi Stalenberg': (7, 10, 1, 0, 'run out'), 'Dani Gibson': (3, 5, 0, 0, 'caught'), 'Charlie Dean': (10, 14, 0, 0, 'not out'), 'Georgia Prestwidge': (23, 11, 2, 2, 'not out')}, 'Perth Scorchers Women': {'Katie Mack': (2, 3, 0, 0, 'bowled'), 'Beth Mooney': (28, 24, 4, 0, 'caught'), 'Sophie Devine': (55, 24, 8, 3, 'caught'), 'Freya Kemp': (2, 4, 0, 0, 'bowled'), 'Mikayla Hinkley': (24, 19, 3, 0, 'not out'), 'Chloe Piparo': (14, 16, 1, 0, 'not out')}}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets), keyed under the BATTING team
EXPECTED_BOWLING = {'Melbourne Stars Women': {'Fatima Sana': (4.0, 33, 1), 'Chloe Ainsworth': (3.0, 13, 0), 'Sophie Devine': (3.0, 18, 2), 'Alana King': (4.0, 12, 0), 'Amy Edgar': (3.0, 33, 2), 'Lilly Mills': (3.0, 24, 0)}, 'Perth Scorchers Women': {'Charlie Dean': (3.0, 26, 0), 'Kim Garth': (4.0, 32, 1), 'Sophie Day': (4.0, 34, 2), 'Annabel Sutherland': (3.0, 24, 1), 'Dani Gibson': (1.0, 15, 0)}}

EXPECTED_EXTRAS = {'Melbourne Stars Women': {'legbyes': 3, 'wides': 4}, 'Perth Scorchers Women': {'legbyes': 6, 'wides': 6}}

EXPECTED_TOTALS = {'Melbourne Stars Women': (136, 6), 'Perth Scorchers Women': (137, 4)}

EXPECTED_FOW = {'Melbourne Stars Women': [(38, 'Rhys McKenna'), (49, 'Amy Jones'), (65, 'Annabel Sutherland'), (86, 'Naomi Stalenberg'), (95, 'Dani Gibson'), (105, 'Meg Lanning')], 'Perth Scorchers Women': [(14, 'Katie Mack'), (86, 'Sophie Devine'), (90, 'Freya Kemp'), (109, 'Beth Mooney')]}


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
