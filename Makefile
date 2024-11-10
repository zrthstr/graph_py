

new:
	#python -m venv grpy
	poetry new grpy



activte:
	#@echo "run: source grpy/bin/activate"
	#@echo 'check: echo $$VIRTUAL_ENV'
	poetry shell
	# poetry deactivate


run:
	@#poetry run python demo.py
	@#poetry run grpy ## this needs configuring in  pyproject.toml [tool.poetry.scripts] grpy = "grpy.__main__:main"
	@#rm recon.sqlite || true
	poetry run python -m grpy


add:
	poetry add pendulum
