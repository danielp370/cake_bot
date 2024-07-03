import configparser

class Config:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_value_by_key(self, section, key, fallback=None):
        """
        Retrieve the value by a given section and key.
        :param section: The section in the config file.
        :param key: The key to look for in the provided section.
        :param fallback: The fallback value if the key is not found.
        :return: The value if found, otherwise the fallback value.
        """

        return self.config.get(section, key, fallback=fallback)

    def get_boolean_by_key(self, section, key, fallback=False):
        """
        Retrieve the value by a given section and key and return a boolean.
        :param section: The section in the config file.
        :param key: The key to look for in the provided section.
        :param fallback: The fallback value if the key is not found.
        :return: The value if found, otherwise the fallback value.
        """

        value = self.config.get(section, key, fallback=str(fallback))
        if value == '' or value == 'False' or value == '0':
            return False
        else:
            return True

    def set_value_by_key(self, section, key, value):
        """
        Update a key value.
        :param section: The section in the config file.
        :param key: The key to look for in the provided section.
        """

        self.config.set(section, key, value)
