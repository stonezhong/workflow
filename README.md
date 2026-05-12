# 目录
* [编码风格](#编码风格)
    * [import的先后次序](#import的先后次序)
* [常见术语](#常见术语)
* [总体设计](#总体设计)

# 编码风格
## import的先后次序
* python系统的package
* 第三方的package
* 本项目的package

# 常见术语

| 名称          | 介绍                    | 解释 |
|---------------|------------------------|------|
| DTO           | Data Transfer Object    | 指一个模型的数据存储内容。 |
| DAO           | Data Access Object      | 它用于加载、查询、删除、保存DTO。 |
| API Model     | 在REST API中用到的模型    | 用于定义REST API的输入和输出的结构 |
| Core Model    | 核心层的模型              |             |
| API Mapper    | 负责在API Model和Core Model之间相互转换 | 这个模块在API层 |


## DTO
Data Transfer Object。指一个模型的数据存储内容。

## DAO
Data Access Object。它用于加载、查询、删除、保存DTO。

# 总体设计

总共分为三层
* API层: 负责处理HTTP请求，调用核心层完成请求。
* 核心层: 负责workflow的商业逻辑，调用数据层来保存，查询
* 数据层: 负责数据的保存和查询。

# API层

# 启动
```bash
uvicorn apis:app
```

# 一些链接
* [Swagger Web UI](http://127.0.0.1:8000/docs)

# 测试temporal
```bash
# 先启动temporal
temporal server start-dev
```

# 一些设计模式
```
你可以从dal.dtos找到全部的DTO类型定义
你可以从dal.daos找到全部的DAO类型定义
```

# 未整理内容
```
# 在调试的时候，可以这么安装
pip install -e /mnt/DATA_DISK/projects/workflow

# 运行worker
python -m zworkflow.executor
```

# 难题答疑
```
问题:
在app.py中，为什么在lifespan中已经初始化了app_config并将其放入app.state.app_config
但是在
workflow_service: WorkflowService = WorkflowService(app.state.app_config)
中却遇到错误？说app.state.app_config不存在?

解答:
workflow_service: WorkflowService = WorkflowService(app.state.app_config)
是在模块加载的时候被执行的，那时，lifespan中的函数尚未被执行。


```