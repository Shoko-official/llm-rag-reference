PYTHON ?= python

.PHONY: validate lint test

validate:
	$(PYTHON) scripts/validate_repo.py validate

lint:
	$(PYTHON) scripts/validate_repo.py lint

test:
	$(PYTHON) scripts/validate_repo.py test

search:
	$(PYTHON) scripts/query_search.py --query "main" --output table

