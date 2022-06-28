all: install lint test run
run:
	python3 main.py
up:
	docker-compose --env-file .env up --build -d
logs:
	docker-compose logs bot
down:
	docker-compose down
debug:
	POKERBOT_DEBUG=1 python3 main.py
test:
	python3 -m unittest discover -s ./tests
lint:
	python3 -m flake8 .
install:
	pip3 install -r requirements.txt
.env:
ifeq ($(POKERBOT_TOKEN),)
	@printf "Usage:\n\n\tmake .env POKERBOT_TOKEN=<your telegram token>\n\n"
	@exit 1
endif
	printf "POKERBOT_TOKEN=$(POKERBOT_TOKEN)" > .env
