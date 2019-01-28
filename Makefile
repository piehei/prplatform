



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

.PHONY: deploy

