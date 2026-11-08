"""
validate_match13.py - diff the built JSON against the official scorecard for
WBBL 2026/27 match 13 (Melbourne Renegades Women vs Adelaide Strikers Women).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match13_renegades_vs_strikers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {'Melbourne Renegades Women': {'Olivia Porter': (2, 7, 0, 0, 'caught'), 'Hayley Matthews': (49, 32, 10, 0, 'caught'), 'Courtney Webb': (52, 42, 5, 1, 'not out'), 'Sophie Molineux': (7, 8, 0, 0, 'bowled'), 'Georgia Wareham': (73, 31, 6, 4, 'not out')}, 'Adelaide Strikers Women': {'Emma de Broughe': (27, 24, 2, 1, 'run out'), 'Maia Bouchier': (54, 38, 7, 0, 'bowled'), 'Laura Wolvaardt': (2, 4, 0, 0, 'caught'), 'Tahlia McGrath': (8, 11, 1, 0, 'caught'), 'Madeline Penna': (12, 13, 1, 0, 'caught'), 'Bridget Patterson': (16, 12, 2, 1, 'caught'), 'Amanda-Jade Wellington': (0, 2, 0, 0, 'bowled'), 'Sophie Ecclestone': (20, 13, 3, 0, 'caught'), 'Eleanor Larosa': (6, 3, 1, 0, 'not out')}}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets), keyed under the BATTING team
EXPECTED_BOWLING = {'Melbourne Renegades Women': {'Megan Schutt': (4.0, 36, 0), 'Anesu Mushangwe': (2.0, 21, 1), 'Eleanor Larosa': (2.0, 12, 0), 'Amanda-Jade Wellington': (4.0, 43, 1), 'Sophie Ecclestone': (4.0, 42, 0), 'Madeline Penna': (1.0, 11, 0), 'Tahlia McGrath': (3.0, 22, 1)}, 'Adelaide Strikers Women': {'Sophie Molineux': (3.0, 31, 0), 'Tayla Vlaeminck': (4.0, 16, 2), 'Milly Illingworth': (3.0, 29, 3), 'Tess Flintoff': (1.0, 9, 0), 'Georgia Wareham': (4.0, 27, 1), 'Hayley Matthews': (3.0, 21, 1), 'Deandra Dottin': (2.0, 19, 0)}}

EXPECTED_EXTRAS = {'Melbourne Renegades Women': {'legbyes': 1, 'wides': 4}, 'Adelaide Strikers Women': {'wides': 7}}

EXPECTED_TOTALS = {'Melbourne Renegades Women': (188, 3), 'Adelaide Strikers Women': (152, 8)}

EXPECTED_FOW = {'Melbourne Renegades Women': [(36, 'Olivia Porter'), (64, 'Hayley Matthews'), (79, 'Sophie Molineux')], 'Adelaide Strikers Women': [(67, 'Emma de Broughe'), (76, 'Laura Wolvaardt'), (94, 'Maia Bouchier'), (97, 'Tahlia McGrath'), (123, 'Bridget Patterson'), (123, 'Amanda-Jade Wellington'), (140, 'Madeline Penna'), (152, 'Sophie Ecclestone')]}


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
