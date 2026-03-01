train:
	python model/train.py

api:
	uvicorn app.main:app --reload --port 8000

lint:
	ruff check .

test:
	pytest

