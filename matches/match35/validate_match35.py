"""
validate_match35.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 35 (Guyana Amazon Warriors vs Barbados
Tridents, Kensington Oval, Bridgetown, 2026-09-13).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match35_amazon_vs_tridents.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'Guyana Amazon Warriors': {
        'Glenn Phillips': (24, 23, 2, 1, 'caught'),
        'Mavendra Dindyal': (6, 8, 1, 0, 'stumped'),
        'Shai Hope': (0, 2, 0, 0, 'caught'),
        'Shimron Hetmyer': (0, 1, 0, 0, 'caught'),
        'Mehidy Hasan Miraz': (18, 24, 1, 1, 'caught'),
        'Dwaine Pretorius': (0, 1, 0, 0, 'caught'),
        'Quentin Sampson': (12, 10, 1, 1, 'caught'),
        'Romario Shepherd': (22, 22, 1, 1, 'caught'),
        'Ronaldo Alimohamed': (0, 1, 0, 0, 'bowled'),
        'Imran Tahir': (8, 17, 0, 0, 'run out'),
        'Veerasammy Permaul': (0, 1, 0, 0, 'not out'),
    },
    'Barbados Tridents': {
        'Brandon King': (44, 42, 3, 2, 'not out'),
        'Zachary Carter': (3, 5, 0, 0, 'caught'),
        'Quinton de Kock': (3, 7, 0, 0, 'bowled'),
        'Sherfane Rutherford': (7, 4, 0, 1, 'caught'),
        'Shadrack Descarte': (32, 20, 2, 3, 'caught'),
        'Kevlon Anderson': (8, 11, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures keyed under the team that BATTED against them, i.e. the innings the
# bowler bowled in)
EXPECTED_BOWLING = {
    'Guyana Amazon Warriors': {  # bowled by Barbados Tridents
        'AM Ghazanfar': (4.0, 17, 3),
        'Gudakesh Motie': (4.0, 26, 0),
        'George Linde': (4.0, 13, 2),
        'Chris Green': (2.0, 15, 0),
        'Johann Layne': (2.0, 14, 3),
        'Shadrack Descarte': (2.0, 14, 0),
        'Sherfane Rutherford': (0.1, 0, 1),
    },
    'Barbados Tridents': {  # bowled by Guyana Amazon Warriors
        'Veerasammy Permaul': (4.0, 14, 1),
        'Imran Tahir': (4.0, 32, 1),
        'Mehidy Hasan Miraz': (4.0, 25, 2),
        'Glenn Phillips': (2.0, 15, 0),
        'Ronaldo Alimohamed': (0.5, 13, 0),
    },
}

EXPECTED_EXTRAS = {
    'Guyana Amazon Warriors': {'noballs': 1, 'wides': 8},
    'Barbados Tridents': {'legbyes': 1, 'wides': 2},
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
