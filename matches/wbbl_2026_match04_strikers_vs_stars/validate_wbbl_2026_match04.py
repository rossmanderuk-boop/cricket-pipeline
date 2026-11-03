"""
validate_wbbl_2026_match04.py - reconstruct batter/bowler figures, extras,
fielders and totals from the built JSON and diff against the official scorecard
(WBBL 2026/27 Match 4, Adelaide Strikers Women vs Melbourne Stars Women, 2026-10-31).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match04_strikers_vs_stars.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Adelaide Strikers Women': {
        'Laura Wolvaardt': (70, 50, 9, 0, 'caught'),
        'Maia Bouchier': (30, 21, 5, 0, 'caught and bowled'),
        'Tahlia McGrath': (43, 36, 6, 0, 'not out'),
        'Madeline Penna': (36, 13, 4, 3, 'not out'),
    },
    'Melbourne Stars Women': {
        'Rhys McKenna': (40, 31, 7, 0, 'bowled'),
        'Meg Lanning': (32, 24, 6, 0, 'lbw'),
        'Amy Jones': (2, 3, 0, 0, 'caught'),
        'Annabel Sutherland': (29, 19, 3, 1, 'caught'),
        'Naomi Stalenberg': (32, 25, 4, 0, 'caught'),
        'Dani Gibson': (1, 2, 0, 0, 'caught'),
        'Charlie Dean': (0, 2, 0, 0, 'bowled'),
        'Kim Garth': (13, 9, 2, 0, 'not out'),
        'Carly Leeson': (4, 5, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Adelaide Strikers Women': {  # bowled by Melbourne Stars Women
        'Kim Garth': (4.0, 27, 1),
        'Charlie Dean': (4.0, 25, 0),
        'Annabel Sutherland': (4.0, 40, 1),
        'Sophie Day': (3.0, 33, 0),
        'Maisy Gibson': (1.0, 11, 0),
        'Dani Gibson': (4.0, 47, 0),
    },
    'Melbourne Stars Women': {  # bowled by Adelaide Strikers Women
        'Eleanor Larosa': (4.0, 23, 2),
        'Anesu Mushangwe': (3.0, 34, 0),
        'Sophie Ecclestone': (4.0, 25, 2),
        'Madeline Penna': (2.0, 20, 0),
        'Tahlia McGrath': (2.0, 19, 0),
        'Amanda-Jade Wellington': (4.0, 28, 3),
        'Ella Wilson': (1.0, 9, 0),
    },
}

# Scorecard (0s, WD, NB) per bowler. Cricinfo counts bye/leg-bye balls as dots.
EXPECTED_BOWLING_DETAIL = {
    'Adelaide Strikers Women': {
        'Kim Garth': (9, 3, 0), 'Charlie Dean': (6, 0, 0), 'Annabel Sutherland': (9, 1, 0),
        'Sophie Day': (3, 0, 0), 'Maisy Gibson': (1, 0, 0), 'Dani Gibson': (3, 0, 0),
    },
    'Melbourne Stars Women': {
        'Eleanor Larosa': (12, 1, 0), 'Anesu Mushangwe': (6, 0, 0),
        'Sophie Ecclestone': (12, 2, 0), 'Madeline Penna': (2, 1, 0),
        'Tahlia McGrath': (4, 0, 0), 'Amanda-Jade Wellington': (9, 0, 0),
        'Ella Wilson': (2, 1, 0),
    },
}
SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT = {}

EXPECTED_EXTRAS = {
    'Adelaide Strikers Women': {'byes': 0, 'legbyes': 2, 'noballs': 0, 'wides': 4},
    'Melbourne Stars Women': {'byes': 5, 'legbyes': 1, 'noballs': 0, 'wides': 5},
}

# (batting_team, player_out) -> fielder names
EXPECTED_FIELDERS = {
    ('Adelaide Strikers Women', 'Laura Wolvaardt'): ['Annabel Sutherland'],
    ('Adelaide Strikers Women', 'Maia Bouchier'): [],
    ('Melbourne Stars Women', 'Amy Jones'): ['Sophie Ecclestone'],
    ('Melbourne Stars Women', 'Annabel Sutherland'): ['Maia Bouchier'],
    ('Melbourne Stars Women', 'Naomi Stalenberg'): ['Eleanor Larosa'],
    ('Melbourne Stars Women', 'Dani Gibson'): ['Madeline Penna'],
}

EXPECTED_TOTALS = {'Adelaide Strikers Women': (185, 2), 'Melbourne Stars Women': (164, 7)}


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
