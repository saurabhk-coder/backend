import os
class Project_Configuration:
    DEFAULT_PROJECT_FILE = str(os.getcwd())+ "/app/core/default_config/project_setup.json"
    INIT_FILE = str(os.getcwd())+ "/app/core/default_config/init.json"
    SAMPLE_FILE = str(os.getcwd())+ "/app/core/default_config/readme.txt"
    DEFAULT_SCENE_FILE = str(os.getcwd())+ "/app/core/default_config/scene.json"

PROJECT_CONFIGURATION = Project_Configuration()