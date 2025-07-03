# 🌳 Welcome to Rebecca Lain's missing tree API

This repo is an API that takes in an orchard_id param and returns coordinates for missing trees located on the farm.

## 🗣️ Context sharing

- EPSG stands for European Petroleum Survey Group and is a scientific organization that maintains a geodetic parameter database with standard codes
- EPSG:32734 = UTM Zone 34S (metric) [Source)](https://epsg.io/32734)
- EPSG: 4326 = is a geographic coordinate system that uses latitude and longitude to define locations on Earth (lat and long) [Source](https://epsg.io/4326)
- geodetic -> geodesy noun ge·​od·​e·​sy jē-ˈä-də-sē : a branch of applied mathematics concerned with the determination of the size and shape of the earth and the exact positions of points on its surface and with the description of variations of its gravity field


## 🔢 Things to config _(if applicable)_

- Head to `src/config/settings.py` to see configuration options

## 👩‍💻 Running locally

Please follow these important first steps:

0. Install [Docker](https://docs.docker.com/desktop/setup/install/mac-install/)
1. Clone this repository
2. Open docker on your desktop
3. Run $ make run
4. Once you see `* Running on all addresses (0.0.0.0)` then in a separate terminal run 
```bash
# For health check
curl http://localhost:3000/health

# For missing-trees check
curl -H "Authorization: Bearer your-bearer-token" http://localhost:3000/api/orchards/your-orchard-id/missing-trees
```
5. Once finished $ make stop


Additional commands:
- Exiting a docker container $ exit
- To see python packages intalled on the running container $ pip list

## 🧹 Linting

1. First run $ make build
2. Then run $ make lint

## 🧪 Testing

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

## 🚀 Deploying to AWS

0. Ensure you have 
  a. Terraform installed. See steps under above "Things to install (For Mac)"
  - $ brew tap hashicorp/tap
  - $ brew install hashicorp/tap/terraform
  b. Have configured your AWS keys locally using $ aws configure
1. Set up /infrastructure/terraform.tfvars using the .example file provided
1. Run $ make terraform_init
2. Run $ make terraform_plan and follow prompts
3. Run $ make terraform_apply and follow prompts

## 🚮 Tearing down on AWS

0. Ensure you have 
  a. Terraform installed. See steps under above "Things to install (For Mac)"
  - $ brew tap hashicorp/tap
  - $ brew install hashicorp/tap/terraform
  b. Have configured your AWS keys locally using $ aws configure
1. Run $ make terraform_destroy and follow prompts