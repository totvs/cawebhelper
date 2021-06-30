import json
import os
from datetime import datetime

class ConfigLoader:
    """
    This class is instantiated to contain all config information used throughout the execution of the methods.
    """
    def __init__(self, path="config.json"):
        valid = os.path.isfile(path)

        if valid:
            with open(path) as json_data_file:
                data = json.load(json_data_file)
        else:
            data = {}

        today = datetime.today()

        self.json_data = data
        self.autostart = True
        self.ipExec = str(data["ipExec"]) if "ipExec" in data else ""
        self.url_set_start_exec = str(data["UrlSetStartExec"]) if "UrlSetStartExec" in data else ""
        self.url_set_end_exec = str(data["UrlSetEndExec"]) if "UrlSetEndExec" in data else ""
        self.screenshot = bool(data["ScreenShot"]) if "ScreenShot" in data else True
        self.country = str(data["Country"]) if "Country" in data else "BRA"
        self.execution_id = str(data["ExecId"]) if "ExecId" in data else today.strftime('%Y%m%d')
        self.num_exec = str(data["NumExec"]) if "NumExec" in data else ""
        self.issue = str(data["MotExec"]) if "MotExec" in data else ""
        self.url = str(data["Url"]) if "Url" in data else ""
        self.browser = str(data["Browser"]) if "Browser" in data else ""
        self.environment = str(data["Environment"])  if "Environment" in data else ""
        self.user = str(data["User"]) if "User" in data else ""
        self.password = str(data["Password"]) if "Password" in data else ""
        self.language = str(data["Language"]) if "Language" in data else ""
        self.skip_environment = ("SkipEnvironment" in data and bool(data["SkipEnvironment"]))
        self.headless = ("Headless" in data and bool(data["Headless"]))
        self.log_folder = str(data["LogFolder"]) if "LogFolder" in data else ""
        self.log_file = ("LogFile" in data and bool(data["LogFile"]))
        self.debug_log = ("DebugLog" in data and bool(data["DebugLog"]))
        self.time_out = int(data["TimeOut"]) if "TimeOut" in data else 90
        self.parameter_menu = str(data["ParameterMenu"]) if "ParameterMenu" in data else ""
        self.screenshot_folder = str(data["ScreenshotFolder"]) if "ScreenshotFolder" in data else ""
        self.coverage = ("Coverage" in data  and bool(data["Coverage"]))
        self.skip_restart = ("SkipRestart" in data and bool(data["SkipRestart"]))
        self.smart_test = ("SmartTest" in data and bool(data["SmartTest"]))
        self.smart_erp = ("SmartERP" in data and bool(data["SmartERP"]))
        self.valid_language = self.language != ""
        self.initial_program = ""
        self.routine = ""
        self.date = ""
        self.group = ""
        self.branch = ""
        self.module = ""
        self.user_cfg = str(data["UserCfg"]) if "UserCfg" in data else ""
        self.password_cfg = str(data["PasswordCfg"]) if "PasswordCfg" in data else ""
        self.electron_binary_path = (str(data["BinPath"]) if "BinPath" in data else "")
        self.csv_path = (str(data["CSVPath"]) if "CSVPath" in data else "")
        self.database_driver = str(data["DBDriver"]) if "DBDriver" in data else ""
        self.database_server = str(data["DBServer"]) if "DBServer" in data else ""
        self.database_port = str(data["DBPort"]) if "DBPort" in data else ""
        self.database_name = str(data["DBName"]) if "DBName" in data else ""
        self.database_user = str(data["DBUser"]) if "DBUser" in data else ""
        self.database_password = str(data["DBPassword"]) if "DBPassword" in data else ""
        self.dbq_oracle_server = str(data["DBQOracleServer"]) if "DBQOracleServer" in data else ""
        self.url_tss = str(data["URL_TSS"]) if "URL_TSS" in data else ""
        self.start_program = str(data["StartProgram"]) if "StartProgram" in data else ""
        self.new_log = ("NewLog" in data  and bool(data["NewLog"]))
        self.logurl1 = str(data["LogUrl1"]) if "LogUrl1" in data else ""
        self.logurl2 = str(data["LogUrl2"]) if "LogUrl2" in data else ""
        self.parameter_url = bool(data["ParameterUrl"]) if "ParameterUrl" in data else False
        self.release = str(data["Release"]) if "Release" in data else ""
        self.log_http = str(data["LogHttp"]) if "LogHttp" in data else ""
        self.baseline_spool = str(data["BaseLine_Spool"]) if "BaseLine_Spool" in data else ""
