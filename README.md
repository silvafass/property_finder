# Property Finder

Property Finder is a scanner/searcher to helps track new properties publications.

## Setup
```bash
# venv setup
python -m venv .venv
source .venv/bin/activate

# Dependencies installation
pip -r requirements.txt

# Python path setup
export PYTHONPATH=$PWD

# playwright setup
playwright install chromium firefox
```

## Configuration
```bash
cp config/sample.default.yaml config/default.yaml
```

## Startup
```bash
./bin/run.py
```
Or by using Xvfb:
```bash
xvfb-run ./bin/run.py
```

### Usage
This is a CLI tool, so you can use the help command to see and explore the different supported commands and its descriptions
```bash
./bin/run.py --help

Usage: run.py [OPTIONS] COMMAND [ARGS]...

 Property Finder is a scanner/searcher to helps track new properties publications.

  • Pass --non-log to disable the logs
  • Pass --non-only-inspect to pull all publications
  • Pass --always-download-pictures to force the download of publication pictures

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --log                         --no-log                           [default: log]                                │
│ --only-inspect                --no-only-inspect                  [default: only-inspect]                       │
│ --always-download-pictures    --no-always-download-pictures      [default: no-always-download-pictures]        │
│ --install-completion                                             Install completion for the current shell.     │
│ --show-completion                                                Show completion for the current shell, to     │
│                                                                  copy it or customize the installation.        │
│ --help                                                           Show this message and exit.                   │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ all-process             Perform all detailed search processing on the publishers website.                      │
│ detailed-info-process   Perform publication info processing on the publishers website.                         │
│ playground              Peform playground in publishers.                                                       │
│ search-process          Perform search processing on the publishers website.                                   │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
