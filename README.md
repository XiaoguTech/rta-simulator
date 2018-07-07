# 目录结构
```text
├── Dockerfile
├── grafana # import grafana dashboard which is using influxdb datasources
├── influxdb # influxdb inserting scripts
├── kapacitor_udf
├── LICENSE
├── main.py # influxdb inserting scripts demo
└── udf_3d_printer.py
```

# 使用顺序
0. 启动influxdb与grafana服务
1. 先使用`influxdb`目录中的脚本插入数据
2. 使用`grafana`目录中的脚本导入对应数据源的`dashboard`