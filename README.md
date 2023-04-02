# Doru

[![Build](https://github.com/masa-08/doru/actions/workflows/build.yml/badge.svg)](https://github.com/masa-08/doru/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/masa-08/doru/branch/main/graph/badge.svg?token=261D9I3JLF)](https://codecov.io/gh/masa-08/doru)

**A tiny command line tool for  regular investment of cryptocurrencies on exchanges around the world.**

This module provides a simple command line interface to make regular investments in various
cryptocurrency pairs that are traded on different exchanges around the world.

## Getting Started

### Installation
Install by [pipx](https://pypa.github.io/pipx/):
```shell
pipx install doru
```

### Example
Add a credential:
```shell
$ doru cred add

# interactive prompts
Exchange: binance
Key: hogehoge
Secret: hogehoge
```

Add a regular investment task:
```shell
$ doru add

# interactive prompts
Exchange: binance
Symbol: BTC/USDT
Cycle (Daily, Weekly, Monthly): Daily
Time [00:00]: 12:00
Amount: 10000
Start [True]: True
```

Display a list of regular investment tasks:
```shell
$ doru list
ID            Symbol      Amount  Cycle    Next Invest Date    Exchange    Status
------------  --------  --------  -------  ------------------  ----------  --------
JtynLAJL74A5  BTC/USDT     10000  Daily    2023-03-20 12:00    binance     Running
Gaye3E8PIJkl  ETH/BTC       0.01  Weekly   Not Scheduled       kraken      Stopped
PfavioXafCL1  ETH/USDC     20000  Monthly  2023-04-01 00:00    kucoin      Running
```


## Usage
### Credential
In order to purchase cyrptocurrencies on an exchange, you will need an API key and secret that
authorizes you to purchase cryptocurrencies. The procedure for issuing them varies from exchange to
exchange, so please check the website of the exchage you want to use.

The following shows how to register or delete the API key and secret in this module.

### Add credential
Add interactively:
```shell
$ doru cred add

Exchange: <exchange name>
Key: <API key>
Secret: <API secret>
```

Add with options:
```shell
$ doru cred add -e <exchange name> -k <API key> -s <API secret>
```

### Remove credential
Remove interactively:
```shell
$ doru cred remove

Exchange: <exchange name>
```

Remove with options:
```shell
$ doru cred remove -e <exchange name>
```

### Cryptocurrency task

How to add, start, stop and delete tasks to buy cryptocurrency is described below.

### Add a task to buy cryptocurrencies regularly
The following command is used to add a regular cryptocurrency investment task.
```shell
$ doru add
```

The following options can be specified.


|Option|Detail|Available values|Default value|Required|
|:----|:----|:----|:----|:----|
|-e, --exchange|Exchange name <br>e.g. binance, coinbase|Depends on [ccxt](https://github.com/ccxt/ccxt#supported-cryptocurrency-exchange-markets)|-|✅|
|-s, --symbol|Symbol name <br>e.g. BTC/USDT, ETH/BTC|Depends on the exchange you use|-|✅|
|-c, --cycle|Purchase cycle|Daily, Weekly, Monthly|-|✅|
|-a, --amount|Per purchase amount <br>e.g. Specify 10,000 if you want to buy 10,000 USDT worth of BTC/USDT each time.|more than 0|-|✅|
|-w, --weekday|Day of the week to buy crypto <br>Valid only when the cycle is weekly.|Sun, Mon, Tue, Wed, Thu, Fri, Sat|Sun| |
|-d, --day|Date to buy crypto <br>Valid only when the cycle is monthly.|from 1 to 28|1| |
|-t, --time|Time to buy crypto <br>`hh:mm` format|00:00 ~ 23:59|00:00| |
|--start|Whether to start periodic purchase at the same time the task is added. <br>If false, cyrpto won't be purchased until you explicitly start the task.|True / False|True| |


Daily task:

Add interactively:
```shell
$ doru add

# interactive prompts
Exchange: <exchange name>
Symbol: <symbol name>
Cycle (Daily, Weekly, Monthly): Daily
Time [00:00]: <time>
Amount: <currency amount>
Start [True]: <True or False>
```

Add with options:
```shell
$ doru add -e <exchange name> \
           -s <symbol name> \
           -c Daily \
           -t <time> \
           -a <currency amount>
```


Weekly task:

```shell
$ doru add

# interactive prompts
Exchange: <exchange name>
Symbol: <symbol name>
Cycle (Daily, Weekly, Monthly): Weekly
Weekday (Sun, Mon, Tue, Wed, Thu, Fri, Sat) [Sun]: <weekday>
Time [00:00]: <time>
Amount: <currency amount>
Start [True]: <True or False>
```

Monthly task:

```shell
$ doru add

# interactive prompts
Exchange: <exchange name>
Symbol: <symbol name>
Cycle (Daily, Weekly, Monthly): Monthly
Day [1]: <day>
Time [00:00]: <time>
Amount: <currency amount>
Start [True]: <True or False>
```


### Check the list of tasks

```shell
$ doru list
ID            Symbol      Amount  Cycle    Next Invest Date    Exchange    Status
------------  --------  --------  -------  ------------------  ----------  --------
JtynLAJL74A5  BTC/USDT     10000  Daily    Not Scheduled       binance     Stopped
Gaye3E8PIJkl  ETH/BTC       0.01  Weekly   2023-03-26 09:00    kraken      Running
PfavioXafCL1  ETH/USDC     20000  Monthly  2023-04-01 00:00    kucoin      Running
```

### Start tasks

You can start (schedule) the purchase of cyrptocurrency by specifying the ID of the task.

Multiple IDs can be specified by separating them with a space.

The IDs can be found in the result of the command `doru list`.

```shell
$ doru start <ID1> <ID2> ....
```

If you want to start all tasks, you can use the `--all` option to start all tasks.

```shell
$ doru start --all
```

### Stop tasks

You can stop the purchase of cyrptocurrency by specifying the ID of the task.

Multiple IDs can be specified by separating them with a space.

The IDs can be found in the result of the command `doru list`.

```shell
$ doru stop <ID1> <ID2> ....
```

If you want to stop all tasks, you can use the `--all` option to stop all tasks.

```shell
$ doru stop --all
```

#### Remove a task

```shell
$ doru remove <ID>
```

### Daemon

This tool is handled by the daemon process running behind the command line interface.

It is not normally necessary to start and stop the daemon manually.
However, if you need to restart it after an unexpected error,
or if you want to edit and reload a configuration file directly, this interface is useful.

### Daemon Process Up
```shell
$ doru daemon up
```

### Daemon Process Down
```shell
$ doru daemon down
```


## Environmental variables

The following environmental variables are used in this module.

The Values can be changed to suit your environment.

|Variable name|Detail|Default value|
|:----|:----|:----|
|DORU_SOCK_NAME|The path of the UNIX domain socket to which the daemon process will bind|~/.doru/run/doru.sock|
|DORU_PID_FILE|The path of the daemon's PID file|~/.doru/run/doru.pid|
|DORU_CREDENTIAL_FILE|Credentials file path|~/.doru/credential.json|
|DORU_TASK_FILE|File path to store information about cryptocurrency buying tasks.|~/.doru/task.json|
|DORU_LOG_FILE|Log file path|~/.doru/log/doru.log|
|DORU_TASK_LIMIT|Maximum number of tasks that can run simultaneously. <br>(not the maximum number of tasks that can be added)|50|


## Specification

- This module depends on the [ccxt](https://github.com/ccxt/ccxt) library.
- Supported exchanges
  - Check [ccxt](https://github.com/ccxt/ccxt).
  - If you enter an unsupported exchange name, you will get an error message that indicates which exchanges are supported.
- Supported symbols
  - Check the exchange documentation.
  - If you enter an unsupported symbol, you will get an error message which lists the symbols supported by the exchange.
- Support only SPOT type
- The order price is basically the bid price obtained from the exchange API. Some exchanges (or symbols) do
  not provide bid prices, in which case the closing price of the last ticker is used.
- Wait 10 minutes for each order to execute.
- If the order is not executed within 10 minutes, it will be canceled and retried (up to 5 retries).
- However, to prevent duplicate orders, an order will not be retried even if it does not execute in the following cases.
  - If the order cancellation fails
  - If the order status cannot be retrieved and is unknown (for example, due to network problems or maintenance)


## Tests

After cloning the repository, execute the following command.
```shell
$ tox
```

NOTE:

Some tests send requests to real exchanges, which may cause the test to fail due to exchange maintenance or other reasons.
In the future, the dependency on exchanges will be removed using mock.

## Contributing

Welcome issues and pull requests for reasons such as not knowing how to use this module,
finding a bug, or suggesting a new feature.
