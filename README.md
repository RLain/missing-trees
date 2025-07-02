# 🌳 Welcome to Rebecca Lain's missing tree API

This repo is an API that takes in an orchard_id param and returns coordinates for missing trees located on the farm.

## 🗣️ Context sharing

- EPSG stands for European Petroleum Survey Group and is a scientific organization that maintains a geodetic parameter database with standard codes
- EPSG:32734 = UTM Zone 34S (metric) [Source)](https://epsg.io/32734)
- EPSG: 4326 = is a geographic coordinate system that uses latitude and longitude to define locations on Earth (lat and long) [Source](https://epsg.io/4326)
- geodetic -> geodesy noun ge·​od·​e·​sy jē-ˈä-də-sē : a branch of applied mathematics concerned with the determination of the size and shape of the earth and the exact positions of points on its surface and with the description of variations of its gravity field

## ⬇️ Things to install (For Mac)

- [Docker](https://docs.docker.com/desktop/setup/install/mac-install/)
- SAM set up. Example using [brew](https://brew.sh/)
  - a. $ brew tap aws/tap
  - b. $ brew install aws-sam-cli

## 🔢 Things to config _(if applicable)_

- Head to `src/config/settings.py` to see configuration options

## 👩‍💻 Running locally

Please follow these important first steps:

1. Clone this repository
2. ~Set up your local `env` file. Use the `.env.sample` to see the required structure.~ Ignore: Sempahore & Serverless not working. 
3. Open docker on your desktop
4. $ make build
6. Run $ make run
7. Once you see `* Running on all addresses (0.0.0.0)` then in a separate terminal run 
```bash
curl -H "Authorization: Bearer your-bearer-token" http://localhost:3000/api/orchards/your-orchard-id/missing-trees
```
8. Once finished CMD + Q to end sam and then run $ make clean


Additional commands:
- Exiting a docker container $ exit
- To see python packages intalled on the running container $ pip list

## Linting

1. First run $ make build
2. Then run $ make lint

## Testing

### Unit tests

Unit tests are located in the `src/tests/unit` folder.
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
