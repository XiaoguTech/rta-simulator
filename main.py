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
    def __init__(self):        
        self.download_url = get_env('RTA_URL', 'http://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip')
        self.download_file = get_env('RTA_FILE', 'household_power_consumption.txt')
        self.result_file = get_env('RTA_RESULT', 'house.influxdb')
        self.split_symbol = get_env('RTA_SPLIT_SYMBOL', ';')

        self.tag_keys = get_env('RTA_TAG_KEYS', 'metric').split(' ')
        self.tag_values = get_env('RTA_TAG_VALUES', 'ljz').split(self.split_symbol)
        self.field_keys = get_env('RTA_FIELD_KEYS', 'Global_active_power;Global_reactive_power;Voltage;Global_intensity;Sub_metering_1;Sub_metering_2;Sub_metering_3').split(self.split_symbol)
        self.field_values = get_env('RTA_FIELD_VALUES', '$3 $4 $5 $6 $7 $8 $9').split(self.split_symbol)
        
        # self.field_values_pos = [res[1:] for res in field_values.split(' ')]
        self.replace_src = get_env('RTA_REPLACE_SRC', '?')
        self.replace_dest = get_env('RTA_REPLACE_DEST', '0.000')
        self.fromline = int(get_env('RTA_FROMLINE', '2')) - 1

        self.batch_size = int(get_env('RTA_BATCH_SIZE', '1'))
        self.start_time = get_env('RTA_START_TIME')
        self.interval = int(get_env('RTA_INTERVAL', '10'))

        self.hosts = get_env('RTA_INFLUX_HOST', 'https://twinpines-9429794e.influxcloud.net:8086')
        self.database = get_env('RTA_DATABASE', 'test')
        self.measurement = get_env('RTA_MEASUREMENT', 'test')
        self.username = get_env('RTA_USERNAME', 'xiaogu')
        self.password = get_env('RTA_PASSWORD', '123q456w')

        self.retention_policy_name = get_env('RTA_RETENTION_POLICY_NAME', 'default_one_day one_week eight_weeks').split(' ')
        self.retention_policy = get_env('RTA_RETENTION_POLICY', '1d 1w 8w').split(' ')
        self.continuous_query_name = 'cq_5m cq_5h'.split(' ')
        self.continuous_query = '5m 5h'.split(' ')

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
                    # -------------------------------------
                    # diff the immediate num and x'th column
                    fields = reduce(lambda x, y: x+'%s=%s,' % (y[0], values[int(y[1])-1]), list(zip(self.config.field_keys, self.config.field_values_pos)), '')[:-1]
                    
                    # every series is a tag
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
        
    def down_sample_config(self):
        base_url = '%s/query?db=%s&u=%s&p=%s&q=' % (self.config.hosts, self.config.database, self.config.username, self.config.password)
        retention_create_format = 'CREATE RETENTION POLICY {} ON ' + self.config.database + ' DURATION {} REPLICATION 1'
        for index, retention in enumerate( list(zip(self.config.retention_policy_name, self.config.retention_policy)) ):
            url = base_url + retention_create_format.format(retention[0], retention[1]) + (' default' if index==0 else '')
            log(url+'\n')
            log(str(requests.post(url).json()) + '\n')

        continuous_create_format = 'create continuous query {cq_name} on %s begin select mean("Voltage") as "mean_voltage" into {retention}.%s from {last_retention}.%s group by time({cq_time}), * end' % (self.config.database, self.config.measurement, self.config.measurement)
        for index in range(len(self.config.continuous_query)):
            cq_name = self.config.continuous_query_name[index]
            cq_time = self.config.continuous_query[index]
            retention = self.config.retention_policy_name[index+1]
            last_retention = self.config.retention_policy_name[index]
            url = base_url + continuous_create_format.format(cq_name=cq_name, retention=retention, last_retention=last_retention, cq_time=cq_time)
            log(str(requests.post(url).json()) + '\n')

class Director:
    @staticmethod
    def Start(simulator):
        simulator.download()
        simulator.unzip()
        simulator.process()
        simulator.down_sample_config()
        simulator.upload()

def get_env(key, default=None):
    env = os.getenv(key)
    if env:
        return env
    else:
        return default

if __name__ == "__main__":
    config = Config()
    Director.Start(Simulator(config))
    
