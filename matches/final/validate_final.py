"""
validate_final.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for the CPL 2026 Final (Jamaica Kingsmen vs Antigua and
Barbuda Falcons, Kensington Oval, Bridgetown, 2026-09-20).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_final_kingsmen_vs_falcons.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Jamaica Kingsmen': {
        'Maaz Sadaqat': (114, 58, 8, 9, 'caught'),
        'Kirk McKenzie': (0, 4, 0, 0, 'caught'),
        'Keacy Carty': (9, 8, 1, 0, 'caught'),
        'Saim Ayub': (29, 22, 2, 1, 'caught'),
        'Rovman Powell': (0, 3, 0, 0, 'caught'),
        'Romaine Morris': (0, 3, 0, 0, 'lbw'),
        'Hassan Khan': (1, 3, 0, 0, 'caught'),
        'Keemo Paul': (3, 9, 0, 0, 'stumped'),
        'Andre Russell': (2, 7, 0, 0, 'caught'),
        'Hunain Shah': (0, 3, 0, 0, 'not out'),
        'Vitel Lawes': (0, 1, 0, 0, 'not out'),
    },
    'Antigua and Barbuda Falcons': {
        'Rahkeem Cornwall': (20, 6, 2, 2, 'bowled'),
        'Evin Lewis': (38, 26, 5, 2, 'bowled'),
        'Amir Jangoo': (57, 34, 4, 3, 'not out'),
        'Hasan Nawaz': (47, 35, 3, 3, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures keyed under the team that BATTED against them, i.e. the innings the
# bowler bowled in)
EXPECTED_BOWLING = {
    'Jamaica Kingsmen': {  # bowled by Antigua and Barbuda Falcons
        'Jayden Seales': (2.0, 18, 1),
        'Alzarri Joseph': (4.0, 27, 2),
        'Rahkeem Cornwall': (3.0, 35, 0),
        'Joshua James': (2.0, 36, 0),
        'Shadab Khan': (4.0, 28, 1),
        'Sufyan Moqim': (4.0, 14, 4),
        'Shamar Springer': (1.0, 10, 1),
    },
    'Antigua and Barbuda Falcons': {  # bowled by Jamaica Kingsmen
        'Saim Ayub': (3.0, 42, 1),
        'Andre Russell': (2.0, 16, 0),
        'Hunain Shah': (2.1, 26, 0),
        'Keemo Paul': (3.0, 18, 0),
        'Vitel Lawes': (4.0, 32, 1),
        'Hassan Khan': (1.0, 14, 0),
        'Rovman Powell': (1.3, 23, 0),
    },
}

EXPECTED_EXTRAS = {
    'Jamaica Kingsmen': {'byes': 1, 'legbyes': 1, 'noballs': 1, 'wides': 9},
    'Antigua and Barbuda Falcons': {'legbyes': 2, 'noballs': 1, 'wides': 8},
}

EXPECTED_TOTALS = {'Jamaica Kingsmen': (170, 9), 'Antigua and Barbuda Falcons': (173, 2)}


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

        tot = sum(dl['runs']['total'] for o in inn['overs'] for dl in o['deliveries'])
        wk = sum(len(dl.get('wickets', [])) for o in inn['overs'] for dl in o['deliveries'])
        ok = (tot, wk) == EXPECTED_TOTALS[team]
        all_ok &= ok
        print(f"-- Total: got {tot}/{wk} vs expected {EXPECTED_TOTALS[team][0]}/{EXPECTED_TOTALS[team][1]}",
              'OK' if ok else '*** MISMATCH ***')

    print()
    print('ALL OK' if all_ok else '*** SOME MISMATCHES - fix before using this file ***')
    return all_ok


if __name__ == '__main__':
    main()
