import os
import argparse
import sys
import time
import requests
import time
from functools import reduce
import numpy as np
log = sys.stdout.write
error = sys.stderr.write


class Config:
    def __init__(self):
        self.download_url = get_env('RTA_URL', 'http://archive.ics.uci.edu/ml/machine-learning-databases/00362/HT_Sensor_UCIsubmission.zip')
        self.dataset_filename = get_env('RTA_DATASET_FILENAME', 'HT_Sensor_dataset.zip')
        self.useless_filename = get_env('RTA_USELESS', 'HT_Sensor_dataset.zip __MACOSX')
        self.download_file = get_env('RTA_FILE', 'ht_sensor_data.txt')
        self.result_file = get_env('RTA_RESULT', 'sensor.influxdb')
        self.split_symbol = get_env('RTA_SPLIT_SYMBOL', ';')

        self.tag_keys = get_env('RTA_TAG_KEYS', 'metric').split(' ')
        self.tag_values = get_env('RTA_TAG_VALUES', 'ljz').split(self.split_symbol)
        self.field_keys = get_env('RTA_FIELD_KEYS', 'R1;R2;R3;R4;R5;R6;R7;R8;Temp;Humidity;Class;DurationTime').split(self.split_symbol)
        self.field_values = get_env('RTA_FIELD_VALUES', '$3 $4 $5 $6 $7 $8 $9 $10 $11 $12 $13 $14').split(' ')

        self.field_values_pos = [res[1:] for res in self.field_values]
        self.replace_src = get_env('RTA_REPLACE_SRC', '?')
        self.replace_dest = get_env('RTA_REPLACE_DEST', '0.000')
        self.fromline = int(get_env('RTA_FROMLINE', '2')) - 1

        self.batch_size = int(get_env('RTA_BATCH_SIZE', '1'))
        self.start_time = get_env('RTA_START_TIME')
        self.interval = int(get_env('RTA_INTERVAL', '600'))

        self.hosts = get_env('RTA_INFLUX_HOST', 'http://127.0.0.1:8086')
        self.database = get_env('RTA_DATABASE', 'UCIlab')
        self.measurement = get_env('RTA_MEASUREMENT', 'gas_sensor')
        self.username = get_env('RTA_USERNAME', 'test')
        self.password = get_env('RTA_PASSWORD', 'test')

        self.retention_policy_name = get_env('RTA_RETENTION_POLICY_NAME', 'default default_one_day one_week eight_weeks').split(' ')
        self.retention_policy = get_env('RTA_RETENTION_POLICY', '30m 1d 1w 8w').split(' ')
        # self.continuous_query_name = 'cq_5m cq_5h'.split(' ')
        # self.continuous_query = '5m 5h'.split(' ')

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
            os.system("unzip -o " + self.config.dataset_filename)
            os.system("rm -rf " + self.config.useless_filename)
        else:
            pass

    def preprocess(self):
        for root, dirs, files in os.walk('.'):
            for file_name in files:
                if file_name == 'HT_Sensor_metadata.dat':
                    metadata = np.loadtxt(file_name, skiprows=1, dtype=bytes).astype(str)
                    metadata[ metadata[:,2] == 'background', 2 ] = 0
                    metadata[ metadata[:,2] == 'wine', 2 ] = 1
                    metadata[ metadata[:,2] == 'banana', 2 ] = 2
                    metadata = np.array( metadata[:,[0,2,4]], dtype=float)
                elif file_name == 'HT_Sensor_dataset.dat':
                    dataset = np.loadtxt(file_name, skiprows=1)
                else:
                    pass
        data_i0 = dataset[dataset[:,0]==0]
        label_0 = np.ones(data_i0.shape[0])*metadata[ metadata[:,0] == 0, 1]
        dt_0 = np.ones(data_i0.shape[0])*metadata[ metadata[:,0] == 0, 2]
        data_0 = np.c_[data_i0,label_0,dt_0]
        for i in metadata[:,0]:
            data_ii = dataset[dataset[:,0]==(i+1)]
            label_i = np.ones(data_ii.shape[0])*metadata[ metadata[:,0] == (i+1), 1]
            dt_i = np.ones(data_ii.shape[0])*metadata[ metadata[:,0] == (i+1), 2]
            data_i = np.c_[data_ii,label_i,dt_i]
            data_0 = np.row_stack((data_0, data_i))
        np.savetxt(self.config.download_file, data_0, fmt=['%s']*(data_0.shape[1]), newline='\n')

    def process(self):
        protocol_format = "%s,{tags} {fields}\n" % self.config.measurement
        tags = []
        # per line tag
        for tag_value in self.config.tag_values:
            tag_values = tag_value.split(' ')
            tags.append( reduce(lambda x, y: x+'%s=%s,' % (y[0], y[1]), list(zip(self.config.tag_keys, tag_values)), '') )
        # write db static file
        with open(self.config.result_file, 'w') as writer:
            with open(self.config.download_file) as reader:
                for i, line in enumerate(reader, 1):
                    values = line.split(' ')
                    fields = reduce(lambda x, y: x+'%s=%s,' % (y[0], values[int(y[1])-1]), list(zip(self.config.field_keys, self.config.field_values_pos)), '')[:-1]
                    for tag in tags:
                        line_data = protocol_format.format(tags=tag[:-1], fields=fields).replace(self.config.replace_src, self.config.replace_dest)
                        writer.write(line_data)

    def upload(self):
        upload_url = '%s/write?db=%s&u=%s&p=%s' % (self.config.hosts, self.config.database, self.config.username, self.config.password)

        with open(self.config.result_file) as reader:
            count = 0
            text = ''
            for line in reader:
                if count == self.config.batch_size:
                    print('text:'+text)
                    value = text.split(' ')[-1].split(',')[-1].split('=')[-1].split('\\')[0]
                    duration = float(value)*60
                    print(duration)
                    response = requests.post(upload_url, data=text.encode('utf-8'))
                    if response.status_code == 404:
                        requests.get('%s/query?u=%s&p=%s&q=create database %s' % (self.config.hosts, self.config.username, self.config.password, self.config.database))
                        response = requests.post(upload_url, data=text.encode('utf-8'))
                    log(str(response) + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
                    time.sleep(duration)
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
            log(str(requests.get(url).json()) + '\n')

class Director:
    @staticmethod
    def Start(simulator):
        # simulator.download()
        # simulator.unzip()
        # simulator.preprocess()
        # simulator.process()
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
