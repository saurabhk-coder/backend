import os
class Account_Configuration:
    DEFAULT_ACCOUNT_FILE = str(os.getcwd())+ "/app/core/default_config/account_setup.json"
    INIT_FILE = str(os.getcwd())+ "/app/core/default_config/readme.txt"

ACCOUNT_CONFIGURATION = Account_Configuration()