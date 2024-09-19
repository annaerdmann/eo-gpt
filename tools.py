# LLM + Langchain packages
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.agents import Tool
from langchain.tools import BaseTool
from langchain_experimental.tools.python.tool import PythonAstREPLTool

# data analysis packages
import climetlab as cml
from climetlab_wekeo_datasets import hda2cml
import xarray as xr
import json


class APICreator(BaseTool):
    name = "Create API Request"
    description = "Generates an API request for satellite data given a dictionary of 'start_time' in the format \"YYYY-MM-DDT00:00:00.000Z\", 'end_time' in the format \"YYYY-MM-DDT00:00:00.000Z\" and 'dataset_id'. Please wrap the json in a string"
    def _run(self, input: str):
        input_dict = json.loads(input)

        api_template = '''{
                      "dataset_id": "EO:EUM:DAT:METOP:GLB-SST-NC",
                      "dtstart": {start_time},
                      "dtend": {end_time}
                    }'''
        api_request =  api_template.replace("{start_time}", '"'+input_dict['start_time']+'"').replace("{end_time}", '"'+input_dict['end_time']+'"')
        return api_request.replace('{', '{{').replace('}', '}}')


    def _arun(self, input: list):
        raise NotImplementedError("This tool does not support async")

api_creator = APICreator()


class DataDownloader(BaseTool):
    name = "Download Data and get Shape"
    description = "The input to the tool is an API request created by the APICreator tool! Given this API request as a json wrapped in a string, this tool downloads the data, converts it to an xarray and gives back the shape of the data. This tool is useful if you want to find out which python code is needed next to analyze the data."
    def _run(self, input: str):
        global api_request_glob
        api_request_glob = input
        input_dict = json.loads(input)
        dsid, args = hda2cml(input_dict)
        cml_ds = cml.load_dataset(dsid, **args)
        ds_local = cml_ds.to_xarray()
        output = "Coordinates of xarray Dataset: ", ds_local.coords, " Variables: ", list(ds_local.keys())
        return output


    def _arun(self, input: list):
        raise NotImplementedError("This tool does not support async")

downloader = DataDownloader()

python_exe = PythonAstREPLTool()

python_tool = Tool(
        name = "python executer",
        func=python_exe,
        description="takes python code as input and executes it. all packages have to be imported inside the python code. make sure that relevant findings are printed to be further processed."
    )

analysis_cmlcode = '''import climetlab as cml
import xarray as xr
import json
from climetlab_wekeo_datasets import hda2cml
dsid, args = hda2cml(api_request)
cml_ds = cml.load_dataset(dsid, **args)
ds_local = cml_ds.to_xarray()

'''

class DataAnalyzer(BaseTool):
    name = "Climetlab Data Analyzer"
    description = "The input to the tool is valid python code to make data analysis. This tool is useful after downloading the data from an API to answer the user question. The data is a xarray dataset and is stored in the variable ds_local. It is most likely a das-sliced xarray, so always use the python package xarray to make the calculations and  the function.compute()in the end! Print the final result using the print() statement."
    def _run(self, input: str):
        code = analysis_cmlcode.replace("api_request", api_request_glob)
        print(code)
        return  python_exe.run(code+input)


analysis_tool = DataAnalyzer()