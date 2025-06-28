# 🌳 Welcome to Rebecca Lain's missing tree API

## 🗣️ Context sharing

- EPSG:32734 = UTM Zone 34S (metric)
- EPSG: 4326 = is a geographic coordinate system that uses latitude and longitude to define locations on Earth (lat and long)

## ⬇️ Things to install

- Docker (For Mac)[https://docs.docker.com/desktop/setup/install/mac-install/]


## 👩‍💻 Running locally

Please follow these important first steps:

1. Clone this repository
2. Set up your local `env` file.
3. Run $ make build
4. Then you can spin up the container and execute the handler using $ make run-handler. This will:
  a) Spin up /tmp/tree_gaps_map.html for a quick visualisation of the data to make building easier

Addition commands:
• Exiting a docker container $ exit
• To see python packages intalled on the running container $ pip list


# Infrastructure and Environment variable set up

This middleware runs on the `ProServices Production` account, ID: 706927447862. Please make sure you have configured an AWS profile locally with this name.

## Adding environment variables to serverless and AWS Parameter Store

In order to prevent environment variables being overwritten while deploying updates to the lambda functions with serverless we need to store the values in the AWS Parameter Store.

1. Open AWS and navigate to the AWS SSM Parameter Store.
2. The variables are defined on the serverless.yml file under the provider.environment path, example: `${ssm(env:AWS_REGION_VARIABLE):/middleware-client-bulk-updater/sls:stage/env/ROOT_API_KEY}`
3. To add/update a parameter to the Parameter Store with the AWS CLI use the following command,

```bash
aws ssm put-parameter --name /middleware-client-bulk-updater/uat/env/{{NAME OF VARIABLE}} --value staging --type {{TYPE}} --overwrite --profile ProServicesProduction --region af-south-1

Example:


aws ssm put-parameter --name /middleware-client-bulk-updater/uat/env/NODE_ENV --value uat --type String --overwrite --profile ProServicesProduction --region af-south-1
aws ssm put-parameter --name /middleware-client-bulk-updater/uat/env/AWS_REGION_VARIABLE --value af-south-1 --type String --overwrite --profile ProServicesProduction --region af-south-1


```

## Deploying to AWS for testing

The [serverless-plugin-typescript](https://www.serverless.com/plugins/serverless-plugin-typescript) automatically ensures that your typescript code compiles before deploying your code, so you don't have to run the `tsc` command manually.

To deploy, run `npm run deploy:dev` and enter the name of the AWS account to deploy to. To use the default account, just press enter.

To remove the app run `npm run remove:dev`.

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

We use `semaphore` to deploy middleware.

🚨 Please ensure to update the AWS_REGION_VARIABLE and AWS_ACCOUNT values on the semaphore files if not using the following:

- `AWS_REGION_VARIABLE`: af-south-1
- `AWS_ACCOUNT`: ProServices Production account
