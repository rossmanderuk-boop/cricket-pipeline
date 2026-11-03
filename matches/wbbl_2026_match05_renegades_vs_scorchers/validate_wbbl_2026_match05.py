"""
validate_wbbl_2026_match05.py - reconstruct batter/bowler figures, extras,
fielders and totals from the built JSON and diff against the official scorecard
(WBBL 2026/27 Match 5, Melbourne Renegades Women vs Perth Scorchers Women, 2026-10-31).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match05_renegades_vs_scorchers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Melbourne Renegades Women': {
        'Hayley Matthews': (7, 9, 1, 0, 'caught'),
        'Courtney Webb': (6, 9, 1, 0, 'bowled'),
        'Sophie Molineux': (1, 3, 0, 0, 'caught'),
        'Tess Flintoff': (2, 8, 0, 0, 'lbw'),
        'Nicole Faltum': (48, 49, 4, 0, 'bowled'),
        'Georgia Wareham': (62, 39, 8, 1, 'caught'),
        'Deandra Dottin': (5, 3, 0, 0, 'not out'),
        'Chloe Tryon': (1, 1, 0, 0, 'not out'),
    },
    'Perth Scorchers Women': {
        'Katie Mack': (9, 11, 1, 0, 'bowled'),
        'Beth Mooney': (58, 40, 9, 0, 'not out'),
        'Sophie Devine': (47, 32, 4, 3, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Melbourne Renegades Women': {  # bowled by Perth Scorchers Women
        'Chloe Ainsworth': (4.0, 22, 2),
        'Fatima Sana': (4.0, 27, 2),
        'Alana King': (4.0, 35, 1),
        'Sophie Devine': (3.0, 21, 1),
        'Amy Edgar': (3.0, 18, 0),
        'Lilly Mills': (2.0, 12, 0),
    },
    'Perth Scorchers Women': {  # bowled by Melbourne Renegades Women
        'Tayla Vlaeminck': (4.0, 29, 1),
        'Milly Illingworth': (2.0, 23, 0),
        'Sophie Molineux': (3.0, 27, 0),
        'Georgia Wareham': (1.3, 19, 0),
        'Hayley Matthews': (1.0, 10, 0),
        'Deandra Dottin': (2.0, 23, 0),
    },
}

# Scorecard (0s, WD, NB) per bowler. Cricinfo counts bye/leg-bye balls as dots.
EXPECTED_BOWLING_DETAIL = {
    'Melbourne Renegades Women': {
        'Chloe Ainsworth': (11, 1, 0), 'Fatima Sana': (12, 0, 1), 'Alana King': (6, 1, 0),
        'Sophie Devine': (7, 0, 0), 'Amy Edgar': (7, 0, 0), 'Lilly Mills': (4, 0, 0),
    },
    'Perth Scorchers Women': {
        'Tayla Vlaeminck': (13, 7, 1), 'Milly Illingworth': (5, 3, 0),
        'Sophie Molineux': (8, 1, 0), 'Georgia Wareham': (1, 0, 0),
        'Hayley Matthews': (0, 1, 0), 'Deandra Dottin': (6, 3, 1),
    },
}
SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT = {}

EXPECTED_EXTRAS = {
    'Melbourne Renegades Women': {'byes': 0, 'legbyes': 1, 'noballs': 1, 'wides': 2},
    'Perth Scorchers Women': {'byes': 0, 'legbyes': 7, 'noballs': 2, 'wides': 15},
}

# (batting_team, player_out) -> fielder names
EXPECTED_FIELDERS = {
    ('Melbourne Renegades Women', 'Hayley Matthews'): ['Freya Kemp'],
    ('Melbourne Renegades Women', 'Sophie Molineux'): ['Freya Kemp'],
    ('Melbourne Renegades Women', 'Georgia Wareham'): ['Fatima Sana'],
}

EXPECTED_TOTALS = {'Melbourne Renegades Women': (136, 6), 'Perth Scorchers Women': (138, 1)}


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
