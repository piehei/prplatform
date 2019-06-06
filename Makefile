



default:
	@echo "No default set. Choose from:"
	@echo "deploy"



SSH_DEPLOY_COMMAND = 'cd prplatform &&\
source ../venv/bin/activate &&\
source .env &&\
git pull &&\
python3.6 manage.py migrate &&\
python3.6 manage.py collectstatic &&\
touch config/production.wsgi &&\
touch config/production.wsgi'

deploy:
	# SSH_DEPLOY_URL in your shell env
	ssh ${SSH_DEPLOY_URL} $(SSH_DEPLOY_COMMAND)

test:
	docker-compose run --rm django python manage.py test

coverage:
	docker-compose run --rm django coverage run manage.py test && docker-compose run --rm djagno coverage html && echo "COVERAGE UPDATED, INSPECT htmlcov"


.PHONY: deploy test
