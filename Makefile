TARGET ?= doru

type:
	poetry run mypy ${TARGET} --no-incremental --cache-dir=nul

lint:
	poetry run black .
	poetry run isort --atomic .
	poetry run autoflake \
		-r --in-place \
		--exclude ".venv" \
		--remove-all-unused-imports \
		--remove-unused-variables \
		.
	poetry run flake8 .
