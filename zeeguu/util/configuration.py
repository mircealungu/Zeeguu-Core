import os


def assert_configs(config, required_keys, config_file_name=None):
    for key in required_keys:
        config_value = config.get(key, None)
        if config_value is None:
            print("Please define the {key} key in the {config} file!".format(key=key,
                                                                             config=config_file_name or 'config'))
            exit(-1)


def load_configuration_or_abort(app, environ_variable, mandatory_config_keys=[]):
    """
    
        Try to load config from the file named in the environ variable. 
                
        If a config is loaded, the function makes sure that the mandatory_config_keys are 
        in the file
        
    :return: Returns in case of success. Throws exception otherwise. 

    """

    try:
        config_file = load_config_file(environ_variable)
        app.config.from_pyfile(config_file, silent=False)
    except Exception as e:
        print(str(e))
        exit(-1)

    assert_configs(app.config, mandatory_config_keys, config_file)

    print(("ZEEGUU: Loaded {0} config from {1}".format(app.name, config_file)))


def load_config_file(environ_variable):
    try:
        return os.environ[environ_variable]
    except Exception as e:
        print(str(e))
        print(("You must define a {0} environment var to be able to load the configuration. ".format(environ_variable)))
