# AIM-py

AIM's python code repository

## Setup

1. Clone the repo

    ```bash
    git clone https://github.com/mlibrary/aim-py.git
    cd aim-py
    ```

2. In the terminal, run the `init.sh`

    ```bash
    ./init.sh
    ```

    This will:
    * set up the initial environment variables file
    * set up the rclone config with the example file
    * build the docker image
    * install the python dependencies
    * Set up the database for digifeeds

    `./init.sh` can be run more than once.
  
3. Edit `.env` with actual environment variables

4. Edit `.config/rclone/rclone.conf` with your actual values

5. If using VSCode for editing, the repository is set up for use with dev containers. You will have to rebuild the container in there.

6. In the app container, use `poetry shell` to enable the virtual environment. Otherwise use:

```bash
 docker compose run --rm app poetry run YOUR_COMMAND
```

## Structure

The codebase has the following structure high level structure:

```text
.
├── aim/
│   ├── cli/
│   │   ├── my_project.py
│   │   └── __init__.py
│   ├── my_project/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── other_file_for_project.py
│   ├── services.py
│   └── __init__.py
└── tests/
    ├── fixtures/
    │   └── my_project/
    │       ├── fixture1.json
    │       └── fixture2.yaml
    ├── cli/
    │   ├── test_my_project.py
    │   └── __init__.py
    ├── my_project/
    │   ├── test_main.py
    │   ├── test_other_file_for_project.py
    │   └── __init__.py
    └── conftest.py
```

`aim` is the directory where all of the business logic lives. Every directory and subdirectory within `aim` has an `__init__.py` file so that python imports work properly.

In this example there is an application/product/project called `my_project`. `my_project` has several subdirectories and files with related code.

One is `aim/my_project`. That's where the application code lives. Code within `my_project` can be arranged however makes sense for the project. Further subjectories within `my_project` are fine if they help make the project code easier to think about and work with.

If the application is a subcommand for the AIM cli then code related to the cli goes in `cli/my_project`.

`aim/services.py` has configuration objects. It provides an object called `S` that has things like environment variable values or database connection strings. Configuration for all projects goes in here. Use `my_project_` as a prefix if there are concerns about name collisions. `S` is a `NamedTuple` so that these objects show up in code completion in IDEs like vscode.

Tests go in `tets/my_project`. Ideally the folder and file structure in `tests/my_project` should mirror `aim/my_project`. This way it's easy to figure out where relevant tests should live. Prefix tests files with `test_` so that `pytest` picks up the tests. If there are fixture files for your tests, put them in `fixtures/my_project`. This should make it easier to tell what tests the fixtures are for. As with the code in `aim` every folder in tests except for `fixtures` needs to have an `__init__.py` file.

`tests/conftest.py` has test configuration that's available for all tests for all projects. For now it has code to handle setting up the `digifeeds` database and its API for tests.

## Projects

### Digifeeds

Digifeeds code is in the `aim/digifeeds` folder. The `database` folder has the code for the database and its web API.

#### Database

To run database migrations:

```bash
cd aim/digifeeds/database
alembic upgrade heads
```

The alembic migrations live in the `aim/digifeeds/database/migrations` folder.

#### Web API for the Database

The docker compose `api` service runs the application on port 8000.

Assuming docker compose is up for the `aim-py` repository, in the browser go to:
<http://localhost:8000/docs> to work with the API.

#### CLI

The digifeeds CLI is in the file `aim/cli/digifeeds.py` It has a mix a database
operations and application operations.

To use the CLI, on the command line run:

```bash
docker compose run --rm app poetry run aim digifeeds --help
```

This will show the commands available for the digifeeds cli applciation.

## Tests

To run tests:

```bash
docker compose run --rm app poetry run pytest
```

### Connecting to the internet is blocked for tests

We are using `pytest-socket` to block actually http requests in tests.

To mock http requests, use the `responses` library. Don't forget to put the `@responses.activate` decorator above tests that use `responses`.

Blocking requests occurs because in `pyproject.toml` we've set `pytest` to run with the `--disable-socket` option. The `--allow-unix-socket` option allows connection to our test database.

### Mocking objects

`pytest-mock` is included in the project, so the `mocker` fixture is available in all tests.

### Test Coverage

`pytest-cov` is used for test coverage information. On every run of `pytest` there's a summary of coverage in the terminal, and an html report in the folder `htmlcov`. This is configured with the following `pytest` options in `pyproject.toml`: `--cov=aim --cov-report=html --cov-report=term:skip-covered`

### Using the `digifeeds` database

`tests/conftest.py` sets up a couple of `pytest` fixtures for working with the `digifeeds` database.

One is `db_session` which provides a `sqlalchemy` database session object. You can commit changes in the session and they will only last for the duration of thests.

The other is `client`, which provides a `fastapi` `TestClient` that knows about the `db_session` fixture.

### CLI tests

The `typer` `CliRunner` works without special modification. This is a good place to put in some integration tests since this is the entrypoint for using the application. That said, it's ok to mock out things like database calls.

## Documentation

Documentation lives in the `/docs` directory.

[Sphinx](https://www.sphinx-doc.org) is used to generate the documentation website.

The [documentation site](https://mlibrary.github.io/aim-py/) is built with a Github Action on each push to main.

We are using [Google style docstrings](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings).

In development the documentation should build automatically and be available at <http://localhost:8888/>

## Deployment

### Production Docker image

The production Docker image of `aim-py` uses `poetry` to generate a `requirements.txt` file of the dependencies necessary to run the application in produciton. In a separate step that `requirements.txt` file is copied into the container and then installed with `pip`.

That means the project is used differently in production than in development. In development you need to run `poetry shell` to get enable the virtual environment. If you have the virtual environment activated you can run commands like `aim --help` because `pyproject.toml` knows about the `aim` cli.

In production, you do not need to enable a virtual environment because all of the dependencies are installed globally in the image. To run the cli you need to run `python -m aim --help` to get the same help menu.

### Github Actions Workflows

This repository has the following actions related to deployment:

`build-unstable` takes a git commit hash and builds an `aim-py-unstable` image with a tag of the commit hash.

`manual-deploy-workshop` does what `build-unstable` does, and then sends a message to the `aim-kube` repository to update the appropriate workshop kuberentes cluster related files with the address of this new `aim-py-unstable` image. In this case it updates `environments/digifeeds/workshop/app-image.txt` in `aim-kube`.

`build-main` is the same as `manual-deploy-workshop` except it happens automatically on pushes to the `main` branch where the tests have passed.

`build-deploy-on-release` runs when a new github release is made. It builds an `aim-py` image with the same tag as the release tag. Then it sends a message to the `aim-kube` repository to update the appropriate production image files. In this case it updates `environments/digifeeds/workshop/app-image.txt`

`manual-deploy-production` does the same thing as `build-deploy-on-release` but a tag is input manually. This would be used for reverting to older images.
