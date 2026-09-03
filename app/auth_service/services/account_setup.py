import json
# from ..crud.crud_user import CRUD_USER
from app.core.default_config.account_setup import ACCOUNT_CONFIGURATION
from app.core.default_config.project_setup import PROJECT_CONFIGURATION
from ..schemas import AddFiledRequest

class DefaultAccountSetting:

	def __init__(self,  debug=True):
		self.inputType = ACCOUNT_CONFIGURATION
		self.template_file = ACCOUNT_CONFIGURATION.DEFAULT_ACCOUNT_FILE
		self.sample_txt = ACCOUNT_CONFIGURATION.INIT_FILE
		self.sample_file = PROJECT_CONFIGURATION.SAMPLE_FILE

	

	def new_account_setup(self,db,account_id):
		template_file = ACCOUNT_CONFIGURATION.DEFAULT_ACCOUNT_FILE
		f = open(template_file)
		template_file = json.load(f)		
		structure =template_file['default_folders']
		container_name = template_file['account_container']+str(account_id)
		for single_path in structure:
			file_request: AddFiledRequest = AddFiledRequest()
			file_request.container_name = container_name
			file_request.user_id = account_id
			file_request.account_id = account_id
			file_request.file_name ="Readme.txt"
			file_request.display_name = "Readme.txt"
			file_request.file_url = str(container_name)+str(single_path)+"/"+"Readme.txt"
			file_request.folder_name = single_path
			text_file_full_name = str(single_path)+"/"+"Readme.txt"
			file_obj = open(self.sample_file, 'r').read()
			
			# CRUD_USER.add_new_folder(db, file_request)
			

ACCOUNT_SETUP = DefaultAccountSetting()
	

	

