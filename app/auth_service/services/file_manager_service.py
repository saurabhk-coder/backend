from abc import *
from ..schemas import FileUploadResponse
from azure.storage.blob import ContainerClient,BlobServiceClient
from ...core import AppSettings,AzureSettings

class IFileManagerService(ABC):
   @abstractmethod
   def upload_file(self,file_name, data, container_name) ->FileUploadResponse:
       pass
 
   

 

class AzureFileManager(IFileManagerService):
   

    def __init__(self):
        
        self.sas_token = AppSettings.AZURE.AZURE_BLOB_SAS_TOKEN
        self.MY_CONNECTION_STRING = AppSettings.AZURE.AZURE_BLOB_CONNECTION_STRING
        self.blob_service_client =  BlobServiceClient.from_connection_string(self.MY_CONNECTION_STRING)

    
        

    def __check_container(self, container_name):
        container = ContainerClient.from_connection_string(AppSettings.AZURE.AZURE_BLOB_CONNECTION_STRING, container_name)
        try:
            container.get_container_properties()
            return True
        except Exception as e:
            # print("Error: {0}".format(str(e)))
            return False

    def upload_file(self,file_name, data, container_name) ->FileUploadResponse:
      
        if self.__check_container(container_name):
            blob_client = self.blob_service_client.get_blob_client(container=container_name,blob=file_name)
        else:
            self.blob_service_client.create_container(container_name)
            blob_client = self.blob_service_client.get_blob_client(container=container_name,blob=file_name)
        blob_client.upload_blob(data,overwrite=True)
        
        response = FileUploadResponse
        response.container_name=container_name
        response.file_name = file_name
        response.file_key = blob_client.url
        response.file_size = "20"
        return response

    

AZURE_FILE_MANAGER_SERVICE:IFileManagerService = AzureFileManager()
