POETRY = poetry
RUN = $(POETRY) run
APP = grpy

.PHONY: all clean test install run stats clear reset

all: install test

clean:
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test: clear run stats

install:
	$(POETRY) install

run:
	$(RUN) $(APP) ingest

stats:
	$(RUN) $(APP) stats

clear:
	$(RUN) $(APP) clear