import requests
import json
import os

def load_json(file_name):
    '''
    return stringify json data
    '''
    if file_name.split('.')[-1] == 'json':
        f = open(file_name)
        d = json.load(f)
        return json.dumps(d)
    return None

def import_dashboard(data):
    '''
    data is a json file text exported by another dashboard
    '''
    url = 'http://admin:admin@localhost:3000/api/dashboards/import'
    headers = {"Content-Type": 'application/json'}
    response = requests.post(url, data=data, headers=headers)
    return response.status_code

def load_import():
    for roots, dirs, files in os.walk('.'):
        for file_name in files:
            data = load_json(file_name)
            if data:
                status_code = import_dashboard(data)
                print('status code:', status_code)
            else:
                pass

if __name__ == "__main__":
    load_import()
