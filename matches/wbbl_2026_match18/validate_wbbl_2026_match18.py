"""
validate_wbbl_2026_match18.py - reconstruct batter and bowler figures from the built JSON
and diff against the official scorecard for WBBL 2026/27 Match 18 (Sydney Thunder Women vs
Perth Scorchers Women, W.A.C.A, Perth, 2026-11-11).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match18_thunder_vs_scorchers.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Sydney Thunder Women': {
        'Phoebe Litchfield': (13, 14, 2, 0, 'caught'),
        'Georgia Voll': (0, 5, 0, 0, 'caught'),
        'Anika Learoyd': (53, 44, 5, 1, 'caught'),
        'Heather Knight': (71, 46, 12, 0, 'bowled'),
        'Laura Harris': (3, 6, 0, 0, 'caught'),
        'Nadine de Klerk': (8, 5, 1, 0, 'not out'),
        'Tahlia Wilson': (1, 1, 0, 0, 'not out'),
    },
    'Perth Scorchers Women': {
        'Katie Mack': (31, 27, 5, 0, 'caught and bowled'),
        'Ines Mckeon': (6, 2, 0, 1, 'lbw'),
        'Sophie Devine': (37, 32, 5, 1, 'bowled'),
        'Freya Kemp': (10, 8, 2, 0, 'caught'),
        'Mikayla Hinkley': (24, 16, 3, 1, 'run out'),
        'Chloe Piparo': (20, 16, 2, 0, 'not out'),
        'Fatima Sana': (0, 2, 0, 0, 'bowled'),
        'Chloe Ainsworth': (15, 8, 2, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
EXPECTED_BOWLING = {
    'Sydney Thunder Women': {  # bowled by Perth Scorchers Women
        'Chloe Ainsworth': (3.0, 22, 1),
        'Lilly Mills': (3.0, 29, 0),
        'Fatima Sana': (4.0, 26, 1),
        'Alana King': (4.0, 30, 1),
        'Sophie Devine': (3.0, 23, 1),
        'Amy Edgar': (3.0, 24, 1),
    },
    'Perth Scorchers Women': {  # bowled by Sydney Thunder Women
        'Samantha Bates': (4.0, 32, 1),
        'Lauren Bell': (3.3, 26, 1),
        'Hannah Darlington': (3.0, 29, 1),
        'Nadine de Klerk': (4.0, 30, 1),
        'Georgia Voll': (2.0, 18, 0),
        'Jemma Barsby': (2.0, 19, 1),
    },
}

EXPECTED_EXTRAS = {
    'Sydney Thunder Women': {'byes': 1, 'legbyes': 4, 'noballs': 1, 'wides': 4},
    'Perth Scorchers Women': {'byes': 0, 'legbyes': 6, 'noballs': 0, 'wides': 11},
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

        print('-- Extras --')
        for k, v in EXPECTED_EXTRAS[team].items():
            ok = extras_total.get(k, 0) == v
            all_ok &= ok
            print(f"  {k}: got {extras_total.get(k, 0)} vs expected {v}", 'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
