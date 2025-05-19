#!/bin/bash

set -e

#####################
# --- Constants --- #
#####################

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
MINIMUM_TEST_COVERAGE_PERCENT=0

AWS_LAMBDA_FUNCTION_NAME="files-api-handler"
BUILD_DIR_REL_PATH="./build"
BUILD_DIR="${THIS_DIR}/${BUILD_DIR_REL_PATH}"


##########################
# --- Task Functions --- #
##########################

# install core and development Python dependencies into the currently activated venv
function install {
    uv pip install --editable "$THIS_DIR/[dev]"
}

function deploy-lambda {
    export AWS_PROFILE=cloud-course
    export AWS_REGION=us-west-2
    deploy-lambda:cd
}

function deploy-lambda:cd {
    # Get the current user ID and group ID to run the docker command with so that
	# the generated lambda-env folder doesn't have root permissions, instead user level permission
	# This will help in library installation in the docker container and cleaning up the lambda-env folder later on.
	USER_ID=$(id -u)
	GROUP_ID=$(id -g)

    LAMBDA_LAYER_DIR_NAME="lambda-env"
    LAMBDA_LAYER_DIR="${BUILD_DIR}/${LAMBDA_LAYER_DIR_NAME}"
    LAMBDA_LAYER_ZIP_FPATH="${BUILD_DIR}/lambda-layer.zip"
    LAMBDA_HANDLER_ZIP_FPATH="${BUILD_DIR}/lambda.zip"
    SRC_DIR="${THIS_DIR}/src"

    # clean up artifacts
    rm -rf "$LAMBDA_LAYER_DIR" || true
    rm -f "$LAMBDA_LAYER_ZIP_FPATH" || true

    # install dependencies
    docker logout || true  # log out to use the public ecr
    docker pull public.ecr.aws/lambda/python:3.12-arm64

    # install dependencies in a docker container to ensure compatibility with AWS Lambda
    #
    # Note: we remove boto3 and botocore because AWS lambda automatically
    # provides these. This saves us ~24MB in the final, uncompressed layer size.
    docker run --rm \
        --user $USER_ID:$GROUP_ID \
        --volume "${THIS_DIR}":/out \
        --entrypoint /bin/bash \
        public.ecr.aws/lambda/python:3.12-arm64 \
        -c " \
        pip install --root --upgrade pip \
        && pip install \
            --editable /out/[aws-lambda] \
            --target /out/${BUILD_DIR_REL_PATH}/${LAMBDA_LAYER_DIR_NAME}/python
        "

    # bundle dependencies and handler in a zip file
    cd "$LAMBDA_LAYER_DIR"
    zip -r "$LAMBDA_LAYER_ZIP_FPATH" ./

    cd "$SRC_DIR"
    zip -r "$LAMBDA_HANDLER_ZIP_FPATH" ./

    cd "$THIS_DIR"

    # publish the lambda "deployment package" (the handler)
    aws lambda update-function-code \
        --function-name "$AWS_LAMBDA_FUNCTION_NAME" \
        --zip-file fileb://${LAMBDA_HANDLER_ZIP_FPATH} \
        --output json | cat

    # publish the lambda layer with a new version
    LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
        --layer-name cloud-course-project-python-deps \
        --compatible-runtimes python3.12 \
        --zip-file fileb://${LAMBDA_LAYER_ZIP_FPATH} \
        --compatible-architectures arm64 \
        --query 'LayerVersionArn' \
        --output text | cat)

    # update the lambda function to use the new layer version
    aws lambda update-function-configuration \
        --function-name "$AWS_LAMBDA_FUNCTION_NAME" \
        --layers $LAYER_VERSION_ARN \
        --handler "files_api.aws_lambda_handler.handler" \
        --output json | cat
}

function set-local-aws-env-vars {
    export AWS_PROFILE=mlops-club-sso
    export AWS_REGION=us-west-2
}

function run-docker {
    set-local-aws-env-vars
    aws configure export-credentials --profile $AWS_PROFILE --format env > .env
    # aws configure get aws_access_key_id --profile $AWS_PROFILE     | awk '{print "AWS_ACCESS_KEY_ID=" $0}' > .env
    # aws configure get aws_secret_access_key --profile $AWS_PROFILE | awk '{print "AWS_SECRET_ACCESS_KEY=" $0}' >> .env
    # aws configure get region --profile $AWS_PROFILE                | awk '{print "AWS_REGION=" $0}' >> .env

    docker compose up --build -d
}

function run-locust {
    set-local-aws-env-vars
    aws configure export-credentials --profile $AWS_PROFILE --format env > .env
    docker compose \
        --file docker-compose.yaml \
        --file docker-compose.locust.yaml \
        up \
        --build \
        -d
}

function install-generated-sdk {
    # setting editable_mode=strict fixes an issue with autocompletion
    # in VS Code when installing editable packages. See:
    # https://github.com/microsoft/pylance-release/issues/3473
    uv pip install --editable "$THIS_DIR/files-api-sdk" \
        --config-settings editable_mode=strict
}

