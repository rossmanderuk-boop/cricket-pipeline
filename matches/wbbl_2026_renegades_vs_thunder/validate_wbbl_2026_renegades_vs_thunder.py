"""
validate_wbbl_2026_renegades_vs_thunder.py - reconstruct batter/bowler figures, extras,
fielders and totals from the built JSON and diff against the official scorecard
(WBBL 2026/27, Melbourne Renegades Women vs Sydney Thunder Women, 2026-10-29).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_renegades_vs_thunder.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Melbourne Renegades Women': {
        'Courtney Webb': (22, 24, 3, 0, 'caught'),
        'Hayley Matthews': (45, 30, 6, 1, 'caught'),
        'Sophie Molineux': (7, 13, 0, 0, 'caught'),
        'Georgia Wareham': (23, 19, 3, 0, 'caught'),
        'Tess Flintoff': (1, 3, 0, 0, 'caught'),
        'Chloe Tryon': (10, 12, 1, 0, 'caught'),
        'Deandra Dottin': (0, 2, 0, 0, 'caught'),
        'Nicole Faltum': (2, 2, 0, 0, 'run out'),
        'Annie Wikman': (9, 7, 0, 0, 'not out'),
        'Milly Illingworth': (0, 1, 0, 0, 'caught'),
        'Tayla Vlaeminck': (10, 9, 0, 0, 'not out'),
    },
    'Sydney Thunder Women': {
        'Georgia Voll': (25, 18, 4, 1, 'caught'),
        'Phoebe Litchfield': (14, 17, 1, 0, 'caught'),
        'Anika Learoyd': (48, 37, 9, 0, 'bowled'),
        'Heather Knight': (29, 22, 3, 0, 'not out'),
        'Laura Harris': (0, 2, 0, 0, 'caught'),
        'Nadine de Klerk': (12, 6, 3, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Melbourne Renegades Women': {  # bowled by Sydney Thunder Women
        'Samantha Bates': (4.0, 20, 1),
        'Lauren Bell': (4.0, 35, 0),
        'Hannah Darlington': (4.0, 29, 2),
        'Nadine de Klerk': (4.0, 26, 1),
        'Georgia Voll': (4.0, 26, 4),
    },
    'Sydney Thunder Women': {  # bowled by Melbourne Renegades Women
        'Hayley Matthews': (1.0, 15, 0),
        'Tayla Vlaeminck': (4.0, 23, 2),
        'Sophie Molineux': (3.0, 23, 0),
        'Tess Flintoff': (1.0, 8, 1),
        'Georgia Wareham': (3.0, 22, 0),
        'Milly Illingworth': (2.0, 14, 0),
        'Deandra Dottin': (2.0, 27, 1),
        'Chloe Tryon': (1.0, 7, 0),
    },
}

EXPECTED_EXTRAS = {
    'Melbourne Renegades Women': {'byes': 0, 'legbyes': 2, 'noballs': 2, 'wides': 5},
    'Sydney Thunder Women': {'byes': 0, 'legbyes': 1, 'noballs': 0, 'wides': 11},
}

# Wicket-taker fielder checks: (batting_team, player_out) -> fielder names
EXPECTED_FIELDERS = {
    ('Melbourne Renegades Women', 'Courtney Webb'): ['Tahlia Wilson'],
    ('Melbourne Renegades Women', 'Hayley Matthews'): ['Lauren Bell'],
    ('Melbourne Renegades Women', 'Sophie Molineux'): ['Phoebe Litchfield'],
    ('Melbourne Renegades Women', 'Georgia Wareham'): ['Laura Harris'],
    ('Melbourne Renegades Women', 'Tess Flintoff'): ['Heather Knight'],
    ('Melbourne Renegades Women', 'Chloe Tryon'): ['Laura Harris'],
    ('Melbourne Renegades Women', 'Deandra Dottin'): ['Tahlia Wilson'],
    ('Melbourne Renegades Women', 'Nicole Faltum'): ['Georgia Voll', 'Tahlia Wilson'],
    ('Melbourne Renegades Women', 'Milly Illingworth'): ['Heather Knight'],
    ('Sydney Thunder Women', 'Georgia Voll'): ['Nicole Faltum'],
    ('Sydney Thunder Women', 'Phoebe Litchfield'): ['Sophie Molineux'],
    ('Sydney Thunder Women', 'Laura Harris'): ['Milly Illingworth'],
}

EXPECTED_TOTALS = {'Melbourne Renegades Women': (138, 9), 'Sydney Thunder Women': (140, 4)}


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
        tot = sum(x['runs']['total'] for o in inn['overs'] for x in o['deliveries'])
        wk = sum(len(x.get('wickets', [])) for o in inn['overs'] for x in o['deliveries'])

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
