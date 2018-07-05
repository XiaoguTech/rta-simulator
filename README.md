# 数据集说明
## uci
### house hold power
[数据集地址](http://archive.ics.uci.edu/ml/datasets/Individual%20household%20electric%20power%20consumption)

### gas sensor
[数据集地址](http://archive.ics.uci.edu/ml/datasets/Gas+sensors+for+home+activity+monitoring)

## nasa
### nasa algae
[数据集地址](https://ti.arc.nasa.gov/dev/tech/dash/groups/pcoe/prognostic-data-repository/publications/#algae)

### nasa battery aging
[数据集地址](https://ti.arc.nasa.gov/dev/tech/dash/groups/pcoe/prognostic-data-repository/publications/#battery)

# 配置文件说明

* tag_keys:
每一行代表一个tag_key
```
tag_keys=metric place
```

* tag_values:
会生成两行influxdb数据，split_symbol分割，默认分号
```
tag_values=voltage xx;global xx
```

* field_keys:
```
field_keys=Voltage Global
```

* field_values,$1代表第1列（无第0列），#10.0代表立即数， 同一行的数据用空格分割，不同行的数据用`split_symbol`分割，保证行数与tag_values对应，每行数据数与field_keys对应
```
field_values=$1 $3;$4 $6;#10 #11
```

* src 为待替换的字符，一组字符使用空格分割
* dest 为替换的目标字符
* fromline 为从第几行开始读，2为第二行开始，没有第0行。
Global_active_power;Global_reactive_power;Voltage;Global_intensity;Sub_metering_1;Sub_metering_2;Sub_metering_3

### downsampling的相关设置
* retention policy name: 空格分隔，第一项为默认存储策略，第二项为一级归档
* retention policy : 与名字一一对应，空格分割，为时长，如1周为1w
* continuous query name: 空格分割，与retention policy一一对应，
* continuous query interval: 查询间隔。

* 还没做的
1. 区分field values
