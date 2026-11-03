"""
validate_wbbl_2026_match02.py - reconstruct batter/bowler figures, extras,
fielders and totals from the built JSON and diff against the official scorecard
(WBBL 2026/27 Match 2, Melbourne Stars Women vs Hobart Hurricanes Women, 2026-10-29).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match02_stars_vs_hurricanes.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Melbourne Stars Women': {
        'Rhys McKenna': (13, 10, 3, 0, 'caught'),
        'Meg Lanning': (71, 52, 10, 0, 'lbw'),
        'Amy Jones': (7, 7, 1, 0, 'stumped'),
        'Annabel Sutherland': (57, 36, 5, 2, 'lbw'),
        'Dani Gibson': (22, 11, 2, 1, 'not out'),
        'Kim Garth': (6, 4, 0, 0, 'not out'),
    },
    'Hobart Hurricanes Women': {
        'Lizelle Lee': (57, 33, 6, 3, 'caught'),
        'Chamari Athapaththu': (10, 8, 2, 0, 'bowled'),
        'Rachel Trenaman': (24, 17, 3, 0, 'caught'),
        'Nicola Carey': (32, 25, 4, 0, 'stumped'),
        'Heather Graham': (20, 15, 4, 0, 'bowled'),
        'Maddy Green': (5, 6, 1, 0, 'bowled'),
        'Chinelle Henry': (11, 11, 2, 0, 'not out'),
        'Ruth Johnston': (0, 1, 0, 0, 'caught'),
        'Lauren Smith': (5, 3, 1, 0, 'stumped'),
        'Molly Strano': (1, 1, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Melbourne Stars Women': {  # bowled by Hobart Hurricanes Women
        'Molly Strano': (4.0, 38, 0),
        'Nicola Carey': (3.0, 41, 0),
        'Chinelle Henry': (3.0, 25, 1),
        'Heather Graham': (4.0, 31, 2),
        'Lauren Smith': (4.0, 30, 1),
        'Ira Aery': (2.0, 24, 0),
    },
    'Hobart Hurricanes Women': {  # bowled by Melbourne Stars Women
        'Kim Garth': (4.0, 36, 2),
        'Charlie Dean': (4.0, 13, 1),
        'Annabel Sutherland': (4.0, 34, 3),
        'Sophie Day': (2.0, 28, 0),
        'Dani Gibson': (2.0, 23, 0),
        'Carly Leeson': (1.0, 12, 0),
        'Maisy Gibson': (3.0, 25, 2),
    },
}

# Scorecard (0s, WD, NB) per bowler. Cricinfo counts leg-bye balls as dots.
EXPECTED_BOWLING_DETAIL = {
    'Melbourne Stars Women': {
        'Molly Strano': (8, 0, 0), 'Nicola Carey': (6, 2, 0), 'Chinelle Henry': (6, 2, 0),
        'Heather Graham': (6, 1, 0), 'Lauren Smith': (7, 0, 0), 'Ira Aery': (2, 3, 0),
    },
    'Hobart Hurricanes Women': {
        'Kim Garth': (9, 1, 0), 'Charlie Dean': (14, 0, 0), 'Annabel Sutherland': (10, 0, 0),
        'Sophie Day': (0, 0, 0), 'Carly Leeson': (0, 1, 0),
        # Scorecard prints Dani 9 / Maisy 2 dots, which is inconsistent with its own
        # O/R/W rows (2 overs for 23 runs cannot include 9 dots). Expect the O/R/W-consistent
        # values here and report the scorecard's printed values alongside.
        'Dani Gibson': (2, 0, 0), 'Maisy Gibson': (9, 0, 0),
    },
}
SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT = {'Dani Gibson': 9, 'Maisy Gibson': 2}

EXPECTED_EXTRAS = {
    'Melbourne Stars Women': {'byes': 0, 'legbyes': 3, 'noballs': 0, 'wides': 13},
    'Hobart Hurricanes Women': {'byes': 0, 'legbyes': 3, 'noballs': 0, 'wides': 6},
}

# (batting_team, player_out) -> fielder names
EXPECTED_FIELDERS = {
    ('Melbourne Stars Women', 'Rhys McKenna'): ['Ruth Johnston'],
    ('Melbourne Stars Women', 'Amy Jones'): ['Lizelle Lee'],
    ('Hobart Hurricanes Women', 'Lizelle Lee'): ['Meg Lanning'],
    ('Hobart Hurricanes Women', 'Rachel Trenaman'): ['Rhys McKenna'],
    ('Hobart Hurricanes Women', 'Nicola Carey'): ['Amy Jones'],
    ('Hobart Hurricanes Women', 'Ruth Johnston'): ['Charlie Dean'],
    ('Hobart Hurricanes Women', 'Lauren Smith'): ['Amy Jones'],
}

EXPECTED_TOTALS = {'Melbourne Stars Women': (192, 4), 'Hobart Hurricanes Women': (174, 8)}


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
        fielders_got = {}
        bdet = defaultdict(lambda: [0, 0, 0])
        tot = sum(x['runs']['total'] for o in inn['overs'] for x in o['deliveries'])
        wk = sum(len(x.get('wickets', [])) for o in inn['overs'] for x in o['deliveries'])

        for over in inn['overs']:
            for deliv in over['deliveries']:
                b = deliv['batter']
                bwl = deliv['bowler']
                ex = deliv.get('extras', {})

                bdet[bwl][0] += deliv['runs']['batter'] == 0 and set(ex) <= {'legbyes', 'byes'}
                bdet[bwl][1] += ex.get('wides', 0) > 0
                bdet[bwl][2] += ex.get('noballs', 0) > 0
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
                    fielders_got[w['player_out']] = [f['name'] for f in w.get('fielders', [])]
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

        print('-- Bowler 0s/WD/NB --')
        for name, e in EXPECTED_BOWLING_DETAIL[team].items():
            ok = tuple(bdet[name]) == e
            all_ok &= ok
            note = (f" (scorecard prints {SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT[name]} dots - known inconsistent)"
                    if name in SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT else '')
            print(f"  {name}: got {tuple(bdet[name])} vs expected {e}{note}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Extras --')
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

        print('-- Fielders / total --')
        for (t, pl), ef in EXPECTED_FIELDERS.items():
            if t != team: continue
            ok = fielders_got.get(pl) == ef
            all_ok &= ok
            print(f"  {pl}: got {fielders_got.get(pl)} vs expected {ef}", 'OK' if ok else '*** MISMATCH ***')
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"  total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team]}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
