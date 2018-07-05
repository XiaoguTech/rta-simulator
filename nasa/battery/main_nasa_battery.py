import os
import argparse
import sys
import time
import requests
import time
from functools import reduce
import scipy.io as sio
import datetime

log = sys.stdout.write
error = sys.stderr.write

class Config:
    def __init__(self):        
        
        self.download_file = get_env('RTA_FILE', 'nasa_battery.txt')
        self.download_file_1 = get_env('RTA_FILE_1', 'nasa_battery_1.txt')
        self.result_file = get_env('RTA_RESULT', 'nasa_battery.influxdb')
        self.result_file_1 = get_env('RTA_RESULT', 'nasa_battery_1.influxdb')
        
        self.split_symbol = get_env('RTA_SPLIT_SYMBOL', ';')

        self.tag_keys = get_env('RTA_TAG_KEYS', 'metric').split(' ')
        self.tag_values = get_env('RTA_TAG_VALUES', 'exp').split(self.split_symbol)
        self.tag_keys_1 = get_env('RTA_TAG_KEYS', 'metric').split(' ')
        self.tag_values_1 = get_env('RTA_TAG_VALUES', 'var').split(self.split_symbol)
        self.field_keys = get_env('RTA_FIELD_KEYS', 'ambient_temperature;Voltage_measured;Current_measured;Temperature_measured;Current_charge;Voltage_charge').split(self.split_symbol)
        self.field_values = get_env('RTA_FIELD_VALUES', '$1 $2 $3 $4 $5 $6').split(' ')
        self.field_keys_1 = get_env('RTA_FIELD_KEYS_1', 'ambient_temperature;Capacity;Voltage_measured;Current_measured;Temperature_measured;Current_load;Voltage_load').split(self.split_symbol)
        self.field_values_1 = get_env('RTA_FIELD_VALUES_1', '$1 $2 $3 $4 $5 $6 $7').split(' ')
        
        self.field_values_pos = [res[1:] for res in self.field_values]
        self.field_values_pos_1 = [res[1:] for res in self.field_values_1]
        self.replace_src = get_env('RTA_REPLACE_SRC', '?')
        self.replace_dest = get_env('RTA_REPLACE_DEST', '0.000')
        self.fromline = int(get_env('RTA_FROMLINE', '2')) - 1

        self.batch_size = int(get_env('RTA_BATCH_SIZE', '1'))
        self.start_time = get_env('RTA_START_TIME')
        self.interval = int(get_env('RTA_INTERVAL', '10'))

        self.hosts = get_env('RTA_INFLUX_HOST', 'http://127.0.0.1:8086')
        self.database = get_env('RTA_DATABASE', 'UCIlab')
        self.measurement = get_env('RTA_MEASUREMENT', 'battery')
        self.username = get_env('RTA_USERNAME', 'test')
        self.password = get_env('RTA_PASSWORD', 'test')

