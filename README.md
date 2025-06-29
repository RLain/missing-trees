# 🌳 Welcome to Rebecca Lain's missing tree API

This repo takes in an orchard_id and returns coordinates for missing trees located on the farm.

## 🗣️ Context sharing

- EPSG stands for European Petroleum Survey Group and is a scientific organization that maintains a geodetic parameter database with standard codes
- EPSG:32734 = UTM Zone 34S (metric) (Source)[https://epsg.io/32734]
- EPSG: 4326 = is a geographic coordinate system that uses latitude and longitude to define locations on Earth (lat and long) (Source)[https://epsg.io/4326]
- geodetic -> geodesy noun ge·​od·​e·​sy jē-ˈä-də-sē : a branch of applied mathematics concerned with the determination of the size and shape of the earth and the exact positions of points on its surface and with the description of variations of its gravity field

## ⬇️ Things to install (For Mac)

- (Docker)[https://docs.docker.com/desktop/setup/install/mac-install/]
- SAM set up. Example using (brew)[https://brew.sh/]
  a. $ brew tap aws/tap
  b. $ brew install aws-sam-cli

## 🔢 Things to config _(if applicable)_

- Head to `src/config/settings.py` to see configuration options

## 👩‍💻 Running locally

Please follow these important first steps:

1. Clone this repository
2. Set up your local `env` file. Use the `.env.sample` to see the required structure.
3. Open docker
4. $ make build_sam - _note to give this a moment, it takes a bit of time to mount the image to SAM. Please wait for the following to finish:_
```bash
Mounting /Users/your_name/Documents/dir_of_the_repo/missing-trees as                       
/tmp/samcli/source:ro,delegated, inside runtime container  
```
5. $ sam validate - this should pass with `is a valid SAM Template`
6. $ make start_api
7. Once you see `* Running on all addresses (0.0.0.0)` then in a separate terminal run $ curl http://localhost:3000/orchard/orchard_id - replace orchard_id

NB: The API is unacceptably slow (sorry). Have patience with ...Finding missing trees. This takes a long ol' time.
```bash
START RequestId: 2944f11c-c41d-42f6-8a41-18999d3c0c7b Version: $LATEST
Reached missing_trees - kicking off asyncio
Setting up AeroboticsAPIClient and invoking API...
** GET : HTTPClient URL: https://api.aerobotics.com/farming/surveys?orchard_id=216269
** GET : HTTPClient URL: https://api.aerobotics.com/farming/surveys/25319/tree_surveys/
Kicking off spatial calculations...
...Creating outer polygon
...Creating inner boundary
...Creating tree polygons
Total input trees: 508
...Finding missing trees
Identified 4 missing trees
Creating orchard map...
Analysing results...
END RequestId: c6d6be20-94b5-4498-b761-1e24614acaa7
REPORT RequestId: c6d6be20-94b5-4498-b761-1e24614acaa7  Init Duration: 1.55 ms  Duration: 241573.03 ms     Billed Duration: 241574 ms      Memory Size: 128 MB     Max Memory Used: 128 MB
```

To run the function directly using docker:
- Run $ make build
- Then you can spin up the container and execute the handler using $ make run-handler. This will:
  a) Spin up /tmp/tree_gaps_map.html for a quick visualisation of the data to make building easier

Additional commands:
• Exiting a docker container $ exit
• To see python packages intalled on the running container $ pip list
• To run serverless container on terminal: $ docker run --rm -it -v "$(pwd):/app" -w /app my-serverless bash
• To check NPM packages intall on container: $ npm list -g --depth=0

## Testing

### Unit tests

Unit tests are located in the `src/tests` folder.
To run unit tests run `$ make test`

You shoud see an outcome similar to:

```bash
============================= test session starts ==============================
platform linux -- Python 3.11.13, pytest-8.4.1, pluggy-1.6.0 -- /usr/local/bin/python3.11
cachedir: .pytest_cache
rootdir: /app
plugins: asyncio-1.0.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 4 items

src/tests/test_*.py::test_missing_trees PASSED                           [ 25%]
src/tests/utils/test_timer.py::test_sleep PASSED                         [ 50%]
src/tests/utils/test_timer.py::test_start_and_elapsed_time_in_ms PASSED  [ 75%]
src/tests/utils/test_timer.py::test_log_elapsed_time_in_ms_logs_message PASSED [100%]

============================== 4 passed in 0.20s ===============================
```

### Integration tests

_To be added_

## Deploying to AWS

_To be finished_

We use `semaphore` to deploy the middleware. The deployment secrets are stored on `https://rlain.semaphoreci.com/` including AWS and Serverless Framwork.
