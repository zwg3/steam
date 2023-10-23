import yaml

infinity = float('Inf')

with open('config.yml', 'r') as f:
    sas = yaml.load(f, Loader=yaml.CLoader)
    print(sas)
