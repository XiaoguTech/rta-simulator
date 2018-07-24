# 创建日期
20180718

last updated：20180724
# 树莓派
- [x] 读取温度的实验对应教程实验26

- [ ] 使用ATK-S1216获得gps数据实验

## 连接机器
机器在局域网内的ip为`192.168.1.126`

用户名：`pi`

超级用户名：`root`

密码均与用户名同名

## 读取温度实验
使用的模块包括：DS18B20数模转换器与一个热敏数字温度传感器

实验代码位于`/home/pi/Documents/Demo/e26`目录下，分为`c`版本与`python`版本
### 接线
各组件地线与火线正常接线（**注意：接线时先接地线，拔线时最后拔地线**）
1. 热敏数字温度传感器`out`接`GPIO`板的`G4`管脚
2. DS18B20数模转换器的`SCL`与`SDA`管脚对应接`GPIO`板的`SCL`与`SDA`管脚

### `c`版本
`cd c`后，需要注意一下DS18B20通过总线传输数据，所以还需要注意一下代码中的地址是否正确，执行`gcc 26_ds18b20.c -o temp -lwiringPi`进行编译链接后，使用`./temp`执行文件得到输出。

### `python`版本
需要安装两个依赖包：
- `wiringpi`（gpio板子的python wrapper）
- `requests`（提供web请求方法）

python版本中，需要注意一下，python中实现了向局域网内某台安装influxdb的机器发送数据的子功能。可以根据需要修改`host_name`（一般出现route didn't match 的错误，需要排查是否ip号错误等）。

可以使用`nohup python temp_uploader.py 2>&1 1>log &`后台运行代码

## 获得GPS实验
使用的模块为`ATK-S1216`（程序目前还有bug，也可能是物理硬件bug）

### 接线
注意：`TXD`与`RXD`脚分别与GPIO的`RXD`和`TXD`管脚连接

### 代码运行
需要安装两个依赖包：
- `serial`（用于操作gpio串口）
- `pynmea2`（用于操作从串口获得的gps原始数据）

需要使用`sudo python gps.py`运行程序，因为读`tty`需要`root`权限。

# grafana可视化
注意数据源的选取，以及对应的表名和字段名

数据的单位为摄氏度`celsius`，在数据库的间隔为`300second(5minute)`
