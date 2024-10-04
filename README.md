# AIM-py 

AIM's python code repository

## Setup

1. Clone the repo

```
git clone https://github.com/mlibrary/aim-py.git
cd aim-py
```

2. In the terminal, run the `init.sh` 
```
./init.sh
```
This will:

* set up the initial environment variables file
* build the docker image
* install the python dependencies
* Set up the database for digifeeds

`./init.sh` can be run more than once. 
  
3. Edit `.env` with actual environment variables

4. If using VSCode for editing, the repository is set up for use with dev containers. You will have to rebuild the container in there. 

5. In the app container, use `poetry shell` to enable the virtual environment. Otherwise use:
```
 docker compose run --rm app poetry run YOUR_COMMAND
```

## Projects

### Digifeeds

Digifeeds code is in the `aim/digifeeds` folder. The `database` folder has the code for the database and its web API. 

#### Database
To run database migrations:
```
cd aim/digifeeds/database
alembic upgrade heads
```
The alembic migrations live in the `aim/digifeeds/database/migrations` folder.

#### Web API for the Database
The docker compose `api` service runs the application on port 8000.

Assuming docker compose is up for the `aim-py` repository, in the browser go to:
http://localhost:8000/docs to work with the API.

#### CLI

The digifeeds CLI is in the file `aim/cli/digifeeds.py` It has a mix a database
operations and application operations.

## Tests

To run tests:
```
docker compose run --rm app poetry run pytest
```
