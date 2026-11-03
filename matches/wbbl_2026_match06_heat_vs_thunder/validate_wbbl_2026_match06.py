"""
validate_wbbl_2026_match06.py - reconstruct batter/bowler figures, extras,
fielders and totals from the built JSON and diff against the official scorecard
(WBBL 2026/27 Match 6, Brisbane Heat Women vs Sydney Thunder Women, 2026-11-01).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match06_heat_vs_thunder.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Brisbane Heat Women': {
        'Charli Knott': (16, 11, 3, 0, 'bowled'),
        'Grace Harris': (58, 37, 7, 2, 'caught'),
        'Georgia Redmayne': (57, 44, 4, 1, 'caught'),
        'Yastika Bhatia': (1, 3, 0, 0, 'caught and bowled'),
        'Orla Prendergast': (28, 20, 5, 0, 'stumped'),
        "Annie O'Neil": (8, 4, 0, 1, 'not out'),
        'Lucy Hamilton': (2, 1, 0, 0, 'not out'),
    },
    'Sydney Thunder Women': {
        'Phoebe Litchfield': (41, 19, 6, 1, 'caught'),
        'Georgia Voll': (2, 7, 0, 0, 'caught'),
        'Anika Learoyd': (37, 28, 2, 2, 'caught'),
        'Heather Knight': (54, 29, 7, 2, 'not out'),
        'Laura Harris': (35, 16, 6, 1, 'caught'),
        'Nadine de Klerk': (4, 1, 1, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Brisbane Heat Women': {  # bowled by Sydney Thunder Women
        'Samantha Bates': (4.0, 34, 1),
        'Lauren Bell': (4.0, 38, 1),
        'Hannah Darlington': (2.0, 20, 0),
        'Jemma Barsby': (3.0, 25, 0),
        'Nadine de Klerk': (4.0, 34, 1),
        'Georgia Voll': (3.0, 25, 2),
    },
    'Sydney Thunder Women': {  # bowled by Brisbane Heat Women
        'Lucy Hamilton': (3.0, 34, 1),
        'Lily Bassingthwaighte': (3.4, 31, 2),
        'Orla Prendergast': (2.0, 23, 1),
        'Sarah Glenn': (3.0, 40, 0),
        'Charli Knott': (2.0, 19, 0),
        'Sianna Ginger': (3.0, 33, 0),
    },
}

# Scorecard (0s, WD, NB) per bowler. Cricinfo counts bye/leg-bye balls as dots.
EXPECTED_BOWLING_DETAIL = {
    'Brisbane Heat Women': {
        'Samantha Bates': (7, 0, 0), 'Lauren Bell': (7, 4, 0), 'Hannah Darlington': (3, 0, 0),
        'Jemma Barsby': (3, 0, 0), 'Nadine de Klerk': (9, 0, 0), 'Georgia Voll': (6, 2, 0),
    },
    'Sydney Thunder Women': {
        'Lucy Hamilton': (6, 3, 0), 'Lily Bassingthwaighte': (10, 2, 0),
        'Orla Prendergast': (4, 0, 0), 'Sarah Glenn': (3, 0, 0),
        'Charli Knott': (3, 1, 0), 'Sianna Ginger': (4, 1, 0),
    },
}
SCORECARD_PRINTED_DOTS_KNOWN_INCONSISTENT = {}

EXPECTED_EXTRAS = {
    'Brisbane Heat Women': {'byes': 0, 'legbyes': 2, 'noballs': 0, 'wides': 6},
    'Sydney Thunder Women': {'byes': 0, 'legbyes': 0, 'noballs': 0, 'wides': 7},
}

# (batting_team, player_out) -> fielder names
EXPECTED_FIELDERS = {
    ('Brisbane Heat Women', 'Grace Harris'): ['Hannah Darlington'],
    ('Brisbane Heat Women', 'Georgia Redmayne'): ['Jemma Barsby'],
    ('Brisbane Heat Women', 'Yastika Bhatia'): [],
    ('Brisbane Heat Women', 'Orla Prendergast'): ['Tahlia Wilson'],
    ('Sydney Thunder Women', 'Phoebe Litchfield'): ['Orla Prendergast'],
    ('Sydney Thunder Women', 'Georgia Voll'): ['Georgia Redmayne'],
    ('Sydney Thunder Women', 'Anika Learoyd'): ['Ayaka Kato-Stafford'],
    ('Sydney Thunder Women', 'Laura Harris'): ['Grace Harris'],
}

EXPECTED_TOTALS = {'Brisbane Heat Women': (178, 5), 'Sydney Thunder Women': (180, 4)}


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
