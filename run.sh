#!/bin/bash

set -e

#####################
# --- Constants --- #
#####################

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
MINIMUM_TEST_COVERAGE_PERCENT=0


##########################
# --- Task Functions --- #
##########################

# install core and development Python dependencies into the currently activated venv
function install {
    uv pip install --editable "$THIS_DIR/[dev]"
}

function run {
    export S3_BUCKET_NAME=some-bucket
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
