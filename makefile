all: run
run:
	python3 main.py
debug:
	POKERBOT_DEBUG=1 python3 main.py