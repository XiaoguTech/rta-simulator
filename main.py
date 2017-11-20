import os
import argparse
import sys
import time
import requests
import time
from functools import reduce

log = sys.stdout.write
error = sys.stderr.write

class Config:
    def __init__(self, download_url, download_file, result_file, \
                    tag_keys, tag_values, field_keys, field_values, split_symbol=';', src='?', dest='0.000', fromline = 1,\
                    batch_size=1, start_time=None, interval=10,
                    hosts='https://twinpines-9429794e.influxcloud.net:8086', database='house_data', username='xiaogu', password='123q456w', measurement='house'):
        self.download_url = download_url
        self.download_file = download_file
        self.result_file = result_file
        self.split_symbol = split_symbol
        
        self.tag_keys = tag_keys.split(' ')
        self.tag_values = tag_values.split(',')
        self.field_keys = field_keys.split(';')
        self.field_values_pos = [res[1:] for res in field_values.split(' ')]
        self.src = src
        self.dest = dest
        self.fromline = fromline

        self.batch_size = batch_size
        self.start_time = start_time
        self.interval = interval

        self.hosts = hosts
        self.database = database
        self.measurement = measurement
        self.username = username
        self.password = password

class Simulator:
    def __init__(self, config):
        self.config = config

    def download(self):
        os.system("wget " + self.config.download_url)
    
    def unzip(self):
        file_name = self.config.download_url.split('/')[-1]
        log(file_name)
        suffix = file_name.split('.')
        if suffix[-1] == 'zip':
            os.system("unzip -o " + file_name)
        else:
            pass
    
    def process(self):
        protocol_format = "%s,{tags} {fields}" % self.config.measurement
        tags = []
        # per line tag
        for tag_value in self.config.tag_values:
            tag_values = tag_value.split(' ')
            tags.append( reduce(lambda x, y: x+'%s=%s,' % (y[0], y[1]), list(zip(self.config.tag_keys, tag_values)), '') )

        with open(self.config.result_file, 'w') as writer:
            with open(self.config.download_file) as reader:
                for i in range(self.config.fromline):
                    reader.readline()
                
                for line in reader:
                    values = line.split(self.config.split_symbol)
                    fields = reduce(lambda x, y: x+'%s=%s,' % (y[0], values[int(y[1])-1]), list(zip(self.config.field_keys, self.config.field_values_pos)), '')[:-1]
                    
                    # it should be a loop
                    for tag in tags:
                        line_data = protocol_format.format(tags=tag[:-1], fields=fields).replace(self.config.src, self.config.dest)
                        log(line_data)
                        writer.write(line_data)

    def upload(self):
        upload_url = '%s/write?db=%s&u=%s&p=%s' % (self.config.hosts, self.config.database, self.config.username, self.config.password)
        with open(self.config.result_file) as reader:
            count = 0
            text = ''
            for line in reader:
                if count == self.config.batch_size:
                    response = requests.post(upload_url, data=text.encode('utf-8'))
                    log(str(response) + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
                    time.sleep(self.config.interval)
                    count = 0
                    text = ''
                else:
                    count += 1
                    text += line
                                

class Director:
    @staticmethod
    def Start(simulator):
        simulator.download()
        simulator.unzip()
        simulator.process()
        simulator.upload()

def get_env(key, default=None):
    env = os.getenv(key)
    if env:
        return env
    else:
        return default

if __name__ == "__main__":
    download_url = get_env('RTA_URL', 'http://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip')
    download_file = get_env('RTA_FILE', 'household_power_consumption.txt')
    result_file = get_env('RTA_RESULT', 'house.influxdb')
    tag_keys = get_env('RTA_TAG_KEYS', 'metric')
    tag_values = get_env('RTA_TAG_VALUES', 'ljz')
    field_keys = get_env('RTA_FIELD_KEYS', 'Global_active_power;Global_reactive_power;Voltage;Global_intensity;Sub_metering_1;Sub_metering_2;Sub_metering_3')
    field_values = get_env('RTA_FIELD_VALUES', '$3 $4 $5 $6 $7 $8 $9')
    config = Config(download_url=download_url, download_file=download_file, result_file=result_file, tag_keys=tag_keys, tag_values=tag_values, \
                    field_keys=field_keys, field_values=field_values)
    Director.Start(Simulator(config))
    
