import time
import os
import numpy as nump
import pandas as panda
import uuid
import csv
import inspect
import re
import requests
import json
import platform
from datetime import datetime
from tir.technologies.core.config import ConfigLoader

class Log:
    """
    This class is instantiated to create the log file and to append the results and failures to it.

    Usage:

    >>> # Instanted inside base.py:
    >>> self.log = Log()
    """
    def __init__(self, suite_datetime="", user="", station="", program="", program_date="", version="", release="", database="", issue="", execution_id="", country="", folder="", test_type=""):
        self.timestamp = time.strftime("%Y%m%d%H%M%S")
        
        today = datetime.today()

        self.user = user
        self.station = station
        self.program = program
        self.program_date = "19800101"
        self.version = version
        self.release = release
        self.database = database
        self.initial_time = datetime.today()
        self.seconds = 0
        self.suite_datetime = suite_datetime
        self.test_case_log = []
        self.csv_log = []
        self.invalid_fields = []
        self.folder = folder
        self.test_type = "TIR"
        self.issue = issue
        self.execution_id = execution_id
        self.country = country
        self.config = ConfigLoader()
        self.ct_method = ""
        self.ct_number = ""
        self.so_type = platform.system()
        self.so_version = f"{self.so_type } {platform.release()}"
        self.build_version = ""
        self.lib_version = ""
        self.webapp_version = ""
        self.date = today.strftime('%Y%m%d')
        self.hour = time.strftime('%H:%M:%S')
        self.hash_exec = ""

    def generate_result(self, result, message):
        """
        Generate a result of testcase and export to a json.

        :param result: The result of the case.
        :type result: bool
        :param message: The message to be logged..
        :type message: str

        Usage:

        >>> # Calling the method:
        >>> self.log.generate_result(True, "Success")
        """
        total_cts = 1
        result = 0 if result else 1
        printable_message = ''.join(filter(lambda x: x.isprintable(), message))[:650]

        if not self.suite_datetime:
            self.suite_datetime = time.strftime("%d/%m/%Y %X")

        self.generate_json(self.generate_dict(result, printable_message))

    def set_seconds(self):
        """
        Sets the seconds variable through a calculation of current time minus the execution start time.

        Usage:

        >>> # Calling the method:
        >>> self.log.set_seconds()
        """
        delta = datetime.today() - self.initial_time
        self.seconds = round(delta.total_seconds(), 2)

    def list_of_testcases(self):
        """
        Returns a list of test cases from suite 
        """
        runner = next(iter(list(filter(lambda x: "runner.py" in x.filename, inspect.stack()))))
        try:
            return list(runner.frame.f_locals['test'])
        except KeyError:
            return []

    def get_testcase_stack(self):
        """
        Returns a string with the current testcase name
        [Internal]
        """
        return next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('setUpClass', x.function) or re.search('test_', x.function), inspect.stack())))), None)

    def get_file_name(self, file_name):
        """
        Returns a Testsuite name
        """
        testsuite_stack = next(iter(list(filter(lambda x: file_name in x.filename.lower(), inspect.stack()))),None)
        
        if testsuite_stack:

            if '/' in testsuite_stack.filename:
                split_character = '/'
            else:
                split_character = '\\'

            return testsuite_stack.filename.split(split_character)[-1].split(".")[0]
        else:
            return ""

    def generate_dict(self, result, message):
        """
        Returns a dictionary with the log information
        """
        log_version = "20190819"

        dict_key = {
            "APPVERSION":self.build_version,
            "CLIVERSION":self.webapp_version,
            "COUNTRY":self.country,
            "CTMETHOD":self.ct_method,
            "CTNUMBER":self.ct_number,
            "DATE":self.date,
            "DATEPROGRAM":self.program_date,
            "DBACCESS":"",
            "DBTYPE":self.database,
            "DBVERSION":"",
            "FAILSCTS":message,
            "HASHEXEC":self.hash_exec,
            "HOUR":self.hour,
            "HOURPROGRAM":"00:00:00",
            "IDENTIFICADOR":self.issue,
            "IDEXEC":self.config.execution_id,
            "LIBVERSION":self.lib_version,
            "LOGTOOL":self.test_type,
            "LOGVERSION":self.test_type+log_version,
            "PROGRAM":self.program,
            "RELEASE":self.release,
            "RESULT":str(result),
            "SECONDS":str(self.seconds),
            "SOTYPE":self.so_type,
            "SOVERSION":self.so_version,
            "TESTCASE":self.get_file_name('testcase'),
            "TESTSUITE":self.get_file_name('testsuite'),
            "TESTTYPE":"1",
            "TOKEN":"",
            "USER":self.user,
            "VERSION":self.version,
            "WORKSTATION":self.station
        }

        return dict_key
    
    def generate_json(self, dictionary):
        """
        """
        server_address1 = "http://10.171.78.41:8006/rest/LOGEXEC/"
        server_address2 = "http://10.171.78.43:8204/rest/LOGEXEC/"

        success = False

        data = dictionary

        json_data = json.dumps(data)

        endtime = time.time() + 15

        while(time.time() < endtime and not success):

            success = self.send_request(server_address1, json_data)

            if not success:
                success = self.send_request(server_address2, json_data)

            time.sleep(1)
        
        if not success:
            self.save_file(json_data)            

    def send_request(self, server_address, json_data):
        """
        Send a post request to server
        """
        success = False
        response = None

        try:
            response = requests.post(server_address.strip(), data=json_data)
        except:
            pass

        if response:
            if response.status_code == 200:
                print("Log de execucao enviado com sucesso!")
                success = True
            elif response.status_code == 201 or response.status_code == 204:
                print("Log de execucao enviado com sucesso!")
                success = True
        else:
            return False

        return success

    def save_file(self, json_data):
        """
        Writes the log file to the file system.

        Usage:

        >>> # Calling the method:
        >>> self.log.save_file()
        """

        try:
            if self.folder:
                path = f"{self.folder}\\{self.station}_v6"
                os.makedirs(path)
            else:
                path = f"Log\\{self.station}"
                os.makedirs(path)
        except OSError:
            pass
        
        log_file = f"{self.user}_{uuid.uuid4().hex}.json"

        if self.config.smart_test:
            open("log_exec_file.txt", "w")
    
        with open(f"{path}\\{log_file}", mode="w", encoding="utf-8") as json_file:
            json_file.write(json_data)

        print(f"Log file created successfully: {path}\\{log_file}")