function generate-client-library {
    docker run --rm \
        -v ${PWD}:/local openapitools/openapi-generator-cli generate \
        --generator-name python-pydantic-v1 \
        --input-spec /local/openapi.json \
        --output /local/files-api-sdk \
        --package-name files_api_sdk
}

function run {
    export S3_BUCKET_NAME=some-bucket
    export LOGURU_LEVEL="INFO"
    AWS_PROFILE=cloud-course uvicorn files_api.main:create_app --reload
}

function run-mock {
    set +e
    # lsof -i :5000 | grep LISTEN | awk '{print $2}' | xargs kill -9
    python -m moto.server -p 5000 &
    MOTO_PID=$!
    export AWS_ENDPOINT_URL="http://localhost:5000"
    export AWS_SECRET_ACCESS_KEY="mock"
    export AWS_ACCESS_KEY_ID="mock"
    export S3_BUCKET_NAME=some-bucket

    if ! aws s3 ls "s3://$S3_BUCKET_NAME" --endpoint-url "http://localhost:5000" 2>/dev/null; then
        aws s3 mb "s3://$S3_BUCKET_NAME" --endpoint-url "http://localhost:5000"
    fi

    trap 'kill $MOTO_PID' EXIT
    uvicorn files_api.main:create_app --reload
    wait $MOTO_PID
}

# run linting, formatting, and other static code quality tools
function lint {
    pre-commit run --all-files
}

# same as `lint` but with any special considerations for CI
function lint:ci {
    SKIP=no-commit-to-branch pre-commit run --all-files
}

# execute tests that are not marked as `slow`
function test:quick {
    run-tests -m "not slow" ${@:-"$THIS_DIR/tests/"}
}

# execute tests against the installed package; assumes the wheel is already installed
function test:ci {
    INSTALLED_PKG_DIR="$(python -c 'import files_api; print(files_api.__path__[0])')"
    COVERAGE_DIR="$INSTALLED_PKG_DIR" run-tests
}

function run-tests {
    PYTEST_EXIT_STATUS=0

    rm -rf "$THIS_DIR/test-reports" || mkdir "$THIS_DIR/test-reports"

    python -m pytest ${@:-"$THIS_DIR/tests/"} \
        --cov "${COVERAGE_DIR:-$THIS_DIR/src}" \
        --cov-report html \
        --cov-report term \
        --cov-report xml \
        --cov-report=term-missing \
        --junit-xml "$THIS_DIR/test-reports/report.xml" \
        --cov-fail-under "$MINIMUM_TEST_COVERAGE_PERCENT" || ((PYTEST_EXIT_STATUS+=$?))

    mv coverage.xml "$THIS_DIR/test-reports/" || true
    mv htmlcov "$THIS_DIR/test-reports/" || true
    mv .coverage "$THIS_DIR/test-reports/" || true
    return $PYTEST_EXIT_STATUS
}

function test:wheel-locally {
    deactivate || true
    rm -rf test-env || true
    uv venv test-env --python 3.11.8
    source test-env/bin/activate
    clean || true
    uv pip install build pytest pytest-cov
    build
    uv pip install ./dist/*.whl
    test:ci
    deactivate || true
}

function serve-coverage-report {
    python -m http.server --directory "$THIS_DIR/test-reports/htmlcov/" 8000
}

function build {
    python -m build --sdist --wheel "$THIS_DIR/"
}

function release:test {
    lint
    clean
    build
    publish:test
}

function release:prod {
    release:test
    publish:prod
}

function publish:test {
    try-load-dotenv || true
    twine upload dist/* \
        --repository testpypi \
        --username=__token__ \
        --password="$TEST_PYPI_TOKEN"
}

function publish:prod {
    try-load-dotenv || true
    twine upload dist/* \
        --repository pypi \
        --username=__token__ \
        --password="$PROD_PYPI_TOKEN"
}

function clean {
    rm -rf dist build coverage.xml test-reports
    find . \
      -type d \
      \( \
        -name "*cache*" \
        -o -name "*.dist-info" \
        -o -name "*.egg-info" \
        -o -name "*htmlcov" \
      \) \
      -not -path "*env/*" \
      -exec rm -r {} + || true

    find . \
      -type f \
      -name "*.pyc" \
      -not -path "*env/*" \
      -exec rm {} +
}

function try-load-dotenv {
    if [ ! -f "$THIS_DIR/.env" ]; then
        echo "no .env file found"
        return 1
    fi

    while read -r line; do
        export "$line"
    done < <(grep -v '^#' "$THIS_DIR/.env" | grep -v '^$')
}

function help {
    echo "$0 <task> <args>"
    echo "Tasks:"
    compgen -A function | cat -n
}

TIMEFORMAT="Task completed in %3lR"
time ${@:-help}
