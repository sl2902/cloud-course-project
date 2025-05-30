# Execute the "targets" in this file with `make <target>` e.g. `make help`.
#
# You can also run multiple in sequence, e.g. `make clean lint test serve-coverage-report`
#
# See run.sh for more in-depth comments on what each target does.

build:
	bash run.sh build

deploy-lambda: clean
	bash run.sh deploy-lambda

deploy-lambda-code: clean
	bash run.sh deploy-lambda:code

run-docker:
	bash run.sh run-docker

run-locust:
	bash run.sh run-locust

install-generated-sdk:
	bash run.sh install-generated-sdk

generate-client-library:
	bash run.sh generate-client-library

run:
	bash run.sh run

run-mock:
	bash run.sh run-mock

clean:
	bash run.sh clean

help:
	bash run.sh help

install:
	bash run.sh install

lint:
	bash run.sh lint

lint-ci:
	bash run.sh lint:ci

publish-prod:
	bash run.sh publish:prod

publish-test:
	bash run.sh publish:test

release-prod:
	bash run.sh release:prod

release-test:
	bash run.sh release:test

serve-coverage-report:
	bash run.sh serve-coverage-report

test-ci:
	bash run.sh test:ci

test-quick:
	bash run.sh test:quick

test:
	bash run.sh run-tests

test-wheel-locally:
	bash run.sh test:wheel-locally
