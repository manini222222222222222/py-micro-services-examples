[中文](README.md) | [English](README.EN.md)
# Python Web example of microservice project

Integrated with common web project components, providing basic web functionality
- scheduled tasks: 
  - [xxl-job](https://github.com/xuxueli/xxl-job)
  - [pyxxl](https://github.com/fcfangcc/pyxxl)
- configuration center: [Nacos](https://github.com/nacos-group/nacos-sdk-python)
- database: [MySQL / sqlalchemy](https://github.com/sqlalchemy/sqlalchemy)
- web framework: [FastAPI](https://github.com/fastapi/fastapi)
- log (integrated trace id): [loguru](https://github.com/Delgan/loguru)
- third party notification component: [Enterprise Wechat](https://developer.work.weixin.qq.com/document/path/99110)

# Project Structure

```
root/
├── app/                         # core application code directory
│   ├── common/                  # universal module
│   │   ├── const.py             # enumeration / constant common class
│   │   ├── logger.py            # system log configuration
│   │   └── utils/               # tool collection
│   ├── config/                  # system configuration module
│   │   ├── db/                  # database access layer and data storage
│   │   ├── trace_/              # log link configuration class
│   │   ├── nacos_config.py      # nacos configuration center class
│   │   └── xxl_job_config.py    # xxl-job configuration class
│   ├── nacos_/                  # nacos configuration center module
│   │   └── controller.py        # nacos external api
│   ├── demo_business/           # demo module
│   │   ├── controller.py        # demo business external api
│   │   └── service.py           # demo business logic implementation
│   ├── web/                     # web service module
│   │   └── server.py            # web service startup entrance
│   └── xxl_job/                 # XXL-JOB task scheduling
│       ├── tasks/               # XXL-JOB specific task implementation
│       └── scheduler_server.py  # xxl-job task scheduling service startup portal
├── docker/                      # docker configuration file directory
├── log/                         # log file directory
├── xx_log/                      # XXL-JOB log file directory
├── config_prod.yaml             # production environment configuration file 
│                                # (Just connect to the configuration file of Nacos, the specific configuration information is configured in Nacos)
├── config_uat.yaml              # uat environment configuration file (consistent with the function of config_prod.yaml)
├── config_test.yaml             # test environment Configuration File (consistent with the function of config_prod.yaml)
└── requirements.txt             # project dependency package list
```

# Directory Explanation

## [app](app) (core application code directory)
```
This is the root application directory of the project, which contains all core business logic modules.
```

### [common](app/common) (universal module)
```
Contains the basic components of the project, such as enumeration classes, utility classes, logs, etc.
```

subdirectory description:
- `utils`: tool collection
  - [wechat_msg_util.py](app/common/utils/wechat_msg_util.py): enterprise wechat messaging tools

### [config](app/config) (system configuration module)
```
Contains various basic configurations of the project, such as database connection, Nacos configuration, XXL-JOB configuration, etc.
```

subdirectory description:
- `db`: database related configuration
  - [db_mysql.py](app/config/db/db_mysql.py): enterprise wechat messaging tools
- `trace_`: link tracing configuration set
  - [trace_config.py](app/config/trace_/trace_id_config.py): web request link tracing middleware
  - [request_context.py](app/config/trace_/request_context.py): request context object
- [nacos_config.py](app/config/nacos_config.py): Nacos configuration class
- [xxl_job_config.py](app/config/xxl_job_config.py): XXL-JOB configuration class

### [demo_business](app/demo_business) (example business module)
```
To showcase the example modules of the project structure, you can refer to the example modules for self expansion.
```

Subdirectory Description: (Refer to MVC Framework)
- [controller.py](app/demo_business/controller.py): Example Business Unified External Exposure Interface (RESTful API)
- [service.py](app/demo_business/service.py):  example business specific business implementation

### [nacos_](app/nacos_) (nacos business module)
```
Due to not using the automatic monitoring configuration refresh logic provided by Nacos official, I implemented manual refresh logic myself
(The official logic involves multiprocessing logic, which is not very convenient to use)
```

Subdirectory Description: (Refer to MVC Framework)
- [controller.py](app/demo_business/controller.py): The external refresh interface (RESTful API) provided by Nacos


### [web](app/web) (web service module)
```
provide restful api interface
```

subdirectory description:
- [server.py](app/web/server.py): web server entrance, using FastAPI framework

### [xxl_job](app/xxl_job) (task scheduling module)
```
Integrate XXL-JOB distributed task scheduling platform.
```

subdirectory description:
- `tasks`: specific task implementation
  - [config_task.py](app/xxl_job/tasks/config_task.py): System configuration scheduled tasks (such as nacos refresh)
- [scheduler_server.py](app/xxl_job/scheduler_server.py): Scheduling server, responsible for registering and executing tasks

## [docker](docker) (docker configuration)
```
Contains the configuration files required for building Docker images.
```

document description:
- [dockerfile-server](docker/dockerfile-server): web service docker image build file
- [dockerfile-job](docker/dockerfile-job): XXL-JOB scheduling service Docker image construction file

## [log](log) (log file)
```
Store log files generated during project runtime, named by date.
```

## [xxl_log](xxl_log) (xxl-job log file)
```
Store the log files generated by xxl-job runtime, named by date.
```

## Configuration file

### [config_prod.yaml](config_prod.yaml)
```
The production environment configuration file has configured the relevant parameters of the Nacos configuration center.
```

### [config_uat.yaml](config_uat.yaml)
```
UAT environment configuration file, configured with relevant parameters of Nacos configuration center.
```

### [config_test.yaml](config_test.yaml)
```
The TEST environment configuration file has configured the relevant parameters of the Nacos configuration center.
```