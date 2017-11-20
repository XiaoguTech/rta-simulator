# 配置文件说明

* tag_keys:
每一行代表一个tag_key
```
tag_keys=metric place
```

* tag_values:
会生成两行influxdb数据，逗号分割
```
tag_values=voltage xx,global xx
```

* field_keys:
```
field_keys=Voltage Global
```

* field_values:
```
field_values=$1 $3
```

Global_active_power;Global_reactive_power;Voltage;Global_intensity;Sub_metering_1;Sub_metering_2;Sub_metering_3
