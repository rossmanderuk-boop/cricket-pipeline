"""
validate_match31.py - reconstruct batter and bowler figures from the built JSON and diff
against the official scorecard for CPL 2026 Match 31 (St Lucia Kings vs Guyana Amazon
Warriors, Providence Stadium, 2026-09-09).
"""

import json, os
from collections import defaultdict

_HERE = os.path.dirname(__file__)
JSON_PATH = os.path.join(_HERE, 'cpl_2026_match31_kings_vs_amazon.json')

# expected_by_team[batting_team][batter] = (runs, balls, fours, sixes, status_substring)
EXPECTED_BATTING = {
    'St Lucia Kings': {
        'Tim Seifert': (4, 5, 0, 0, 'lbw'),
        'Kamil Pooran': (43, 35, 6, 2, 'lbw'),
        'John Campbell': (12, 8, 2, 0, 'caught'),
        'Charith Asalanka': (8, 10, 0, 0, 'caught'),
        'Roston Chase': (1, 2, 0, 0, 'lbw'),
        'Kemol Savory': (2, 4, 0, 0, 'lbw'),
        'Obus Pienaar': (35, 28, 4, 1, 'caught'),
        'McKenny Clarke': (0, 2, 0, 0, 'bowled'),
        'Matthew Forde': (0, 2, 0, 0, 'bowled'),
        'Joshua Bishop': (5, 6, 1, 0, 'lbw'),
        'Maheesh Theekshana': (6, 11, 0, 0, 'not out'),
    },
    'Guyana Amazon Warriors': {
        'Glenn Phillips': (37, 40, 2, 1, 'bowled'),
        'Mavendra Dindyal': (5, 9, 1, 0, 'caught'),
        'Shai Hope': (21, 31, 0, 0, 'caught'),
        'Shimron Hetmyer': (14, 13, 0, 1, 'caught'),
        'Mehidy Hasan Miraz': (1, 4, 0, 0, 'caught'),
        'Quentin Sampson': (37, 11, 1, 5, 'not out'),
        'Romario Shepherd': (1, 2, 0, 0, 'caught'),
        'Dwaine Pretorius': (1, 1, 0, 0, 'not out'),
    },
}

# expected_bowling[batting_team][bowler] = (overs, runs, wickets)
# (bowling figures are keyed under the team that BATTED against them, i.e. the innings
# the bowler bowled in, per the toolkit's known pitfall about this)
EXPECTED_BOWLING = {
    'St Lucia Kings': {  # bowled by Guyana Amazon Warriors
        'Dwaine Pretorius': (3.0, 27, 1),
        'Khary Pierre': (2.0, 16, 0),
        'Shamar Joseph': (3.0, 16, 0),
        'Mehidy Hasan Miraz': (4.0, 13, 3),
        'Imran Tahir': (4.0, 17, 5),
        'Glenn Phillips': (1.0, 16, 0),
        'Romario Shepherd': (1.5, 13, 1),
    },
    'Guyana Amazon Warriors': {  # bowled by St Lucia Kings
        'Matthew Forde': (2.3, 13, 1),
        'Maheesh Theekshana': (4.0, 29, 1),
        'Roston Chase': (4.0, 34, 3),
        'Joshua Bishop': (4.0, 17, 0),
        'Charith Asalanka': (4.0, 27, 1),
    },
}

EXPECTED_EXTRAS = {
    'St Lucia Kings': {'legbyes': 1, 'wides': 2},
    'Guyana Amazon Warriors': {'legbyes': 2, 'wides': 3},
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