class Simulator:
    def __init__(self, config):
        self.config = config
    
    def preprocess(self):
        def getstamp(y=2012,m=2,d=2,h=0,mi=0,s=0.0):
            the_date = datetime.datetime(y,m,d)
            result_date = the_date + datetime.timedelta(hours=h) + datetime.timedelta(minutes=mi) + datetime.timedelta(seconds=s)
            d = result_date.strftime('%a %b %d %H:%M:%S %Y')
            timestamp = int(time.mktime(time.strptime(d))*1000000000)
            return timestamp
        data = sio.loadmat('./B0005.mat')
        data = data['B0005'][0][0]['cycle']
        index = data.shape[1]#616
        for ind in range(index):
            print('%d/%d'%(ind,index))
            exp = data[0][ind]
            ind_type = exp['type'][0]
            ind_temp = exp['ambient_temperature'][0][0]
            ind_start_time = exp['time'][0]# elemet[5] add data.Time
            # manipulating field data
            ind_data = exp['data'][0][0]
            if ind_type == 'charge':
                with open(self.config.download_file,'a+') as writer:
                    dat_voltage_measured = ind_data['Voltage_measured']
                    dat_current_measured = ind_data['Current_measured']
                    dat_temperature_measured = ind_data['Temperature_measured']
                    dat_current_charge = ind_data['Current_charge']
                    dat_voltage_charge = ind_data['Voltage_charge']
                    dat_time = ind_data['Time']
                    index_data = dat_voltage_measured.shape[1]
                    for ind_sim in range(index_data):
                        v_m = dat_voltage_measured[0][ind_sim]
                        c_m = dat_current_measured[0][ind_sim]
                        t_m = dat_temperature_measured[0][ind_sim]
                        c_c = dat_current_charge[0][ind_sim]
                        v_c = dat_voltage_charge[0][ind_sim]
                        t = dat_time[0][ind_sim]
                        stam = getstamp(int(ind_start_time[0]),int(ind_start_time[1]),int(ind_start_time[2]),int(ind_start_time[3]),int(ind_start_time[4]),float(ind_start_time[5]+t))
                        line_data='{ambient_temperature} {Voltage_measured} {Current_measured} {Temperature_measured} {Current_charge} {Voltage_charge} {time_stamp}\n'.format(ambient_temperature=str(ind_temp),Voltage_measured=str(v_m),Current_measured=str(c_m),Temperature_measured=str(t_m),Current_charge=str(c_c),Voltage_charge=str(v_c),time_stamp=str(stam))
                        writer.write(line_data)
            elif ind_type == 'discharge':
                # another txt
                with open(self.config.download_file_1, 'a+') as writer1:
                    ind_capacity = ind_data['Capacity'][0][0]
                    dat_voltage_measured = ind_data['Voltage_measured']
                    dat_current_measured = ind_data['Current_measured']
                    dat_temperature_measured = ind_data['Temperature_measured']
                    dat_current_load = ind_data['Current_load']
                    dat_voltage_load = ind_data['Voltage_load']
                    dat_time = ind_data['Time']
                    index_data = dat_voltage_measured.shape[1]
                    for ind_sim in range(index_data):
                        v_m = dat_voltage_measured[0][ind_sim]
                        c_m = dat_current_measured[0][ind_sim]
                        t_m = dat_temperature_measured[0][ind_sim]
                        c_l = dat_current_load[0][ind_sim]
                        v_l = dat_voltage_load[0][ind_sim]
                        t = dat_time[0][ind_sim]
                        stam = getstamp(int(ind_start_time[0]),int(ind_start_time[1]),int(ind_start_time[2]),int(ind_start_time[3]),int(ind_start_time[4]),float(ind_start_time[5]+t))
                        line_data='{ambient_temperature} {Capacity} {Voltage_measured} {Current_measured} {Temperature_measured} {Current_load} {Voltage_load} {time_stamp}\n'.format(ambient_temperature=str(ind_temp),Capacity=str(ind_capacity),Voltage_measured=str(v_m),Current_measured=str(c_m),Temperature_measured=str(t_m),Current_load=str(c_l),Voltage_load=str(v_l),time_stamp=str(stam))
                        writer1.write(line_data)
            else:
                # ignore impedance
                pass
    
    def process(self):
        tags = []
        # per line tag
        for tag_value in self.config.tag_values:
            tag_values = tag_value.split(' ')
            tags.append( reduce(lambda x, y: x+'%s=%s,' % (y[0], y[1]), list(zip(self.config.tag_keys, tag_values)), '') )
        with open(self.config.result_file, 'w') as writer:
            with open(self.config.download_file) as reader:
                for i,line in enumerate(reader,1):
                    protocol_format = "%s,{tags} {fields} {timestamp}\n" % self.config.measurement
                    values = line.split('\n')[0]
                    values = values.split(' ')
                    fields = reduce(lambda x, y: x+'%s=%s,' % (y[0], values[int(y[1])-1]), list(zip(self.config.field_keys, self.config.field_values_pos)), '')[:-1]
                    timestamp = values[-1]
                    for tag in tags:
                        line_data = protocol_format.format(tags=tag[:-1], fields=fields, timestamp=timestamp).replace(self.config.replace_src, self.config.replace_dest)
                        writer.write(line_data)
        tags = []
        # per line tag
        for tag_value in self.config.tag_values_1:
            tag_values = tag_value.split(' ')
            tags.append( reduce(lambda x, y: x+'%s=%s,' % (y[0], y[1]), list(zip(self.config.tag_keys_1, tag_values)), '') )
        with open(self.config.result_file_1, 'w') as writer:
            with open(self.config.download_file_1) as reader:
                for i,line in enumerate(reader,1):
                    protocol_format = "%s,{tags} {fields} {timestamp}\n" % self.config.measurement
                    values = line.split('\n')[0]
                    values = values.split(' ')
                    fields = reduce(lambda x, y: x+'%s=%s,' % (y[0], values[int(y[1])-1]), list(zip(self.config.field_keys_1, self.config.field_values_pos_1)), '')[:-1]
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
                    log(str(response) + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
                    # time.sleep(self.config.interval)
                    count = 0
                    text = ''
                else:
                    count += 1
                    text += line
        with open(self.config.result_file_1) as reader:
            count = 0
            text = ''
            for line in reader:
                if count == self.config.batch_size:
                    response = requests.post(upload_url, data=text.encode('utf-8'))
                    if response.status_code == 404:
                        requests.get('%s/query?u=%s&p=%s&q=create database %s' % (self.config.hosts, self.config.username, self.config.password, self.config.database))
                        response = requests.post(upload_url, data=text.encode('utf-8'))
                        # log(upload_url)
                    log(str(response) + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
                    # time.sleep(self.config.interval)
                    count = 0
                    text = ''
                else:
                    count += 1
                    text += line

class Director:
    @staticmethod
    def Start(simulator):
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
    
