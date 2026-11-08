"""
validate_match11.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for WBBL 2026/27 Match 11 (Perth Scorchers Women vs
Sydney Thunder Women, Drummoyne Oval, Sydney, 2026-11-05).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'wbbl_2026_match11_scorchers_vs_thunder.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Perth Scorchers Women': {
        'Beth Mooney': (80, 55, 8, 1, 'not out'),
        'Katie Mack': (10, 15, 1, 0, 'stumped'),
        'Sophie Devine': (42, 39, 3, 1, 'retired out'),
        'Freya Kemp': (30, 10, 2, 3, 'caught'),
        'Mikayla Hinkley': (1, 1, 0, 0, 'not out'),
    },
    'Sydney Thunder Women': {
        'Georgia Voll': (0, 1, 0, 0, 'bowled'),
        'Phoebe Litchfield': (34, 19, 5, 1, 'caught'),
        'Anika Learoyd': (22, 16, 4, 0, 'lbw'),
        'Heather Knight': (27, 26, 2, 1, 'stumped'),
        'Nadine de Klerk': (2, 4, 0, 0, 'lbw'),
        'Tahlia Wilson': (25, 19, 4, 0, 'caught'),
        'Laura Harris': (29, 12, 3, 2, 'bowled'),
        'Jemma Barsby': (9, 9, 1, 0, 'caught'),
        'Hannah Darlington': (5, 6, 0, 0, 'bowled'),
        'Lauren Bell': (1, 1, 0, 0, 'not out'),
        'Samantha Bates': (0, 1, 0, 0, 'bowled'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (keyed under the team that BATTED against them)
EXPECTED_BOWLING = {
    'Perth Scorchers Women': {  # bowled by Sydney Thunder Women
        'Samantha Bates': (4.0, 25, 0),
        'Lauren Bell': (4.0, 43, 0),
        'Hannah Darlington': (4.0, 34, 1),
        'Jemma Barsby': (3.0, 18, 1),
        'Nadine de Klerk': (3.0, 28, 0),
        'Georgia Voll': (2.0, 24, 0),
    },
    'Sydney Thunder Women': {  # bowled by Perth Scorchers Women
        'Chloe Ainsworth': (4.0, 24, 2),
        'Fatima Sana': (2.0, 15, 1),
        'Lilly Mills': (3.0, 33, 0),
        'Sophie Devine': (3.0, 31, 2),
        'Amy Edgar': (3.0, 22, 1),
        'Alana King': (4.0, 35, 4),
    },
}

EXPECTED_EXTRAS = {
    'Perth Scorchers Women': {'byes': 4, 'legbyes': 7, 'wides': 9},
    'Sydney Thunder Women': {'byes': 5, 'legbyes': 1, 'wides': 6},
}

EXPECTED_TOTALS = {
    'Perth Scorchers Women': (183, 3),
    'Sydney Thunder Women': (166, 10),
}

# Fall of wickets: (score, player) in order
EXPECTED_FOW = {
    'Perth Scorchers Women': [(51, 'Katie Mack'), (136, 'Sophie Devine'), (176, 'Freya Kemp')],
    'Sydney Thunder Women': [(0, 'Georgia Voll'), (41, 'Anika Learoyd'), (86, 'Phoebe Litchfield'),
                             (89, 'Nadine de Klerk'), (101, 'Heather Knight'), (144, 'Laura Harris'),
                             (153, 'Tahlia Wilson'), (165, 'Hannah Darlington'),
                             (166, 'Jemma Barsby'), (166, 'Samantha Bates')],
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
