# Contributing

## Setup

```bash
git clone https://github.com/ArchishmanSengupta/primordium.git
cd primordium
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Verify

```bash
pytest tests/ -q
ruff check primordium/ --select E,F,W --ignore E501
primordium validate configs/template_quick.yaml
primordium run configs/template_quick.yaml
```

## Pull requests

- Target `master`
- Keep changes focused
- Ensure CI passes locally before opening a PR
