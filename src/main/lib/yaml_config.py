import yaml
import os


def _merge(config, config_extends):
    """
    Merges configuration with the configuration being extendsd. Values in the configuration being extended takes
    precedence.

    :param config: config
    :param config_extends: config specified in the 'extends: ...'
    :return:
    """
    for key in config_extends:
        if isinstance(config_extends[key], dict):
            if key not in config:
                config[key] = {}
            _merge(config[key], config_extends[key])
        else:
            config[key] = config_extends[key]
    return config


def load_config(filename):
    """
    Load the configuration from the provided YAML file.

    Configuration can be extending existing one. I.e.:

    file config.yaml:
        extends base.yaml
        value: child

    file base.yaml
        value: parent

    The result is that when config.yaml is being loaded the property named "value" will have a value of "parent".

    :param filename: yaml file holding the configuration
    :return: dict
    """
    with open(filename, 'r') as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    if 'extend' in config:
        parent_file = os.path.dirname(filename) + os.path.sep + config['extend']
        config_extends = load_config(parent_file)
        _merge(config, config_extends)
        del config['extend']

    return config
