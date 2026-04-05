import yaml
def load_config(path):
    with open(path, "r") as file:
        return yaml.load(file, Loader=yaml.FullLoader)      