"""
validate_match34.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 34 (Jamaica Kingsmen vs Barbados
Tridents, Kensington Oval, Bridgetown, 2026-09-12).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match34_kingsmen_vs_tridents.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Jamaica Kingsmen': {
        'Maaz Sadaqat': (47, 34, 3, 2, 'caught'),
        'Kirk McKenzie': (11, 13, 2, 0, 'bowled'),
        'Usman Khan': (18, 17, 1, 1, 'caught'),
        'Rovman Powell': (8, 12, 1, 0, 'caught'),
        'Keemo Paul': (5, 12, 0, 0, 'caught'),
        'Andre Russell': (10, 4, 1, 1, 'caught'),
        'Hassan Khan': (16, 12, 1, 1, 'caught'),
        'Keacy Carty': (15, 7, 2, 1, 'caught'),
        'Odean Smith': (3, 6, 0, 0, 'not out'),
        'Vitel Lawes': (5, 3, 1, 0, 'run out'),
    },
    'Barbados Tridents': {
        'Brandon King': (18, 16, 3, 0, 'caught'),
        'Zachary Carter': (3, 5, 0, 0, 'bowled'),
        'Quinton de Kock': (14, 16, 1, 0, 'caught'),
        'Rivaldo Clarke': (1, 4, 0, 0, 'run out'),
        'Shadrack Descarte': (56, 42, 6, 2, 'caught'),
        'Sherfane Rutherford': (5, 10, 0, 0, 'run out'),
        'Chris Green': (17, 12, 2, 0, 'caught'),
        'Daniel Sams': (5, 6, 0, 0, 'caught'),
        'Gudakesh Motie': (17, 8, 2, 1, 'not out'),
        'AM Ghazanfar': (3, 3, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures keyed under the team that BATTED against them, i.e. the innings the
# bowler bowled in)
EXPECTED_BOWLING = {
    'Jamaica Kingsmen': {  # bowled by Barbados Tridents
        'Chris Green': (4.0, 23, 0),
        'Daniel Sams': (4.0, 41, 2),
        'AM Ghazanfar': (3.0, 26, 1),
        'Jakeem Pollard': (4.0, 38, 3),
        'Gudakesh Motie': (3.0, 7, 2),
        'Shadrack Descarte': (2.0, 12, 0),
    },
    'Barbados Tridents': {  # bowled by Jamaica Kingsmen
        'Hassan Khan': (2.0, 12, 1),
        'Andre Russell': (4.0, 28, 1),
        'Keemo Paul': (4.0, 34, 1),
        'Hunain Shah': (4.0, 25, 2),
        'Odean Smith': (2.0, 21, 0),
        'Vitel Lawes': (4.0, 26, 1),
    },
}

EXPECTED_EXTRAS = {
    'Jamaica Kingsmen': {'byes': 3, 'wides': 9},
    'Barbados Tridents': {'byes': 1, 'legbyes': 4, 'noballs': 2, 'wides': 5},
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
