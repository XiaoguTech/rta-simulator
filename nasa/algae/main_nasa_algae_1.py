import os
import argparse
import sys
import time
import requests
import time
from functools import reduce
import scipy.io as sio
import datetime
import numpy as np
log = sys.stdout.write
error = sys.stderr.write

class Config:
    def __init__(self):        
        self.download_url = get_env('RTA_URL', 'https://ti.arc.nasa.gov/m/project/prognostic-repository/algae.zip')
        self.download_file = get_env('RTA_FILE', 'nasa_algae_1.txt')
        self.result_file = get_env('RTA_RESULT', 'nasa_algae_1.influxdb')
        self.useless_file = get_env('RTA_USELESS', 'Readme.pdf')
        self.split_symbol = get_env('RTA_SPLIT_SYMBOL', ';')

        self.tag_keys = get_env('RTA_TAG_KEYS', 'metric').split(' ')
        self.tag_values = get_env('RTA_TAG_VALUES', 'ljz').split(self.split_symbol)
        self.field_keys = get_env('RTA_FIELD_KEYS', 'chlorophyll_a').split(self.split_symbol)
        self.field_values = get_env('RTA_FIELD_VALUES', '$1').split(' ')
        
        self.field_values_pos = [res[1:] for res in self.field_values]
        self.replace_src = get_env('RTA_REPLACE_SRC', '?')
        self.replace_dest = get_env('RTA_REPLACE_DEST', '0.000')
        self.fromline = int(get_env('RTA_FROMLINE', '2')) - 1

        self.batch_size = int(get_env('RTA_BATCH_SIZE', '1'))
        self.start_time = get_env('RTA_START_TIME')
        self.interval = int(get_env('RTA_INTERVAL', '10'))

        self.hosts = get_env('RTA_INFLUX_HOST', 'http://127.0.0.1:8086')
        self.database = get_env('RTA_DATABASE', 'UCIlab')
        self.measurement = get_env('RTA_MEASUREMENT', 'algae_raceway')
        self.username = get_env('RTA_USERNAME', 'test')
        self.password = get_env('RTA_PASSWORD', 'test')

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
            os.system("rm -rf " + self.config.useless_file)
        else:
            pass
    
    def preprocess(self):
        data = sio.loadmat('./algae.mat')
        algae_ts = data['algae_ts']
        r, c = algae_ts.shape
        def getstamp(y=2012,m=2,d=2,n=0,h=0.67):
            the_date = datetime.datetime(y,m,d)
            result_date = the_date + datetime.timedelta(days=n) + datetime.timedelta(hours=(h*24))
            d = result_date.strftime('%a %b %d %H:%M:%S %Y')
            timestamp = int(time.mktime(time.strptime(d))*1000000000)
            return timestamp
        ind = algae_ts[0][0]['chlorophyll_a'][0][0]['data'].shape[0]
        with open(self.config.download_file, 'w') as writer:
            for index in range(0,ind):
                for i in range(0,r):
                    for j in range(0,c):
                        algae = algae_ts[i][j]# each raceway
                        chlorophyll_a = algae['chlorophyll_a']
                        data_chl = chlorophyll_a[0][0]['data']
                        time_stam = chlorophyll_a[0][0]['time_num']
                        chl = data_chl[index][0]
                        stamp = time_stam[index][0]
                        timestamp = getstamp(2012,2,2,int(stamp),float(0.671))
                        line_data = '{chl} {stamp}\n'.format(chl=str(chl),stamp=str(timestamp))
                        writer.write(line_data)
    
    def process(self):
        tags = []
        # per line tag
        for tag_value in self.config.tag_values:
            tag_values = tag_value.split(' ')
            tags.append( reduce(lambda x, y: x+'%s=%s,' % (y[0], y[1]), list(zip(self.config.tag_keys, tag_values)), '') )

        with open(self.config.result_file, 'w') as writer:
            with open(self.config.download_file) as reader:
                for i,line in enumerate(reader,1):
                    protocol_format = "%s%d,{tags} {fields} {timestamp}\n" % (self.config.measurement,((i+2)%3+1))
                    values = line.split('\n')[0]
                    values = values.split(' ')
                    fields = reduce(lambda x, y: x+'%s=%s,' % (y[0], values[int(y[1])-1]), list(zip(self.config.field_keys, self.config.field_values_pos)), '')[:-1]
                    timestamp = values[-1]
                    for tag in tags:
                        line_data = protocol_format.format(tags=tag[:-1], fields=fields, timestamp=timestamp).replace(self.config.replace_src, self.config.replace_dest)
                        writer.write(line_data)

    def upload(self):
        upload_url = '%s/write?db=%s&u=%s&p=%s' % (self.config.hosts, self.config.database, self.config.username, self.config.password)
        
        with open(self.config.result_file) as reader:
            count = 0
            text = ''
            for line in reader:
                if count == self.config.batch_size:
                    response = requests.post(upload_url, data=text.encode('utf-8'))
                    if response.status_code == 404:
                        requests.get('%s/query?u=%s&p=%s&q=create database %s' % (self.config.hosts, self.config.username, self.config.password, self.config.database))
                        response = requests.post(upload_url, data=text.encode('utf-8'))
                        # log(upload_url)
                    # log(str(response) + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
                    # time.sleep(self.config.interval)
                    count = 0
                    text = ''
                else:
                    count += 1
                    text += line 

class Director:
    @staticmethod
    def Start(simulator):
        # simulator.download()
        # simulator.unzip()
        simulator.preprocess()
        simulator.process()
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
    
