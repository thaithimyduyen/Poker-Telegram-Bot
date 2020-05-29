all: check test run
run:
	python3 main.py
debug:
	POKERBOT_DEBUG=1 python3 main.py
test:
	python3 -m unittest discover -s ./tests
check:
	flake8 .