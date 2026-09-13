# Cricket Pipeline

Converts ESPN Cricinfo ball-by-ball commentary into structured, [Cricsheet](https://cricsheet.org/)-format match JSON files.

## What it does

Cricinfo publishes rich ball-by-ball commentary for professional T20 matches, but it's unstructured text — not something you can analyse directly. This tool parses that commentary and outputs clean, validated JSON in the same format used by [Cricsheet](https://cricsheet.org/), the standard open dataset for ball-by-ball cricket data.

The output can be plugged straight into any tool built around the Cricsheet format — stats workbooks, models, dashboards — without needing to re-invent that structure.

## Why I built it

I spent 23 years as an in-play sports betting trader specialising in cricket. Converting each match manually into a workable dataset was slow and repetitive, so I built a pipeline to automate it — parsing commentary text into structured data I can use for analysis.

## How it works

1. Paste or feed in raw Cricinfo commentary and scorecard text for a match
2. The script parses it ball-by-ball — runs, wickets, overs, batters, bowlers
3. Output is validated and written as a match JSON file in Cricsheet format

## Example output

This repo currently includes matches from the 2026 Carribean Premier League (CPL) 9 matches, so far. 

Each match folder contains a single JSON file structured as:

```json
{
  "meta": { "...": "match info, teams, venue, date" },
  "innings": [
    { "...": "ball-by-ball data per innings" }
  ]
}
```

## Tech used

- Python
- JSON (Cricsheet schema)

## Status

Actively used — new matches are added as they're processed.
