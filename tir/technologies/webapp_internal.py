import re
import time
import pandas as pd
import inspect
import os
import random
import uuid
from functools import reduce
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import tir.technologies.core.enumerations as enum
from tir.technologies.core.log import Log
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.language import LanguagePack
from tir.technologies.core.third_party.xpath_soup import xpath_soup
from tir.technologies.core.psutil import system_info
from tir.technologies.core.base import Base
from tir.technologies.core.numexec import NumExec
from math import sqrt, pow
from selenium.common.exceptions import *
from difflib import SequenceMatcher

class WebappInternal(Base):
    """
    Internal implementation of Protheus Webapp class.

    This class contains all the methods defined to run Selenium Interface Tests on Protheus Webapp.

    Internal methods should have the **[Internal]** tag and should not be accessible to the user.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str
    :param autostart: Sets whether TIR should open browser and execute from the start. - **Default:** True
    :type: bool

    Usage:

    >>> # Inside __init__ method in Webapp class of main.py
    >>> def __init__(self, config_path="", autostart=True):
    >>>     self.__webapp = WebappInternal(config_path, autostart)
    """
    def __init__(self, config_path="", autostart=True):
        """
        Definition of each global variable:

        base_container: A variable to contain the layer element to be used on all methods.

        grid_check: List with fields from a grid that must be checked in the next LoadGrid call.

        grid_counters: A global counter of grids' last row to be filled.

        grid_input: List with fields from a grid that must be filled in the next LoadGrid call.

        used_ids: Dictionary of element ids and container already captured by a label search.
        """
        webdriver_exception = None

        try:
            super().__init__(config_path, autostart)
        except WebDriverException as e:
            webdriver_exception = e

        self.containers_selectors = {
            "SetButton" : ".tmodaldialog,.ui-dialog",
            "GetCurrentContainer": ".tmodaldialog",
            "AllContainers": "body,.tmodaldialog,.ui-dialog",
            "ClickImage": ".tmodaldialog",
            "BlockerContainers": ".tmodaldialog,.ui-dialog",
            "Containers": ".tmodaldialog,.ui-dialog"
        }
        self.base_container = ".tmodaldialog"

        self.grid_check = []
        self.grid_counters = {}
        self.grid_input = []
        self.down_loop_grid = False
        self.num_exec = NumExec()
        self.restart_counter = 0
        self.used_ids = {}
        self.tss = False

        self.parameters = []
        self.backup_parameters = []
        self.tree_base_element = ()

        if not self.config.smart_test and self.config.issue:
            self.check_mot_exec()

        if webdriver_exception:
            message = f"Wasn't possible execute Start() method: {next(iter(webdriver_exception.msg.split(':')), None)}"
            self.restart_counter = 3
            self.log_error(message)
            self.assertTrue(False, message)

    def SetupTSS( self, initial_program = "", enviroment = ""):
        """
        Prepare the Protheus Webapp TSS for the test case, filling the needed information to access the environment.
        .. note::
            This method use the user and password from config.json.

        :param initial_program: The initial program to load.
        :type initial_program: str
        :param environment: The initial environment to load.
        :type environment: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetupTSS("TSSMANAGER", "SPED")
        """
        try:

            print("Starting Setup TSS")
            self.tss = True
            self.service_process_bat_file()

            self.config.initial_program = initial_program
            enviroment = self.config.environment if self.config.environment else enviroment

            self.containers_selectors["SetButton"] = "body"
            self.containers_selectors["GetCurrentContainer"] = ".tmodaldialog, body"

            if not self.config.skip_environment and not self.config.coverage:
                self.program_screen(initial_program, enviroment)

            if not self.log.program:
                self.log.program = self.get_program_name()

            if self.config.coverage:
                self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)

            self.user_screen_tss()
            self.set_log_info_tss()

            if self.config.num_exec:
                if not self.num_exec.post_exec(self.config.url_set_start_exec):
                    self.restart_counter = 3
                    self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

        except ValueError as e:
            self.log_error(str(e))
        except Exception as e:
            self.log_error(str(e))

    def user_screen_tss(self):
        """
        [Internal]

        Fills the user login screen of Protheus with the user and password located on config.json.

        Usage:

        >>> # Calling the method
        >>> self.user_screen()
        """
        print("Fill user Screen")
        self.wait_element(term="[name='cUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")

        self.SetValue('cUser', self.config.user, name_attr = True)
        self.SetValue('cPass', self.config.password, name_attr = True)
        self.SetButton("Entrar")
        

    def Setup(self, initial_program, date='', group='99', branch='01', module='', save_input=True):
        """
        Prepare the Protheus Webapp for the test case, filling the needed information to access the environment.

        :param initial_program: The initial program to load.
        :type initial_program: str
        :param date: The date to fill on the environment screen. - **Default:** "" (empty string)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "99"
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "01"
        :type branch: str
        :param module: The module to fill on the environment screen. - **Default:** "" (empty string)
        :type module: str
        :param save_input: Boolean if all input info should be saved for later usage. Leave this flag 'True' if you are not sure. **Default:** True
        :type save_input: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.Setup("SIGAFAT", "18/08/2018", "T1", "D MG 01 ")
        """

        if self.config.smart_test:
            print(f"***System Info*** in Setup():")
            system_info()

        try:
            self.service_process_bat_file()
            
            if not initial_program:
                self.log_error("Couldn't find The initial program")

            if self.config.smart_erp:
                self.wait_smart_erp_environment()

            if not self.log.program:
                self.log.program = self.get_program_name()

            if save_input:
                self.config.initial_program = initial_program
                self.config.date = date
                self.config.group = group
                self.config.branch = branch
                self.config.module = module

            if self.config.coverage:
                self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)

            if not self.config.valid_language:
                self.config.language = self.get_language()
                self.language = LanguagePack(self.config.language)

            if not self.config.skip_environment and not self.config.coverage:
                self.program_screen(initial_program=initial_program, coverage=False)

            self.log.webapp_version = self.driver.execute_script("return app.VERSION")

            self.user_screen(True) if initial_program.lower() == "sigacfg" else self.user_screen()

            endtime = time.time() + self.config.time_out
            while(time.time() < endtime and (not self.element_exists(term=self.language.database, scrap_type=enum.ScrapType.MIXED, main_container=".twindow", optional_term=".tsay"))):
                self.update_password()

            self.environment_screen()

            while(time.time() < endtime and (not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"))):
                self.close_coin_screen()
                self.close_modal()

            if save_input:
                self.set_log_info()

            self.log.country = self.config.country
            self.log.execution_id = self.config.execution_id
            self.log.issue = self.config.issue
            
        except ValueError as error:
            self.log_error(error)
        except Exception as e:
            self.log_error(str(e))

        if self.config.num_exec:
            if not self.num_exec.post_exec(self.config.url_set_start_exec):
                self.restart_counter = 3
                self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

    def service_process_bat_file(self):
        """
        [Internal]
        This method creates a batfile in the root path to kill the process and its children.
        """
        if self.config.smart_test:
            with open("firefox_task_kill.bat", "w", ) as firefox_task_kill:
                firefox_task_kill.write(f"taskkill /f /PID {self.driver.service.process.pid} /T")




    def program_screen(self, initial_program="", environment="", coverage=False):
        """
        [Internal]

        Fills the first screen of Protheus with the first program to run and the environment to connect.

        :param initial_program: The initial program to load
        :type initial_program: str
        :param environment: The environment to connect
        :type environment: str

        Usage:

        >>> # Calling the method
        >>> self.program_screen("SIGAADV", "MYENVIRONMENT")
        """
        if coverage:
            self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)
        else:
            try_counter = 0
            self.wait_element(term='#inputStartProg', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            self.wait_element(term='#inputEnv', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            soup = self.get_current_DOM()

            print("Filling Initial Program")
            start_prog_element = next(iter(soup.select("#inputStartProg")), None)
            if start_prog_element is None:
                self.restart_counter += 1
                message = "Couldn't find Initial Program input element."
                self.log_error(message)
                raise ValueError(message)

            start_prog = lambda: self.soup_to_selenium(start_prog_element)
            start_prog_value = self.get_web_value(start_prog())
            endtime = time.time() + self.config.time_out
            while (time.time() < endtime and (start_prog_value.strip() != initial_program.strip())):

                if try_counter == 0:
                    start_prog = lambda: self.soup_to_selenium(start_prog_element)
                else:
                    start_prog = lambda: self.soup_to_selenium(start_prog_element.parent)

                self.set_element_focus(start_prog())
                start_prog().clear()
                self.send_keys(start_prog(), initial_program)
                start_prog_value = self.get_web_value(start_prog())
                try_counter += 1 if(try_counter < 1) else -1
            
            if (start_prog_value.strip() != initial_program.strip()):
                self.restart_counter += 1
                message = "Couldn't fill Program input element."
                self.log_error(message)
                raise ValueError(message)

            print("Filling Environment")
            env_element = next(iter(soup.select("#inputEnv")), None)
            if env_element is None:
                self.restart_counter += 1
                message = "Couldn't find Environment input element."
                self.log_error(message)
                raise ValueError(message)

            env = lambda: self.soup_to_selenium(env_element)
            env_value = self.get_web_value(env())
            endtime = time.time() + self.config.time_out
            try_counter = 0
            while (time.time() < endtime and (env_value.strip() != self.config.environment.strip())):

                if try_counter == 0:
                    env = lambda: self.soup_to_selenium(env_element)
                else:
                    env = lambda: self.soup_to_selenium(env_element.parent)

                self.set_element_focus(env())
                env().clear()
                self.send_keys(env(), self.config.environment)
                env_value = self.get_web_value(env())
                try_counter += 1 if(try_counter < 1) else -1

            if (env_value.strip() != self.config.environment.strip()):
                self.restart_counter += 1
                message = "Couldn't fill Environment input element."
                self.log_error(message)
                raise ValueError(message)

            button = self.driver.find_element(By.CSS_SELECTOR, ".button-ok")
            self.click(button)

    def user_screen(self, admin_user = False):
        """
        [Internal]

        Fills the user login screen of Protheus with the user and password located on config.json.

        Usage:

        >>> # Calling the method
        >>> self.user_screen()
        """
        user_text = self.config.user_cfg if  admin_user and self.config.user_cfg else self.config.user
        password_text = self.config.password_cfg if admin_user and self.config.password_cfg else self.config.password

        if self.config.smart_test and admin_user and not self.config.user_cfg :
            user_text = "admin"
            password_text = "1234"

        if not self.wait_element_timeout(term="[name='cGetUser'] > input",
         scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out * 3 , main_container='body'):
            self.reload_user_screen()

        try_counter = 0
        soup = self.get_current_DOM()

        print("Filling User")

        try:
            user_element = next(iter(soup.select("[name='cGetUser'] > input")), None)

            if user_element is None:
                self.restart_counter += 1
                message = "Couldn't find User input element."
                self.log_error(message)
                raise ValueError(message)

            user = lambda: self.soup_to_selenium(user_element)
            user_value = self.get_web_value(user())
        except AttributeError as e:
            self.log_error(str(e))
            raise AttributeError(e)
            
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (user_value.strip() != user_text.strip())):

            if try_counter == 0:
                user = lambda: self.soup_to_selenium(user_element)
            else:
                user = lambda: self.soup_to_selenium(user_element.parent)

            self.set_element_focus(user())
            self.wait_until_to(expected_condition="element_to_be_clickable", element = user_element, locator = By.XPATH, timeout=True)
            self.double_click(user())
            # self.send_keys(user(), Keys.HOME)
            self.send_keys(user(), user_text)
            self.send_keys(user(), Keys.ENTER)
            user_value = self.get_web_value(user())
            try_counter += 1 if(try_counter < 1) else -1

        if (user_value.strip() != user_text.strip()):
            self.restart_counter += 1
            message = "Couldn't fill User input element."
            self.log_error(message)
            raise ValueError(message)

        # loop_control = True

        # while(loop_control):
        print("Filling Password")
        password_element = next(iter(soup.select("[name='cGetPsw'] > input")), None)
        if password_element is None:
            self.restart_counter += 1
            message = "Couldn't find User input element."
            self.log_error(message)
            raise ValueError(message)

        password = lambda: self.soup_to_selenium(password_element)
        password_value = self.get_web_value(password())
        endtime = time.time() + self.config.time_out
        try_counter = 0
        while (time.time() < endtime and not password_value.strip() and self.config.password != ''):

            if try_counter == 0:
                password = lambda: self.soup_to_selenium(password_element)
            else:
                password = lambda: self.soup_to_selenium(password_element.parent)

            self.set_element_focus(password())
            self.wait_until_to( expected_condition="element_to_be_clickable", element = password_element, locator = By.XPATH, timeout=True)
            self.click(password())
            self.send_keys(password(), Keys.HOME)
            self.send_keys(password(), password_text)
            self.send_keys(password(), Keys.ENTER)
            password_value = self.get_web_value(password())
            self.wait_blocker()
            try_counter += 1 if(try_counter < 1) else -1
        
        if not password_value.strip() and self.config.password != '':
            self.restart_counter += 1
            message = "Couldn't fill User input element."
            self.log_error(message)
            raise ValueError(message)

        button_element = next(iter(list(filter(lambda x: self.language.enter in x.text, soup.select("button")))), None)
        if button_element is None:
            self.restart_counter += 1
            message = "Couldn't find Enter button."
            self.log_error(message)
            raise ValueError(message)

        button = lambda: self.driver.find_element_by_xpath(xpath_soup(button_element))
        self.click(button())

    def reload_user_screen(self):
        """
        [Internal]

        Refresh the page - retry load user_screen
        """

        self.driver_refresh()

        if self.config.coverage:
            self.driver.get(f"{self.config.url}/?StartProg=CASIGAADV&A={self.config.initial_program}&Env={self.config.environment}")

        if not self.config.skip_environment and not self.config.coverage:
            self.program_screen(self.config.initial_program)

        self.wait_element_timeout(term="[name='cGetUser'] > input",
         scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out , main_container='body')

    def environment_screen(self, change_env=False):
        """
        [Internal]

        Fills the environment screen of Protheus with the values passed on the Setup method.
        Used to fill the fields triggered by the ChangeEnvironment method as well.

        :param change_env: Boolean if the method is being called by ChangeEnvironment. - **Default:** False
        :type change_env: bool

        Usage:

        >>> # Calling the method
        >>> self.environment_screen()
        """

        if change_env:
            label = self.language.confirm
            container = "body"
        else:
            label = self.language.enter
            container = ".twindow"

        self.wait_element(self.language.database, main_container=container)

        print("Filling Date")
        base_dates = self.web_scrap(term="[name='dDataBase'] input, [name='__dInfoData'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)
        if len(base_dates) > 1:
            base_date = base_dates.pop()
        else:
            base_date = next(iter(base_dates), None)
            
        if base_date is None:
            self.restart_counter += 1
            message = "Couldn't find Date input element."
            self.log_error(message)
            raise ValueError(message)

        date = lambda: self.driver.find_element_by_xpath(xpath_soup(base_date))
        self.double_click(date())
        self.send_keys(date(), Keys.HOME)
        self.send_keys(date(), self.config.date)

        print("Filling Group")
        group_elements = self.web_scrap(term="[name='cGroup'] input, [name='__cGroup'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)
        if len(group_elements) > 1:
            group_element = group_elements.pop()
        else:
            group_element = next(iter(group_elements), None)

        if group_element is None:
            self.restart_counter += 1
            message = "Couldn't find Group input element."
            self.log_error(message)
            raise ValueError(message)
        
        group = lambda: self.driver.find_element_by_xpath(xpath_soup(group_element))
        self.double_click(group())
        self.send_keys(group(), Keys.HOME)
        self.send_keys(group(), self.config.group)

        print("Filling Branch")
        branch_elements = self.web_scrap(term="[name='cFil'] input, [name='__cFil'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)
        if len(branch_elements) > 1:
            branch_element = branch_elements.pop()
        else:
            branch_element = next(iter(branch_elements), None)
        if branch_element is None:
            self.restart_counter += 1
            message = "Couldn't find Branch input element."
            self.log_error(message)
            raise ValueError(message)

        branch = lambda: self.driver.find_element_by_xpath(xpath_soup(branch_element))
        self.double_click(branch())
        self.send_keys(branch(), Keys.HOME)
        self.send_keys(branch(), self.config.branch)

        print("Filling Environment")
        environment_elements = self.web_scrap(term="[name='cAmb'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)
        if len(environment_elements) > 1:
            environment_element = environment_elements.pop()
        else:
            environment_element = next(iter(environment_elements), None)
        if environment_element is None:
            self.restart_counter += 1
            message = "Couldn't find Module input element."
            self.log_error(message)
            raise ValueError(message)


        env = lambda: self.driver.find_element_by_xpath(xpath_soup(environment_element))
        if ("disabled" not in environment_element.parent.attrs["class"] and env().is_enabled()):
            env_value = self.get_web_value(env())
            endtime = time.time() + self.config.time_out
            while (time.time() < endtime and env_value != self.config.module):
                self.double_click(env())
                self.send_keys(env(), Keys.HOME)
                self.send_keys(env(), self.config.module)
                env_value = self.get_web_value(env())
                time.sleep(1)

        buttons = self.filter_displayed_elements(self.web_scrap(label, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container="body"), True)
        button_element = next(iter(buttons), None) if buttons else None

        if button_element  and hasattr(button_element, "name") and hasattr(button_element, "parent"):
            button = lambda: self.driver.find_element_by_xpath(xpath_soup(button_element))
            self.click(button())
        elif not change_env:
            self.restart_counter += 1
            message = f"Couldn't find {label} button."
            self.log_error(message)
            raise ValueError(message)

        self.wait_element(term=self.language.database, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="input", main_container=container)             
            
    def ChangeEnvironment(self, date="", group="", branch="", module=""):
        """
        Clicks on the change environment area of Protheus Webapp and
        fills the environment screen.

        :param date: The date to fill on the environment screen. - **Default:** "" (empty string)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "" (empty string)
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "" (empty string)
        :type branch: str
        :param module: The module to fill on the environment screen. - **Default:** "" (empty string)
        :type module: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ChangeEnvironment(date="13/11/2018", group="T1", branch="D MG 01 ")
        """
        if date:
            self.config.date = date
        if group:
            self.config.group = group
        if branch:
            self.config.branch = branch
        if module:
            self.config.module = module

        element = self.change_environment_element_home_screen()
        if element:
            self.click(self.driver.find_element_by_xpath(xpath_soup(element)))
            self.environment_screen(True)
        else:
            self.log_error("Change Envirioment method did not find the element to perform the click or the element was not visible on the screen.")

        self.close_coin_screen()
        
    def change_environment_element_home_screen(self):
        """
        [Internal]

        This method wait the element to perform ChangeEnvirionmentm return a soup element.

        Usage:

        >>> # Calling the method:
        >>> self.change_environment_element_home_screen()
        """
        endtime = time.time() + self.config.time_out
        while time.time() < endtime:

            if self.wait_element_timeout(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, timeout = 1, optional_term="button", main_container="body"):
                return next(iter(self.web_scrap(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container="body")), None)
            elif self.wait_element_timeout(term=".tpanel > .tpanel > .tbutton", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = 1, main_container="body"):
                tbuttons = self.filter_displayed_elements(self.web_scrap(term=".tpanel > .tpanel > .tbutton", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"), True)
                element = next(iter(list(filter(lambda x: 'TOTVS' in x.text, tbuttons))), None)
                if element:
                    return element

        return False

    def close_modal(self):
        """
        [Internal]

        This method closes the modal in the opening screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_modal()
        """
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".tmodaldialog"), True)
        if modals and self.element_exists(term=".tmodaldialog .tbrowsebutton", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body", check_error = False):
            buttons = modals[0].select(".tbrowsebutton")
            if buttons:
                close_button = next(iter(list(filter(lambda x: x.text == self.language.close, buttons))), None)
                time.sleep(0.5)
                selenium_close_button = lambda: self.driver.find_element_by_xpath(xpath_soup(close_button))
                if close_button:
                    try:
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = close_button , locator = By.XPATH)
                        self.click(selenium_close_button())
                    except:
                        pass

    def close_coin_screen(self):
        """
        [Internal]

        Closes the coin screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_coin_screen()
        """
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".tmodaldialog"), True)
        if modals and self.element_exists(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
         optional_term=".tmodaldialog > .tpanel > .tsay", main_container="body", check_error = False):
            self.SetButton(self.language.confirm)

    def close_coin_screen_after_routine(self):
        """
        [internal]
        This method is responsible for closing the "coin screen" that opens after searching for the routine
        """
        endtime = time.time() + self.config.time_out

        self.wait_element_timeout(term=".workspace-container", scrap_type=enum.ScrapType.CSS_SELECTOR,
            timeout = self.config.time_out, main_container="body", check_error = False)

        tmodaldialog_list = []

        while(time.time() < endtime and not tmodaldialog_list):
            try:
                soup = self.get_current_DOM()
                tmodaldialog_list = soup.select('.tmodaldialog')

                self.wait_element_timeout(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=10, main_container = "body", check_error = False)
                 
                tmodal_coin_screen = next(iter(self.web_scrap(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
                    optional_term=".tmodaldialog > .tpanel > .tsay", main_container="body", check_error = False, check_help = False)), None)

                if tmodal_coin_screen and tmodal_coin_screen in tmodaldialog_list:
                    tmodaldialog_list.remove(tmodal_coin_screen.parent.parent)
                    
                self.close_coin_screen()
                
            except Exception as e:
                print(str(e))
        
        
    def close_resolution_screen(self):
        """
        [Internal]

        Closes the Alert of resolution screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_resolution_screen()
        """
        endtime = time.time() + self.config.time_out
        container = self.get_current_container()
        while (time.time() < endtime and container and self.element_exists(term="img[src*='fwskin_alert_ico.png']", scrap_type=enum.ScrapType.CSS_SELECTOR)):
            self.SetButton(self.language.close)
            time.sleep(1)
        self.wait_element_timeout(term="[name='cGetUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out, main_container='body')

    def set_log_info(self):
        """
        [Internal]
        Fills the log information needed by opening the About page.

        Usage:

        >>> # Calling the method:
        >>> self.set_log_info()
        """
        self.SetLateralMenu(self.language.menu_about, save_input=False)
        self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        self.wait_until_to(expected_condition = "presence_of_all_elements_located", element = ".tmodaldialog", locator= By.CSS_SELECTOR)

        soup = self.get_current_DOM()
        labels = list(soup.select(".tmodaldialog .tpanel .tsay"))

        release_element = next(iter(filter(lambda x: x.text.startswith("Release"), labels)), None)
        database_element = next(iter(filter(lambda x: x.text.startswith("Top DataBase"), labels)), None)
        lib_element = next(iter(filter(lambda x: x.text.startswith("Versão da lib"), labels)), None)
        build_element = next(iter(filter(lambda x: x.text.startswith("Build"), labels)), None)

        if release_element:
            release = release_element.text.split(":")[1].strip()
            self.log.release = release
            self.log.version = release.split(".")[0]

        if database_element:
            self.log.database = database_element.text.split(":")[1].strip()

        if build_element:
            self.log.build_version = build_element.text.split(":")[1].strip()

        if lib_element:
            self.log.lib_version = lib_element.text.split(":")[1].strip()

        self.SetButton(self.language.close, ratio=4.0)

    def set_log_info_tss(self):

        self.log.country = self.config.country
        self.log.execution_id = self.config.execution_id
        self.log.issue = self.config.issue

        label_element = None

        self.SetButton("Sobre")
        
        soup = self.get_current_DOM()
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not label_element):
            soup = self.get_current_DOM()
            label_element = soup.find_all("label", string="Versão do TSS:") 
               
        if not label_element:
            raise ValueError("SetupTss fail about screen not found")
            
        labels = list(map(lambda x: x.text, soup.select("label")))
        label = labels[labels.index("Versão do TSS:")+1]
        self.log.release = next(iter(re.findall(r"[\d.]*\d+", label)), None)

        self.SetButton('x')

    def get_language(self):
        """
        [Internal]

        Gets the current language of the html.

        :return: The current language of the html.
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> language = self.get_language()
        """
        language = self.driver.find_element(By.CSS_SELECTOR, "html").get_attribute("lang")
        return language

    def Program(self, program_name):
        """
        Method that sets the program in the initial menu search field.

        .. note::
            Only used when the Initial Program is the module Ex: SIGAFAT.

        :param program_name: The program name
        :type program_name: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Program("MATA020")
        """
        self.config.routine = program_name
        
        if not self.log.program:
            self.log.program = program_name
        self.set_program(program_name)

    def set_program(self, program):
        """
        [Internal]

        Method that sets the program in the initial menu search field.

        :param program: The program name
        :type program: str

        Usage:

        >>> # Calling the method:
        >>> self.set_program("MATA020")
        """
        try:
            print(f"Setting program: {program}")
            self.wait_element(term="[name=cGet] > input", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            soup = self.get_current_DOM()
            tget = next(iter(soup.select("[name=cGet]")), None)
            tget_input = next(iter(tget.select("input")), None)
            if tget:
                tget_img = next(iter(tget.select("img")), None)

                if tget_img is None:
                    self.log_error("Couldn't find Program field.")

                s_tget = lambda : self.driver.find_element_by_xpath(xpath_soup(tget_input))
                s_tget_img = lambda : self.driver.find_element_by_xpath(xpath_soup(tget_img))

                self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH )
                self.double_click(s_tget())
                self.set_element_focus(s_tget())
                self.send_keys(s_tget(), Keys.HOME)
                ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH )
                self.send_keys(s_tget(), program)
                current_value = self.get_web_value(s_tget()).strip()

                endtime = time.time() + self.config.time_out
                while(time.time() < endtime and current_value != program):
                    self.send_keys(s_tget(), Keys.BACK_SPACE)
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH, timeout=True)
                    self.send_keys(s_tget(), program)
                    current_value = self.get_web_value(s_tget()).strip()
                
                if current_value.strip() != program.strip():
                    self.log_error(f"Couldn't fill program input - current value:  {current_value} - Program: {program}")
                self.set_element_focus(s_tget_img())
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH )
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_img, locator = By.XPATH )
                self.send_action(self.click, s_tget_img, ratio=9.0)
                self.wait_element_is_not_displayed(tget_img)

            if self.config.initial_program.lower() == 'sigaadv':
                self.close_coin_screen_after_routine()

        except AssertionError as error:
            print(f"Warning set program raise AssertionError: {str(error)}")
            raise error
        except Exception as e:
            self.log_error(str(e))

    def standard_search_field(self, term, name_attr=False,send_key=False):
        """
        [Internal]
        
        Do the standard query(F3) 
        this method 
        1.Search the field
        2.Search icon "lookup"
        3.Click()

        :param term: The term that must be searched.
        :type term: str
        :param name_attr: If true searchs element by name.
        :type name_attr: bool
        :param send_key: Try open standard search field send key F3 (no click).
        :type send_key: bool

        Usage:

        >>> # To search using a label name:
        >>> self.standard_search_field(name_label)
        >>> #------------------------------------------------------------------------
        >>> # To search using the name of input:
        >>> self.standard_search_field(field='A1_EST',name_attr=True)
        >>> #------------------------------------------------------------------------
        >>> # To search using the name of input and do action with a key:
        >>> oHelper.F3(field='A1_EST',name_attr=True,send_key=True)
        """
        endtime = self.config.time_out + time.time()

        try:
            #wait element
            if name_attr:
                self.wait_element(term=f"[name$='{term}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                self.wait_element(term)
            # find element
            element = self.get_field(term,name_attr).find_parent()
            if not(element):
                raise Exception("Couldn't find element")

            print("Field successfully found")
            if(send_key):
                input_field = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                self.set_element_focus(input_field())
                container = self.get_current_container()
                self.send_keys(input_field(), Keys.F3)
            else:
                icon = next(iter(element.select("img[src*=fwskin_icon_lookup], img[src*=btpesq_mdi]")),None)
                icon_s = self.soup_to_selenium(icon)
                container = self.get_current_container()
                self.click(icon_s)

            container_end = self.get_current_container()
            if (container['id']  == container_end['id']):
                input_field = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                self.set_element_focus(input_field())
                self.send_keys(input_field(), Keys.F3)
            
            while( time.time() < endtime and container['id']  == container_end['id']):
                container_end = self.get_current_container()
                time.sleep(0.01)

            if time.time() > endtime:
                print("Timeout: new container not found.")
            else:
                print("Success")
                
        except Exception as e:
            self.log_error(str(e))
   
    def SearchBrowse(self, term, key=None, identifier=None, index=False, column=None):
        """
        Searchs a term on Protheus Webapp.

        It will search using the default search key, but if a **key** is provided
        it will search using the chosen key.

        It will search using the first search box on the screen, but if an **identifier**
        is provided, it will search on the chosen search box.

        :param term: The term that must be searched.
        :type term: str
        :param key: The search key to be chosen on the search dropdown. - **Default:** None
        :type key: str
        :param identifier: The identifier of the search box. If none is provided, it defaults to the first of the screen. - **Default:** None
        :type identifier: str
        :param index: Whether the key is an index or not. - **Default:** False
        :type index: bool

        Usage:

        >>> # To search using the first search box and default search key:
        >>> oHelper.SearchBrowse("D MG 001")
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen key:
        >>> oHelper.SearchBrowse("D MG 001", key="Branch+id")
        >>> #------------------------------------------------------------------------
        >>> # To search using a chosen search box and the default search key:
        >>> oHelper.SearchBrowse("D MG 001", identifier="Products")
        >>> #------------------------------------------------------------------------
        >>> # To search using a chosen search box and a chosen search key:
        >>> oHelper.SearchBrowse("D MG 001", key="Branch+id", identifier="Products")
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen column:
        >>> oHelper.SearchBrowse("D MG 001", column="Branch+id")
        >>> #------------------------------------------------------------------------
        """

        self.wait_blocker()

        print(f"Searching: {term}")
        if index and isinstance(key, int):
            key -= 1
        browse_elements = self.get_search_browse_elements(identifier)
        if key:
            self.search_browse_key(key, browse_elements, index)	            
        elif column:
            self.search_browse_column(column, browse_elements, index)	
        self.fill_search_browse(term, browse_elements)

    def get_search_browse_elements(self, panel_name=None):
        """
        [Internal]

        Returns a tuple with the search browse elements in this order:
        Key Dropdown, Input, Icon.

        :param panel_name: The identifier of the search box. If none is provided, it defaults to the first of the screen. - **Default:** None
        :type panel_name: str

        :return: Tuple with the Key Dropdown, Input and Icon elements of a search box
        :rtype: Tuple of Beautiful Soup objects.

        Usage:

        >>> # Calling the method:
        >>> search_elements = self.get_search_browse_elements("Products")
        """
        success = False
        container = None
        elements_soup = None
        
        self.wait_element_timeout(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out)
        endtime = time.time() + self.config.time_out
        
        while (time.time() < endtime and not success): 
            soup = self.get_current_DOM()
            search_index = self.get_panel_name_index(panel_name) if panel_name else 0
            containers = self.zindex_sort(soup.select(".tmodaldialog"), reverse=True) 
            container = next(iter(containers), None)
            
            if container:
                elements_soup = container.select("[style*='fwskin_seekbar_ico']")

            if elements_soup:
                if elements_soup and len(elements_soup) -1 >= search_index:
                    browse_div = elements_soup[search_index].find_parent().find_parent()
                    success = True
            
        if not elements_soup:
            self.log_error("Couldn't find element_soup.")

        if not container:
            self.log_error("Couldn't find container of element.")

        if not success:
            self.log_error("Get search browse elements couldn't find browser div")

        browse_tget = browse_div.select(".tget")[0]
        browse_key = browse_div.select(".tbutton button")[0]
        browse_input = browse_tget.select("input")[0]
        browse_icon = browse_tget.select("img")[0]

        return (browse_key, browse_input, browse_icon)

    def search_browse_key(self, search_key, search_elements, index=False):
        """
        [Internal]

        Chooses the search key to be used during the search.

        :param search_key: The search key to be chosen on the search dropdown
        :type search_key: str
        :param search_elements: Tuple of Search elements
        :type search_elements: Tuple of Beautiful Soup objects
        :param index: Whether the key is an index or not.
        :type index: bool

        Usage:

        >>> #Preparing the tuple:
        >>> search_elements = self.get_search_browse_elements("Products")
        >>> # Calling the method:
        >>> self.search_browse_key("Branch+Id", search_elements)

        """
        success = False

        if index and not isinstance(search_key, int):
            self.log_error("If index parameter is True, key must be a number!")

        sel_browse_key = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[0]))
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[0], locator = By.XPATH)
        self.set_element_focus(sel_browse_key())
        self.click(sel_browse_key())

        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.driver.switch_to.default_content()
            content = self.driver.page_source
            soup = BeautifulSoup(content,"html.parser")
        else:
            soup = self.get_current_DOM()

        if not index:

            search_key = re.sub(r"\.+$", '', search_key.strip()).lower()

            tradiobuttonitens = soup.select(".tradiobuttonitem input")
            tradiobuttonitens_ends_dots = list(filter(lambda x: re.search(r"\.\.$", x.next.text), tradiobuttonitens))
            tradiobuttonitens_not_ends_dots = list(filter(lambda x: not re.search(r"\.\.$", x.next.text), tradiobuttonitens))

            if tradiobuttonitens_not_ends_dots:
                radio = next(iter(list(filter(lambda x: search_key in re.sub(r"\.+$", '', x.next.text.strip()).lower() , tradiobuttonitens_not_ends_dots))), None)
                if radio:
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = radio, locator = By.XPATH )
                    self.click(self.soup_to_selenium(radio))
                    success = True
            if tradiobuttonitens_ends_dots and not success and self.config.initial_program.lower() != "sigaadv":

                for element in tradiobuttonitens_ends_dots:

                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH )
                    selenium_input = lambda : self.soup_to_selenium(element)
                    self.click(selenium_input())
                    time.sleep(1)

                    try_get_tooltip = 0

                    while (not success and try_get_tooltip < 3):
                        success = self.check_element_tooltip(element, search_key, contains=True)
                        try_get_tooltip += 1
                        
                    if success:
                        break
                    elif self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
                        self.driver.switch_to.default_content()
                        content = self.driver.page_source
                        soup = BeautifulSoup(content,"html.parser")
                    else:
                        pass
            if tradiobuttonitens_ends_dots and not success and self.config.initial_program.lower() == "sigaadv":
                for element in tradiobuttonitens_ends_dots:

                    old_value = self.search_browse_key_input_value(search_elements[1])

                    if tradiobuttonitens.index(element) == 0:
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = tradiobuttonitens_ends_dots[1], locator = By.XPATH )
                        self.click(self.soup_to_selenium(tradiobuttonitens_ends_dots[1]))
                        
                        while(old_value == self.search_browse_key_input_value(search_elements[1])):
                            time.sleep(0.1)
                        old_value = self.search_browse_key_input_value(search_elements[1])

                        if not self.driver.find_elements_by_css_selector(".tradiobuttonitem input"):
                            self.get_current_DOM()
                            self.set_element_focus(sel_browse_key())
                            self.click(sel_browse_key())
                            self.driver.switch_to.default_content()

                    
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH )
                    self.click(self.soup_to_selenium(element))
                    
                    while(old_value == self.search_browse_key_input_value(search_elements[1])):
                        time.sleep(0.1)
                    success = search_key.lower().strip() in self.search_browse_key_input_value(search_elements[1]).strip().lower()

                    if success:
                        break
                    else:
                        pass
                        
            if not success:
                self.log_error(f"Couldn't search the key: {search_key} on screen.")
                    
        else:
            tradiobuttonitens = soup.select(".tradiobuttonitem input")
            if len(tradiobuttonitens) < search_key + 1:
                self.log_error("Key index out of range.")
            trb_input = tradiobuttonitens[search_key]

            sel_input = lambda: self.driver.find_element_by_xpath(xpath_soup(trb_input))
            self.wait_until_to( expected_condition = "element_to_be_clickable", element = trb_input, locator = By.XPATH )
            self.click(sel_input())

    def search_browse_column(self, search_column, search_elements, index=False):
        """
        [Internal]

        Chooses the search key to be used during the search.

        :param search_column: The search Column to be chosen on the search dropdown
        :type search_column: str
        :param search_elements: Tuple of Search elements
        :type search_elements: Tuple of Beautiful Soup objects
        :param index: Whether the key is an index or not.
        :type index: bool

        Usage:

        >>> #Preparing the tuple:
        >>> search_elements = self.get_search_browse_elements("Products")
        >>> # Calling the method:
        >>> self.search_browse_key("Filial*", search_elements)
        """


        if index and not isinstance(search_column, int):
            self.log_error("If index parameter is True, column must be a number!")
        sel_browse_column = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[0]))
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[0], locator = By.XPATH)
        self.set_element_focus(sel_browse_column())
        self.click(sel_browse_column())

        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.tmenu_out_iframe = True
        
        self.wait_element_timeout(".tmenupopup.activationOwner", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=5.0, step=0.1, presence=True, position=0)
        tmenupopup = next(iter(self.web_scrap(".tmenupopup.activationOwner", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container = "body")), None)

        if not tmenupopup:
            if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
                self.tmenu_out_iframe = False
            self.log_error("SearchBrowse - Column: couldn't find the new menupopup")

        self.click(self.soup_to_selenium(tmenupopup.select('a')[1]))
        spans = tmenupopup.select("span")
        
        if ',' in search_column:
            search_column_itens = search_column.split(',')
            filtered_column_itens = list(map(lambda x: x.strip(), search_column_itens))
            for  item in filtered_column_itens:
                span = next(iter(list(filter(lambda x: x.text.lower().strip() == item.lower(),spans))), None)
                if not span:
                    span = next(iter(list(filter(lambda x: x.text.lower().replace(" ","") == search_column.lower().replace(" ","") ,spans))), None)
                self.click(self.soup_to_selenium(span))
        else:
            span = next(iter(list(filter(lambda x: x.text.lower().strip() == search_column.lower().strip() ,spans))), None)
            if not span:
                span = next(iter(list(filter(lambda x: x.text.lower().replace(" ","") == search_column.lower().replace(" ","") ,spans))), None)

            self.click(self.soup_to_selenium(span))

        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.tmenu_out_iframe = False

    def fill_search_browse(self, term, search_elements):
        """
        [Internal]

        Fills search input method and presses the search button.

        :param term: The term to be searched
        :type term: str
        :param search_elements: Tuple of Search elements
        :type search_elements: Tuple of Beautiful Soup objects

        Usage:

        >>> #Preparing the tuple:
        >>> search_elements = self.get_search_browse_elements("Products")
        >>> # Calling the method:
        >>> self.fill_search_browse("D MG 01", search_elements)
        """
        self.wait_blocker()
        endtime = time.time() + self.config.time_out
        sel_browse_input = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[1]))
        sel_browse_icon = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[2]))

        current_value = self.get_element_value(sel_browse_input())

        while (time.time() < endtime and current_value.rstrip() != term.strip()):
            try:
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[2], locator = By.XPATH, timeout=True)
                self.click(sel_browse_input())
                self.set_element_focus(sel_browse_input())
                self.send_keys(sel_browse_input(), Keys.DELETE)
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[1], locator = By.XPATH, timeout=True)
                sel_browse_input().clear()
                self.set_element_focus(sel_browse_input())
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[1], locator = By.XPATH, timeout=True)
                sel_browse_input().send_keys(term.strip())
                current_value = self.get_element_value(sel_browse_input())
            except StaleElementReferenceException:
                    self.get_search_browse_elements()
            except:
                pass
        if current_value.rstrip() != term.strip():
            self.log_error(f"Couldn't search f{search_elements}  current value is {current_value.rstrip()}")
        self.send_keys(sel_browse_input(), Keys.ENTER)
        self.wait_blocker()
        self.double_click(sel_browse_icon())
        return True

    def search_browse_key_input_value(self, browse_input ):
        """
        [Internal]

        Get the search browse input value
        """
        self.get_current_DOM()
        input_value = self.soup_to_selenium(browse_input).get_attribute('value')
        self.driver.switch_to.default_content()
        return input_value
        

    
    def wait_blocker(self):
        """
        [Internal]
        
        Wait blocker disappear

        """

        print("Waiting blocker to continue...")
        soup = None
        result = True
        endtime = time.time() + 300

        while(time.time() < endtime and result):
            blocker_container = None
            blocker = None
            soup = self.get_current_DOM()
            blocker_container = self.blocker_containers(soup)
            if blocker_container:
                blocker = soup.select('.ajax-blocker') if len(soup.select('.ajax-blocker')) > 0 else \
                    'blocked' in blocker_container.attrs['class'] if blocker_container and hasattr(blocker_container, 'attrs') else None
                
            if blocker:
                result = True
            else:
                return False
        return result

    def blocker_containers(self, soup):
        """
        Return The container index by z-index and filter if it is displayed

        :param soup: soup object
        :return: The container index by z-index and filter if it is displayed
        """

        try:
            containers = self.zindex_sort(soup.select(self.containers_selectors["BlockerContainers"]), True)

            if containers:
                containers_filtered = list(filter(lambda x: self.element_is_displayed(x), containers))
                if containers_filtered:
                    return next(iter(containers_filtered), None)
                else:
                    return None
            else:
                return None
                       
        except AttributeError as e:
            print(f"Warning: wait_blocker > blocker_containers Exeception (AttributeError)\n {str(e)}")
        except Exception as e:
            print(f"Warning: wait_blocker > blocker_containers Exeception {str(e)}")

            
    def get_panel_name_index(self, panel_name):
        """
        [Internal]

        Gets the index of search box element based on the panel name associated with it.

        :param panel_name:
        :type panel_name:

        :return: The index of the search box starting with 0
        :rtype: int

        Usage:

        >>> # Calling the method:
        >>> index = self.get_panel_name_index("Products")
        """
        soup = self.get_current_DOM()
        panels = soup.select(".tmodaldialog > .tpanelcss > .tpanelcss")
        tsays = list(map(lambda x: x.select(".tsay"), panels))
        label = next(iter(list(filter(lambda x: x.text.lower() == panel_name.lower(), tsays)), None))
        return tsays.index(label)

    def search_element_position(self, field, position=1, input_field=True, direction=None):
        """
        [Internal]
        Usage:
        >>> # Calling the method
        >>> self.search_element_position(field)
        """
        endtime = (time.time() + self.config.time_out)
        label = None
        elem = []
        term=".tget, .tcombobox, .tmultiget"
        position-=1

        if not input_field:
            term=".tsay"

        try:
            while( time.time() < endtime and not label ):
                container = self.get_current_container()
                labels = container.select("label")
                labels_displayed = list(filter(lambda x: self.element_is_displayed(x) ,labels))
                labels_list  = list(filter(lambda x: re.search(r"^{}([^a-zA-Z0-9]+)?$".format(re.escape(field)),x.text) ,labels_displayed))
                labels_list_filtered = list(filter(lambda x: 'th' not in self.element_name(x.parent.parent) , labels_list))
                if labels_list_filtered and len(labels_list_filtered) -1 >= position:
                    label = labels_list_filtered[position]

            if not label:
                self.log_error(f"Label: '{field}'' wasn't found.")

            self.wait_until_to( expected_condition = "element_to_be_clickable", element = label, locator = By.XPATH )
            
            container_size = self.get_element_size(container['id'])
            # The safe values add to postion of element
            width_safe  = (container_size['width']  * 0.015)
            height_safe = (container_size['height'] * 0.01)

            label_s  = lambda:self.soup_to_selenium(label)
            xy_label =  self.driver.execute_script('return arguments[0].getPosition()', label_s())
            list_in_range = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR) 
            list_in_range = list(filter(lambda x: self.element_is_displayed(x) and 'readonly' not in self.soup_to_selenium(x).get_attribute("class") or 'readonly focus' in self.soup_to_selenium(x).get_attribute("class"), list_in_range))

            if not input_field:
                list_in_range = list(filter(lambda x: field.strip().lower() != x.text.strip().lower(), list_in_range))

            position_list = list(map(lambda x:(x[0], self.get_position_from_bs_element(x[1])), enumerate(list_in_range)))
            position_list = self.filter_by_direction(xy_label, width_safe, height_safe, position_list, direction)
            distance      = self.get_distance_by_direction(xy_label, position_list, direction)
            elem          = min(distance, key = lambda x: x[1])
            elem          = list_in_range[elem[0]]

            if not elem:
                self.log_error(f"Label '{field}' wasn't found")
            return elem
            
        except AssertionError as error:
            raise error
        except Exception as error:
            print(error)
            self.log_error(str(error))


    def get_position_from_bs_element(self,element):
        """
        [Internal]

        """
        selenium_element = self.soup_to_selenium(element)
        position = self.driver.execute_script('return arguments[0].getPosition()', selenium_element)
        return position

    def get_distance(self,label_pos,element_pos):
        """
        [internal]

        """
        return sqrt((pow(element_pos['x'] - label_pos['x'], 2)) + pow(element_pos['y'] - label_pos['y'],2))

    def get_element_size(self, id):
        """
        Internal
        Return Height/Width

        """
        script = f'return document.getElementById("{id}").offsetHeight;'
        height = self.driver.execute_script(script)
        script = f'return document.getElementById("{id}").offsetWidth;'
        width  = self.driver.execute_script(script)
        return {'height': height, 'width':width}

    def get_distance_x(self, x_label, x_element):
        """
        [Internal]

        """

        return (x_element['x'] - x_label['x'])

    def get_distance_y(self, y_label, y_element):
        """
        [Internal]

        """

        return (y_element['y'] - y_label['y'])

    def filter_by_direction(self, xy_label, width_safe, height_safe, position_list, direction):
        """
        [Internal]
        
        """

        if not direction:

            return list(filter(lambda xy_elem: (
                        xy_elem[1]['y'] + width_safe >= xy_label['y'] and xy_elem[1]['x'] + height_safe >= xy_label['x']),
                        position_list))

        elif direction.lower() == 'right':
            return list(filter(
                lambda xy_elem: (xy_elem[1]['x'] > xy_label['x']) and (xy_elem[1]['y'] >= xy_label['y'] - height_safe and xy_elem[1]['y'] <= xy_label[
                    'y'] + height_safe), position_list))
        
        elif direction.lower() == 'down':
            return list(filter(
                lambda xy_elem: (xy_elem[1]['y'] > xy_label['y']) and (xy_elem[1]['x'] + width_safe >= xy_label['x'] and
                               xy_elem[1]['x'] - width_safe <= xy_label['x']), position_list))

    def get_distance_by_direction(self, xy_label, position_list, direction):
        
        if not direction:
            get_distance = self.get_distance
        
        elif direction.lower() == 'right':
            get_distance = self.get_distance_x

        elif direction.lower() == 'down':
            get_distance = self.get_distance_y
        
        return list(map(lambda x: (x[0], get_distance(xy_label, x[1])), position_list))

    def SetValue(self, field, value, grid=False, grid_number=1, ignore_case=True, row=None, name_attr=False, position = 1, check_value=True):
        """
        Sets value of an input element.
        
        .. note::
            Attention on the grid use the field mask.
         
        :param field: The field name or label to receive the value
        :type field: str
        :param value: The value to be inputted on the element.
        :type value: str or bool
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param grid_number: Grid number of which grid should be inputted when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param ignore_case: Boolean if case should be ignored or not. - **Default:** True
        :type ignore_case: bool
        :param check_value: Boolean ignore input check - **Default:** True
        :type name_attr: bool
        :param row: Row number that will be filled
        :type row: int
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool

        Usage:

        >>> # Calling method to input value on a field:
        >>> oHelper.SetValue("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is a grid:
        >>> oHelper.SetValue("Client", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to checkbox value on a field that is a grid:
        >>> oHelper.SetValue('Confirmado?', True, grid=True)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is on the second grid of the screen:
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is a grid *Will not attempt to verify the entered value. Run only once.* :
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2, check_value = False)
        >>> oHelper.LoadGrid()
        """
        if grid:
            self.input_grid_appender(field, value, grid_number - 1, row = row, check_value = check_value)
        elif isinstance(value, bool):
            self.click_check_radio_button(field, value, name_attr, position)
        else:
            self.input_value(field, value, ignore_case, name_attr, position, check_value)

    def input_value(self, field, value, ignore_case=True, name_attr=False, position=1, check_value=True):
        """
        [Internal]

        Sets value of an input element.
        Returns True if succeeded, False if it failed.

        :param field: The field name or label to receive the value
        :type field: str
        :param value: The value to be set on the field
        :type value: str
        :param ignore_case: Boolean if case should be ignored or not. - **Default:** True
        :type ignore_case: bool
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool
        :param check_value: Boolean ignore input check - **Default:** True
        :type name_attr: bool
        :returns: True if succeeded, False if it failed.
        :rtype: bool

        Usage:

        >>> # Calling the method
        >>> self.input_value("A1_COD", "000001")
        """

        field = re.sub(r"([\s\?:\*\.]+)?$", "", field).strip()

        main_element = None

        if name_attr:
            self.wait_element(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        else:
            self.wait_element(field)

        success = False
        endtime = time.time() + self.config.time_out

        while(time.time() < endtime and not success):
            unmasked_value = self.remove_mask(value)

            print(f"Looking for element: {field}")

            if field.lower() == self.language.From.lower():
                element = self.get_field("cDeCond", name_attr=True)
            elif field.lower() == self.language.To.lower():
                element = self.get_field("cAteCond", name_attr=True)
            else:
                element = self.get_field(field, name_attr, position)

            if not element:
                continue

            main_element = element

            if "tmultiget" in element.attrs['class'] if self.element_name(element) == 'div' else None:
                textarea = element.select("textarea")
                if not textarea:
                    input_field = lambda : self.soup_to_selenium(element)
                else:
                    input_field = lambda : self.soup_to_selenium(next(iter(textarea), None))
            else:
                input_field = lambda : self.soup_to_selenium(element)
            
            if input_field:
                valtype = "C"
                main_value = unmasked_value if value != unmasked_value and self.check_mask(input_field()) else value

                interface_value = self.get_web_value(input_field())
                current_value = interface_value.strip()
                interface_value_size = len(interface_value)
                user_value_size = len(value)

                if self.element_name(element) == "input":
                    valtype = element.attrs["valuetype"]

                self.scroll_to_element(input_field())

                try:
                    #Action for Combobox elements
                    if ((hasattr(element, "attrs") and "class" in element.attrs and "tcombobox" in element.attrs["class"]) or
                    (hasattr(element.find_parent(), "attrs") and "class" in element.find_parent().attrs and "tcombobox" in element.find_parent().attrs["class"])):
                        self.set_element_focus(input_field())
                        main_element = element.parent
                        self.try_element_to_be_clickable(main_element)
                        self.select_combo(element, main_value)
                        current_value = self.get_web_value(input_field()).strip()
                    #Action for Input elements
                    else:
                        self.wait_until_to( expected_condition = "visibility_of", element = input_field, timeout=True)
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                        self.double_click(input_field())

                        #if Character input
                        if valtype != 'N':
                            self.set_element_focus(input_field())
                            self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                            self.send_keys(input_field(), Keys.HOME)
                            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
                            time.sleep(0.1)
                            if main_value == '':
                                ActionChains(self.driver).move_to_element(input_field()).send_keys_to_element(input_field(), " ").perform()
                            else:
                                self.wait_blocker()
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                                ActionChains(self.driver).move_to_element(input_field()).send_keys_to_element(input_field(), main_value).perform()
                        #if Number input
                        else:
                            tries = 0
                            try_counter = 1
                            while(tries < 3):
                                self.set_element_focus(input_field())
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                                self.try_send_keys(input_field, main_value, try_counter)
                                current_number_value = self.get_web_value(input_field())
                                if self.remove_mask(current_number_value).strip() == main_value:
                                    break
                                tries+=1
                                try_counter+=1

                        if user_value_size < interface_value_size:
                            self.send_keys(input_field(), Keys.ENTER)
                            if not check_value:
                                return

                        if self.check_mask(input_field()):
                            current_value = self.remove_mask(self.get_web_value(input_field()).strip())
                            if re.findall(r"\s", current_value):
                                current_value = re.sub(r"\s", "", current_value)
                        else:
                            current_value = self.get_web_value(input_field()).strip()

                        if current_value != "" and current_value.encode('latin-1', 'ignore'):
                            print(f"Current field value: {current_value}")

                    if ((hasattr(element, "attrs") and "class" in element.attrs and "tcombobox" in element.attrs["class"]) or
                    (hasattr(element.find_parent(), "attrs") and "class" in element.find_parent().attrs and "tcombobox" in element.find_parent().attrs["class"])):
                        current_value = current_value[0:len(str(value))]

                    if re.match(r"^●+$", current_value):
                        success = len(current_value) == len(str(value).strip())
                    elif ignore_case:
                        success = current_value.lower().strip() == main_value.lower().strip()
                    else:
                        success = current_value == main_value
                except:
                    continue

        if "disabled" in element.attrs:
            self.log_error(self.create_message(['', field],enum.MessageType.DISABLED))

        if not success:
            self.log_error(f"Could not input value {value} in field {field}")
        else:
            self.wait_until_to( expected_condition = "element_to_be_clickable", element = main_element, locator = By.XPATH )

    def get_field(self, field, name_attr=False, position=1, input_field=True, direction=None):
        """
        [Internal]

        This method decides if field would be found by either it's name or by it's label.
        Internal method of input_value and CheckResult.

        :param field: Field name or field label to be searched
        :type field: str
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool

        :return: Field element
        :rtype: Beautiful Soup object

        Usage:

        >>> # Calling the method:
        >>> element1 = self.get_field("A1_COD")
        >>> element2 = self.get_field("Product")
        """
        endtime = time.time() + self.config.time_out
        element =  None

        if re.match(r"\w+(_)", field) or name_attr:
            position -= 1

        while(time.time() < endtime and element is None):
            if re.match(r"\w+(_)", field) or name_attr:
                element_list = self.web_scrap(f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
                if element_list and len(element_list) -1 >= position:
                    element = element_list[position]
            else:
                element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True, input_field=input_field, direction=direction, position=position)), None)

        if element:
            element_children = next((x for x in element.contents if self.element_name(x) in ["input", "select"]), None)
            return element_children if element_children is not None else element
        else:
            self.log_error("Element wasn't found.")

    def get_web_value(self, element):
        """
        [Internal]

        Gets the current value or text of element.

        :param element: The element to get value or text from
        :type element: Selenium object

        :return: The value or text of passed element
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> current_value = self.get_web_value(selenium_field_element)
        """
        if element.tag_name == "div":
            element_children = element.find_element(By.CSS_SELECTOR, "div > * ")
            if element_children is not None:
                element = element_children

        if element.tag_name == "label":
            web_value = element.get_attribute("text")
            if not web_value:
                web_value = element.text.strip()
        elif element.tag_name == "select":
            current_select = 0 if element.get_attribute('value') == '' else int(element.get_attribute('value')) 
            selected_element = element.find_elements(By.CSS_SELECTOR, "option")[current_select]
            web_value = selected_element.text
        else:
            web_value = element.get_attribute("value")

        return web_value

    def CheckResult(self, field, user_value, grid=False, line=1, grid_number=1, name_attr=False, input_field=True, direction=None):
        """
        Checks if a field has the value the user expects.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param user_value: The value that the field is expected to contain.
        :type user_value: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param line: Grid line that contains the column field to be checked.- **Default:** 1
        :type line: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool
        :param input_field: False if the desired field is not an input type 
        :type bool
        :param direction: Desired direction to search for the element, currently accepts right and down
        :type str

        Usage:

        >>> # Calling method to check a value of a field:
        >>> oHelper.CheckResult("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to check a field that is on the second line of a grid:
        >>> oHelper.CheckResult("Client", "000001", grid=True, line=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to check a field that is on the second grid of the screen:
        >>> oHelper.CheckResult("Order", "000001", grid=True, line=1, grid_number=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Call method to check a field value that is not an input field and is on the right:
        >>> oHelper.CheckResult("Saldo Titulo", "100.000,00", input_field=False, direction='right')
        >>> oHelper.LoadGrid()
        
        """
        self.wait_blocker()
        if grid:
            self.check_grid_appender(line - 1, field, user_value, grid_number - 1)
        elif isinstance(user_value, bool):
            current_value = self.result_checkbox(field, user_value)
            self.log_result(field, user_value, current_value)
        else:
            field = re.sub(r"(\:*)(\?*)", "", field).strip()
            if name_attr:
                self.wait_element(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                self.wait_element(field)
                
            element = self.get_field(field, name_attr=name_attr, input_field=input_field, direction=direction)
            if not element:
                self.log_error(f"Couldn't find element: {field}")

            field_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
            self.set_element_focus(field_element())
            self.scroll_to_element(field_element())
            endtime = time.time() + self.config.time_out
            current_value =  ''
            while(time.time() < endtime and not current_value):
                current_value = self.get_web_value(field_element()).strip()

            print(f"Value for Field {field} is: {current_value}")

            #Remove mask if present.
            if self.check_mask(field_element()):
                current_value = self.remove_mask(current_value)
                user_value = self.remove_mask(user_value)
            #If user value is string, Slice string to match user_value's length
            if type(current_value) is str:
                current_value = current_value[0:len(str(user_value))]

            self.log_result(field, user_value, current_value)

    def log_result(self, field, user_value, captured_value):
        """
        [Internal]

        Logs the result of comparison between user value and captured value.

        :param field: The field whose values would be compared
        :type field: str
        :param user_value: The value the user expects
        :type user_value: str
        :param captured_value: The value that was captured on the screen
        :type captured_value: str

        Usage:

        >>> # Calling the method:
        >>> self.log_result("A1_COD", "000001", "000001")
        """
        txtaux = ""
        message = ""

        if user_value != captured_value:
            message = self.create_message([txtaux, field, user_value, captured_value], enum.MessageType.INCORRECT)

        self.compare_field_values(field, user_value, captured_value, message)

    def GetValue(self, field, grid=False, line=1, grid_number=1):
        """
        Gets the current value or text of element.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param line: Grid line that contains the column field to be checked.- **Default:** 1
        :type line: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> current_value = oHelper.GetValue("A1_COD")
        """
        endtime = time.time() + self.config.time_out
        element = None

        if not grid:
            while ( (time.time() < endtime) and (not element) and (not hasattr(element, "name")) and (not hasattr(element, "parent"))):           
                element = self.get_field(field)
                if ( hasattr(element, "name") and hasattr(element, "parent") ):
                    selenium_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                    value = self.get_web_value(selenium_element())
        else:
            field_array = [line-1, field, "", grid_number-1]
            x3_dictionaries = self.create_x3_tuple()
            value = self.check_grid(field_array, x3_dictionaries, get_value=True)

        if ( not value ):
            self.log_error("GetValue element is none")
       
        return value


    def restart(self):
        """
        [Internal]

        Restarts the Protheus Webapp and fills the initial screens.

        Usage:

        >>> # Calling the method:
        >>> self.restart()
        """
        webdriver_exception = None

        try:
            self.driver_refresh()
        except WebDriverException as e:
            webdriver_exception = e

        if webdriver_exception:
            message = f"Wasn't possible execute Start() method: {next(iter(webdriver_exception.msg.split(':')), None)}"
            self.assertTrue(False, message)
        
        if self.config.coverage and self.config.initial_program != ''  and self.restart_counter < 3:
            self.open_url_coverage(url=self.config.url, initial_program=self.config.initial_program, environment=self.config.environment)

        try:
            self.driver.switch_to_alert().accept()
        except:
            pass

        if self.config.initial_program != ''  and self.restart_counter < 3:

            if not self.config.skip_environment and not self.config.coverage:
                self.program_screen(self.config.initial_program)
            self.user_screen()
            self.environment_screen()

            endtime = time.time() + self.config.time_out
            while(time.time() < endtime and not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")):
                self.close_modal()

            
            if self.config.routine:
                if ">" in self.config.routine:
                    self.SetLateralMenu(self.config.routine, save_input=False)
                else:
                    self.set_program(self.config.routine)

    def driver_refresh(self):
        """
        [Internal]

        Refresh the driver.

        Usage:

        >>> # Calling the method:
        >>> self.driver_refresh()
        """
        if self.config.smart_test or self.config.debug_log:
            print("Driver Refresh")

        self.driver.refresh()
        self.wait_blocker()
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.F5).key_up(Keys.CONTROL).perform()

    def Finish(self):
        """
        Exit the protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.Finish()
        """
        element = None
        text_cover = None
        string = "Aguarde... Coletando informacoes de cobertura de codigo."
        timeout = 900
        click_counter = 1
        
        if self.config.coverage:
            endtime = time.time() + timeout

            while((time.time() < endtime) and (not element or not text_cover)):

                ActionChains(self.driver).key_down(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down('q').perform()
                ActionChains(self.driver).key_up(Keys.CONTROL).perform()

                element = self.wait_element_timeout(term=self.language.finish, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=5, step=1, main_container="body", check_error = False)

                if element:
                    if self.click_button_finish(click_counter):                        
                        text_cover = self.search_text(selector=".tsay", text=string)
                        if text_cover:
                            print(string)
                            timeout = endtime - time.time()
                            if timeout > 0:
                                self.wait_element_timeout(term=string, scrap_type=enum.ScrapType.MIXED,
                                optional_term=".tsay", timeout=timeout, step=0.1, main_container="body", check_error = False)
                    click_counter += 1
                    if click_counter > 3:
                        click_counter = 1
        else:
            endtime = time.time() + self.config.time_out
            while( time.time() < endtime and not element ):

                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
                soup = self.get_current_DOM()
                element = soup.find_all(text=self.language.finish)

                self.wait_element_timeout(term=self.language.finish, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay", timeout=5, step=0.5, main_container="body")

            if not element:
                print("Warning method finish use driver.refresh. element not found")

            self.driver_refresh() if not element else self.SetButton(self.language.finish)

    def click_button_finish(self, click_counter=None):
        """
        [internal]

        This method is reponsible to click on button finish

        """
        button = None
        listButtons = []
        try:
            soup = self.get_current_DOM()
            listButtons = soup.select('button')
            button = next(iter(list(filter(lambda x: x.text == self.language.finish ,listButtons ))), None)
            if button:
                button_element = lambda : self.soup_to_selenium(button)            
                self.scroll_to_element(button_element())
                self.set_element_focus(button_element())
                if self.click(button_element(), click_type=enum.ClickType(click_counter)):
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Warning Finish method exception - {str(e)}")
            return False

    def LogOff(self):
        """
        Logs out of the Protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.LogOff()
        """
        element = ""
        string = "Aguarde... Coletando informacoes de cobertura de codigo."
        timeout = 900

        if self.config.coverage:
            endtime = time.time() + timeout
            while(time.time() < endtime and not element):
                ActionChains(self.driver).key_down(Keys.ESCAPE).perform()
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
                self.SetButton(self.language.logOff)

                self.wait_element_timeout(term=string, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay", timeout=10, step=0.1)

                element = self.search_text(selector=".tsay", text=string)
                if element:
                    print(string)

        else:
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
            self.SetButton(self.language.logOff)


    def web_scrap(self, term, scrap_type=enum.ScrapType.TEXT, optional_term=None, label=False, main_container=None, check_error=True, check_help=True, input_field=True, direction=None, position=1):
        """
        [Internal]

        Returns a BeautifulSoup object list based on the search parameters.

        Does not support ScrapType.XPATH as scrap_type parameter value.

        :param term: The first search term. A text or a selector
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param label: If the search is based on a label near the element. - **Default:** False
        :type label: bool
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        :return: List of BeautifulSoup4 elements based on search parameters.
        :rtype: List of BeautifulSoup4 objects

        Usage:

        >>> #All buttons
        >>> buttons = self.web_scrap(term="button", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> #----------------#
        >>> #Elements that contain the text "Example"
        >>> example_elements = self.web_scrap(term="Example")
        >>> #----------------#
        >>> #Elements with class "my_class" and text "my_text"
        >>> elements = self.web_scrap(term="my_text", scrap_type=ScrapType.MIXED, optional_term=".my_class")
        """

        try:
            endtime = time.time() + self.config.time_out
            container =  None
            while(time.time() < endtime and container is None):
                soup = self.get_current_DOM()

                if check_error:
                    self.search_for_errors(check_help)

                if self.config.log_file:
                    with open(f"{term + str(scrap_type) + str(optional_term) + str(label) + str(main_container) + str(random.randint(1, 101)) }.txt", "w") as text_file:
                        text_file.write(f" HTML CONTENT: {str(soup)}")

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                containers = self.zindex_sort(soup.select(container_selector), reverse=True) 

                if self.base_container in container_selector:
                    container = self.containers_filter(containers)

                container = next(iter(containers), None) if isinstance(containers, list) else container

            if container is None:
                raise Exception(f"Web Scrap couldn't find container - term: {term}")

            if (scrap_type == enum.ScrapType.TEXT):
                if label:
                    return self.find_label_element(term, container, input_field=input_field, direction=direction, position=position)
                elif not re.match(r"\w+(_)", term):
                    return self.filter_label_element(term, container) if self.filter_label_element(term, container) else []
                else:
                    return list(filter(lambda x: term.lower() in x.text.lower(), container.select("div > *")))
            elif (scrap_type == enum.ScrapType.CSS_SELECTOR):
                return container.select(term)
            elif (scrap_type == enum.ScrapType.MIXED and optional_term is not None):
                return list(filter(lambda x: term.lower() in x.text.lower(), container.select(optional_term)))
            elif (scrap_type == enum.ScrapType.SCRIPT):
                script_result = self.driver.execute_script(term)
                return script_result if isinstance(script_result, list) else []
            else:
                return []
        except AssertionError:
            raise
        except Exception as e:
            self.log_error(str(e))

    def search_for_errors(self, check_help=True):
        """
        [Internal]
        Searches for errors and alerts in the screen.
        Usage:
        >>> # Calling the method:
        >>> self.search_for_errors()
        """
        endtime = time.time() + self.config.time_out
        soup = None
        top_layer = None

        while(time.time() < endtime and not soup):
            soup = self.get_current_DOM()

        try:   
            if not soup:
                self.log_error("Search for erros couldn't find DOM")
            message = ""
            top_layer = next(iter(self.zindex_sort(soup.select(".tmodaldialog, .ui-dialog"), True)), None)

        except AttributeError as e:
            self.log_error(f"Search for erros couldn't find DOM\n Exception: {str(e)}")

        if not top_layer:
            return None

        icon_alert = next(iter(top_layer.select("img[src*='fwskin_info_ico.png']")), None)
        icon_error_log = next(iter(top_layer.select("img[src*='openclosing.png']")), None)
        if (not icon_alert or not check_help) and not icon_error_log:
            return None

        if icon_alert:
            label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.text.strip(), top_layer.select(".tsay label")))
            if self.language.messages.error_msg_required in label:
                message = self.language.messages.error_msg_required
            elif "help:" in label.lower() and self.language.problem in label:
                message = label
            else:
                return None

        elif icon_error_log:
            label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.text.strip(), top_layer.select(".tsay label")))
            textarea = next(iter(top_layer.select("textarea")), None)
            textarea_value = self.driver.execute_script(f"return arguments[0].value", self.driver.find_element_by_xpath(xpath_soup(textarea)))

            error_paragraphs = textarea_value.split("\n\n")
            error_message = f"Error Log: {error_paragraphs[0]} - {error_paragraphs[1]}" if len(error_paragraphs) > 2 else label
            message = error_message.replace("\n", " ")

            button = next(iter(filter(lambda x: self.language.details.lower() in x.text.lower(),top_layer.select("button"))), None)
            self.click(self.driver.find_element_by_xpath(xpath_soup(button)))
            time.sleep(1)
        self.restart_counter += 1
        self.log_error(message)

    def get_function_from_stack(self):
        """
        [Internal]

        Gets the function name that called the Webapp class from the call stack.

        Usage:

        >>> # Calling the method:
        >>> self.get_function_from_stack()
        """
        stack_item = next(iter(filter(lambda x: x.filename == self.config.routine, inspect.stack())), None)
        return stack_item.function if stack_item and stack_item.function else "function_name"

    def create_message(self, args, message_type=enum.MessageType.CORRECT):
        """
        [Internal]

        Returns default messages used all throughout the class based on input parameters.

        Each message type has a different number of placeholders to be passed as a list through args parameter:

        Correct Message = *"{} Value of field {} is correct!"* - **2 placeholders**

        Incorrect Message = *"{} Value expected for field \"{}\" ({}) is not equal to what was found ({})."* - **3 placeholders**

        Disabled Message = *"{} Field \"{}\" is disabled."* - **2 placeholders**

        AssertError Message = *"Failed: Value expected for field {}: \"{}\" is different from what was found \"{}\"."* - **2 placeholders**

        :param args: A list of strings to be replaced in each message.
        :type args: List of str
        :param message_type: Enum of which message type should be created. - **Default:** enum.MessageType.Correct
        :type message_type: enum.MessageType

        Usage:

        >>> # Calling the method:
        >>> message = self.create_message([txtaux, field, user_value, captured_value], enum.MessageType.INCORRECT)
        """
        correctMessage = "{} Value of field {} is correct!"
        incorrectMessage = "{} Value expected for field \"{}\" ({}) is not equal to what was found ({})."
        disabledMessage = "{} Field \"{}\" is disabled."
        assertErrorMessage = "Failed: Value expected for field {}: \"{}\" is different from what was found \"{}\"."

        if message_type == enum.MessageType.INCORRECT:
            return incorrectMessage.format(args[0], args[1], args[2], args[3])
        elif message_type == enum.MessageType.DISABLED:
            return disabledMessage.format(args[0], args[1])
        elif message_type == enum.MessageType.ASSERTERROR:
            return assertErrorMessage.format(args[0], args[1], args[2])
        else:
            return correctMessage.format(args[0], args[1])

    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container=".tmodaldialog,.ui-dialog", check_error=True):
        """
        [Internal]

        Returns a boolean if element exists on the screen.

        :param term: The first term to use on a search of element
        :type term: str
        :param scrap_type: Type of element search. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType
        :param position: Position which element is located. - **Default:** 0
        :type position: int
        :param optional_term: Second term to use on a search of element. Used in MIXED search. - **Default:** "" (empty string)
        :type optional_term: str

        :return: True if element is present. False if element is not present.
        :rtype: bool

        Usage:

        >>> element_is_present = element_exists(term=".ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> element_is_present = element_exists(term=".tmodaldialog.twidget", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1)
        >>> element_is_present = element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay")
        """

        element_list = []
        containers = None

        if self.config.debug_log:
            with open("debug_log.txt", "a", ) as debug_log:
                debug_log.write(f"term={term}, scrap_type={scrap_type}, position={position}, optional_term={optional_term}\n")
                print(f"term={term}, scrap_type={scrap_type}, position={position}, optional_term={optional_term}")

        if scrap_type == enum.ScrapType.SCRIPT:
            return bool(self.driver.execute_script(term))
        elif (scrap_type != enum.ScrapType.MIXED and not (scrap_type == enum.ScrapType.TEXT and not re.match(r"\w+(_)", term))):
            selector = term
            if scrap_type == enum.ScrapType.CSS_SELECTOR:
                by = By.CSS_SELECTOR
            elif scrap_type == enum.ScrapType.XPATH:
                by = By.XPATH
            elif scrap_type == enum.ScrapType.TEXT:
                by = By.CSS_SELECTOR
                selector = f"[name*='{term}']"

            if scrap_type != enum.ScrapType.XPATH:
                soup = self.get_current_DOM()

                if not soup:
                    return False

                if check_error:
                    self.search_for_errors()

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                try:
                    containers_soup = soup.select(container_selector)

                    if not containers_soup:
                        return False

                    containers = self.zindex_sort(containers_soup, reverse=True)

                except Exception as e:
                    print(f"Warning element_exists containers exception:\n {str(e)}")
                    pass

                if self.base_container in container_selector:
                    container = self.containers_filter(containers)

                container = next(iter(containers), None) if isinstance(containers, list) else containers

                if not container:
                    return False

                try:
                    container_element = self.driver.find_element_by_xpath(xpath_soup(container))
                except:
                    return False
            else:
                container_element = self.driver
            try:
                element_list = container_element.find_elements(by, selector)
            except StaleElementReferenceException:
                pass
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error)
            if not element_list:
                return None
        if position == 0:
            return len(element_list) > 0
        else:
            return len(element_list) >= position

    def SetLateralMenu(self, menu_itens, save_input=True):
        """
        Navigates through the lateral menu using provided menu path.
        e.g. "MenuItem1 > MenuItem2 > MenuItem3"

        :param menu_itens: String with the path to the menu.
        :type menu_itens: str
        :param save_input: Boolean if all input info should be saved for later usage. Leave this flag 'True' if you are not sure. **Default:** True
        :type save_input: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetLateralMenu("Updates > Registers > Products > Groups")
        """
        submenu = ""
        endtime = time.time() + self.config.time_out
        wait_coin_screen = True if menu_itens != self.language.menu_about else False
        if save_input:
            self.config.routine = menu_itens

        print(f"Navigating lateral menu: {menu_itens}")
        self.wait_element(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        menu_itens = list(map(str.strip, menu_itens.split(">")))

        soup = self.get_current_DOM()

        menu_xpath = soup.select(".tmenu")

        menu = menu_xpath[0]
        child = menu
        count = 0
        try:
            for menuitem in menu_itens:
                self.wait_blocker()
                self.wait_until_to(expected_condition="element_to_be_clickable", element = ".tmenu", locator=By.CSS_SELECTOR )
                self.wait_until_to(expected_condition="presence_of_all_elements_located", element = ".tmenu .tmenuitem", locator = By.CSS_SELECTOR )
                menuitem_presence = self.wait_element_timeout(term=menuitem, scrap_type=enum.ScrapType.MIXED, timeout = self.config.time_out, optional_term=".tmenuitem", main_container="body")
                if not menuitem_presence and submenu:
                    submenu().click()
                subMenuElements = menu.select(".tmenuitem")
                subMenuElements = list(filter(lambda x: self.element_is_displayed(x), subMenuElements))
                while not subMenuElements or len(subMenuElements) < self.children_element_count(f"#{child.attrs['id']}", ".tmenuitem"):
                    menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
                    subMenuElements = menu.select(".tmenuitem")
                    if time.time() > endtime and (not subMenuElements or len(subMenuElements) < self.children_element_count(".tmenu", ".tmenuitem")):
                        self.restart_counter += 1
                        self.log_error(f"Couldn't find menu item: {menuitem}")
                child = list(filter(lambda x: x.text.startswith(menuitem) and EC.element_to_be_clickable((By.XPATH, xpath_soup(x))), subMenuElements))[0]
                submenu = lambda: self.driver.find_element_by_xpath(xpath_soup(child))
                if subMenuElements and submenu():
                    self.scroll_to_element(submenu())
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = child, locator = By.XPATH )
                    ActionChains(self.driver).move_to_element(submenu()).click().perform()
                    if count < len(menu_itens) - 1:
                        self.wait_element(term=menu_itens[count], scrap_type=enum.ScrapType.MIXED, optional_term=".tmenuitem", main_container="body")
                        menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
                else:
                    self.restart_counter += 1
                    self.log_error(f"Error - Menu Item does not exist: {menuitem}")
                count+=1

            if not re.search("\([0-9]\)$", child.text): 
                self.slm_click_last_item(f"#{child.attrs['id']} > label")

            if wait_coin_screen and self.config.initial_program.lower() == 'sigaadv':
                self.close_coin_screen_after_routine()

        except AssertionError as error:
            raise error
        except Exception as error:
            print(error)
            self.restart_counter += 1
            self.log_error(str(error))
    
    def tmenuitem_element(self, menu):
        subMenuElements = menu.select(".tmenuitem")
        subMenuElements = list(filter(lambda x: self.element_is_displayed(x), subMenuElements))


    def children_element_count(self, element_selector, children_selector):
        """
        [Internal]

        Returns the count of elements of a certain CSS Selector that exists within a certain element located also via CSS Selector.

        :param element_selector: The selector to find the first element.
        :type element_selector: str
        :param children_selector: The selector to find the children elements inside of the first element.
        :type children_selector: str

        :return: The count of elements matching the children_selector inside of element_selector.
        :rtype: int

        Usage:

        >>> # Calling the method:
        >>> self.children_element_count(".tmenu", ".tmenuitem")
        """
        script = f"return document.querySelector('{element_selector}').querySelectorAll('{children_selector}').length;"
        return int(self.driver.execute_script(script))

    def slm_click_last_item(self, sub_menu_child_label):
        """
        [Internal]

        SetLateralMenu, this method retry click in the last sub item
        """
        try:
            child_label = next(iter(self.web_scrap(term=sub_menu_child_label,
                scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")), None)
            child_label_s = self.soup_to_selenium(child_label)
            child_label_s.click()
        except Exception as e:
            if self.config.smart_test or self.config.debug_log:
                print(f"Warning SetLateralMenu click last item method exception: {str(e)} ")

        


    def SetButton(self, button, sub_item="", position=1, check_error=True, ratio=2.0):
        """
        Method that clicks on a button on the screen.

        :param button: Button to be clicked.
        :type button: str
        :param sub_item: Sub item to be clicked inside the first button. - **Default:** "" (empty string)
        :type sub_item: str
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> oHelper.SetButton("Add")
        >>> #-------------------------------------------------
        >>> # Calling the method to click on a sub item inside a button.
        >>> oHelper.SetButton("Other Actions", "Process")
        >>> #-------------------------------------------------
        >>> # Calling the method to click on a sub item inside a button, this form is an alternative.
        >>> oHelper.SetButton("Other Actions", "Process, Process_02, Process_03") 
        """

        self.wait_blocker()
        container = self.get_current_container()

        if container  and 'id' in container.attrs:
            id_container = container.attrs['id']

        print(f"Clicking on {button}")

        try:
            soup_element  = ""
            if (button.lower() == "x"):
                self.set_button_x(position, check_error)
                return
            else:
                self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button, .thbutton", timeout=10, step=0.1, check_error=check_error)
                position -= 1

            layers = 0
            if button in [self.language.confirm, self.language.save]:
                layers = len(self.driver.find_elements(By.CSS_SELECTOR, ".tmodaldialog"))

            success = False
            endtime = time.time() + self.config.time_out
            starttime = time.time()

            if self.config.smart_test:
                print(f"***System Info*** Before Clicking on button:")
                system_info()

            while(time.time() < endtime and not soup_element):
                soup_objects = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button, .thbutton", main_container = self.containers_selectors["SetButton"], check_error=check_error)
                soup_objects = list(filter(lambda x: self.element_is_displayed(x), soup_objects ))


                if soup_objects and len(soup_objects) - 1 >= position:
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects[position], locator = By.XPATH, timeout=True)
                    soup_element = lambda : self.soup_to_selenium(soup_objects[position])
                    parent_element = self.soup_to_selenium(soup_objects[0].parent)
                    id_parent_element = parent_element.get_attribute('id')

            if self.config.smart_test:
                print(f"Clicking on Button {button} Time Spent: {time.time() - starttime} seconds")
                
            if not soup_element:
                other_action = next(iter(self.web_scrap(term=self.language.other_actions, scrap_type=enum.ScrapType.MIXED, optional_term="button", check_error=check_error)), None)
                if (other_action is None or not hasattr(other_action, "name") and not hasattr(other_action, "parent")):
                    self.log_error(f"Couldn't find element: {button}")

                other_action_element = lambda : self.soup_to_selenium(other_action)

                self.scroll_to_element(other_action_element())
                self.click(other_action_element())

                success = self.click_sub_menu(button if button.lower() != self.language.other_actions.lower() else sub_item)
                if success:
                    return
                else:
                    self.log_error(f"Element {button} not found!")

            if soup_element:
                self.scroll_to_element(soup_element())
                self.set_element_focus(soup_element())
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects[position], locator = By.XPATH )
                self.send_action(self.click, soup_element, ratio=ratio)
                self.wait_element_is_not_focused(soup_element)

            if sub_item and ',' not in sub_item:
                if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
                    self.tmenu_out_iframe = True

                soup_objects_filtered = None
                while(time.time() < endtime and not soup_objects_filtered):
                    soup_objects = self.web_scrap(term=sub_item, scrap_type=enum.ScrapType.MIXED, optional_term=".tmenupopupitem", main_container="body", check_error=check_error)
                    soup_objects_filtered = self.filter_is_displayed(soup_objects)
                
                if soup_objects_filtered:
                    soup_element = lambda : self.soup_to_selenium(soup_objects_filtered[0])
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects_filtered[0], locator = By.XPATH )
                    self.click(soup_element())
                    self.tmenu_out_iframe = False
                else:

                    result = False
                    self.tmenu_out_iframe = False

                    soup_objects = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button, .thbutton", main_container = self.containers_selectors["SetButton"], check_error=check_error)
                    soup_objects = list(filter(lambda x: self.element_is_displayed(x), soup_objects ))
                    if soup_objects and len(soup_objects) - 1 >= position:
                        soup_element = lambda : self.soup_to_selenium(soup_objects[position])
                    else:
                        self.log_error(f"Couldn't find element {button}")
                    
                    self.scroll_to_element(soup_element())#posiciona o scroll baseado na height do elemento a ser clicado.
                    self.set_element_focus(soup_element())
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects[position], locator = By.XPATH )
                    self.send_action(self.click, soup_element)

                    result  = self.click_sub_menu(sub_item)
 
                    if not result:
                        self.log_error(f"Couldn't find element {sub_item}")
                    else:
                        return

            elif ',' in sub_item:
                list_sub_itens = sub_item.split(',')
                filtered_sub_itens = list(map(lambda x: x.strip(), list_sub_itens))
                self.click_sub_menu(filtered_sub_itens[len(filtered_sub_itens)-1])

            buttons = [self.language.Ok, self.language.confirm, self.language.finish,self.language.save, self.language.exit, self.language.next, "x"]

            buttons_filtered = list(map(lambda x: x.lower(), buttons)) 

            if button.lower() in buttons_filtered:

                if self.used_ids:
                    self.used_ids = self.pop_dict_itens(self.used_ids, id_container)
                    
                elif self.grid_counters:
                    self.grid_counters = {}

            if button == self.language.save and id_parent_element in self.get_enchoice_button_ids(layers):
                self.wait_element_timeout(term="", scrap_type=enum.ScrapType.MIXED, optional_term="[style*='fwskin_seekbar_ico']", timeout=10, step=0.1, check_error=False, main_container="body")
                self.wait_element_timeout(term="", scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="[style*='fwskin_seekbar_ico']", timeout=10, step=0.1, check_error=False, main_container="body")
            elif button == self.language.confirm and id_parent_element in self.get_enchoice_button_ids(layers):
                self.wait_element_timeout(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=layers + 1, main_container="body", timeout=10, step=0.1, check_error=False)

        except ValueError as error:
            print(str(error))
            self.log_error(f"Button {button} could not be located.")
        except AssertionError:
            raise
        except Exception as error:
            print(str(error))
            self.log_error(str(error))
        
        if self.config.smart_test:
            print(f"***System Info*** After Clicking on button:")
            system_info()

    def set_button_x(self, position=1, check_error=True):
        position -= 1
        term_button = ".ui-button.ui-dialog-titlebar-close[title='Close'], img[src*='fwskin_delete_ico.png'], img[src*='fwskin_modal_close.png']"
        wait_button = self.wait_element(term=term_button, scrap_type=enum.ScrapType.CSS_SELECTOR, position=position, check_error=check_error)
        soup = self.get_current_DOM() if not wait_button else self.get_current_container()

        close_list = soup.select(term_button)
        if not close_list:
            self.log_error(f"Element not found")
        if len(close_list) < position+1:
            self.log_error(f"Element x position: {position} not found")
        if position == 0:
            element_soup = close_list.pop()
        else:
            element_soup = close_list.pop(position)
        element_selenium = self.soup_to_selenium(element_soup)
        self.scroll_to_element(element_selenium)
        self.wait_until_to( expected_condition = "element_to_be_clickable", element = element_soup, locator = By.XPATH )
        
        self.click(element_selenium)
        
    def click_sub_menu(self, sub_item):
        """
        [Internal]

        Clicks on the sub menu of buttons. Returns True if succeeded.
        Internal method of SetButton.

        :param sub_item: The menu item that should be clicked.
        :type sub_item: str

        :return: Boolean if click was successful.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> self.click_sub_menu("Process")
        """
        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.driver.switch_to.default_content()
            
        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")

        menu_id = self.zindex_sort(soup.select(".tmenupopup.active"), True)[0].attrs["id"]
        menu = self.driver.find_element_by_id(menu_id)

        menu_itens = menu.find_elements(By.CSS_SELECTOR, ".tmenupopupitem")

        result = self.find_sub_menu_text(sub_item, menu_itens)

        item = ""
        if result[0]:
            item = result[0]
        elif result[1]:
            item = self.find_sub_menu_child(sub_item, result[1])
        else:
            return False

        if item:
            self.scroll_to_element(item)
            time.sleep(0.5)
            self.click(item)
            return True
        else:
            return False

    def find_sub_menu_child(self, sub_item, containers):
        """
        [Internal]

        Finds the menu item inside child menu layers.

        :param sub_item: The menu item that should be clicked.
        :type sub_item: str
        :param containers: The menu itens of the current layer that have children.
        :type containers: List of Beautiful Soup objects

        :return: The item that was found. If None was found, it returns an empty string.
        :rtype: Selenium object

        Usage:

        >>> # Calling the method:
        >>> item = self.find_sub_menu_child("Process", container_list)
        """
        item = ""
        for child in containers:

            child_id = child.get_attribute("id")
            old_class = self.driver.execute_script("return document.querySelector('#{}').className".format(child_id))
            new_class = old_class + " highlighted expanded"
            self.driver.execute_script("document.querySelector('#{}').className = '{}'".format(child_id, new_class))

            child_itens = child.find_elements(By.CSS_SELECTOR, ".tmenupopupitem")
            result = self.find_sub_menu_text(sub_item, child_itens)

            if not result[0] and result[1]:
                item = self.find_sub_menu_child(sub_item, result[1])
            else:
                item = result[0]
                if item:
                    break
                self.driver.execute_script("document.querySelector('#{}').className = '{}'".format(child_id, old_class))

        return item

    def find_sub_menu_text(self, menu_item, current_itens):
        """
        [Internal]

        Returns a tuple containing a possible match of a menu item among the current itens.
        If none was found it will be an empty string.

        The second position will contain the itens that have children itens.
        If none has children itens, it will be an empty list.

        :param menu_item: The menu item that should be clicked.
        :type menu_item: str
        :param current_item: The menu itens in the current layer.
        :type current_item: List of Selenium objects.

        :return: Tuple containing a possible match of a menu item and the itens that have children itens.
        :rtype: Tuple (selenium object, list of selenium objects)

        Usage:

        >>> # Calling the method:
        >>> result = self.find_sub_menu_text(item, child_itens)
        """
        submenu = ""
        containers = []
        for child in current_itens:
            if "container" in child.get_attribute("class"):
                containers.append(child)
            elif child.text.startswith(menu_item):
                submenu = child
                break

        return (submenu, containers)

    def SetBranch(self, branch):
        """
        Chooses the branch on the branch selection screen.

        :param branch: The branch that would be chosen.
        :type branch: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetBranch("D MG 01 ")
        """
        print(f"Setting branch: {branch}.")
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, position=2, main_container="body")
        Ret = self.fill_search_browse(branch, self.get_search_browse_elements())
        if Ret:
            self.SetButton('OK')

    def WaitHide(self, string, timeout=None, throw_error = True):
        """
        Search string that was sent and wait hide the element.

        :param string: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitHide("Processing")
        """
        print("Waiting processing...")

        if not timeout:
            timeout = 1200
        
        endtime = time.time() + timeout
        while(time.time() < endtime):

            element = None
            
            element = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay, .tgroupbox", main_container = self.containers_selectors["AllContainers"], check_help=False)

            if not element:
                return
            if endtime - time.time() < 1180:
                time.sleep(0.5)

        if not throw_error:
            return False
        else:
            self.log_error(f"Element {string} not found")

    def WaitShow(self, string, timeout=None, throw_error = True):
        """
        Search string that was sent and wait show the elements.

        :param string: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitShow("Processing")
        """
        print(f"Waiting show text '{string}'...")

        if not timeout:
            timeout = 1200

        endtime = time.time() + timeout
        while(time.time() < endtime):

            element = None

            element = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay, .tgroupbox", main_container = self.containers_selectors["AllContainers"], check_help=False)

            if element:
                return element

            if endtime - time.time() < 1180:
                time.sleep(0.5)

        if not throw_error:
            return False
        else:
            self.log_error(f"Element {string} not found")

    def WaitProcessing(self, itens, timeout=None):
        """
        Uses WaitShow and WaitHide to Wait a Processing screen

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitProcessing("Processing")
        """
        if not timeout:
            timeout = 1200

        self.WaitShow(itens, timeout, throw_error = False)

        self.WaitHide(itens, timeout, throw_error = False)


    def SetTabEDAPP(self, table):
        """
        Chooses the table on the generic query (EDAPP).

        :param table: The table that would be chosen.
        :type table: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetTabEDAPP("AAB")
        """
        try:
            field = self.get_field("cPesq", name_attr=True)
            element = lambda: self.driver.find_element_by_xpath(xpath_soup(field))
            self.click(element())
            self.send_keys(element(), table)
            time.sleep(0.5)
            self.send_keys(element(), Keys.ENTER)
            self.send_keys(element(), Keys.ENTER)
            self.SetButton("Ok")
        except:
            print("Search field could not be located.")

    def ClickFolder(self, folder_name, position):
        """
        Clicks on folder elements on the screen.

        :param folder_name: Which folder item should be clicked.
        :type folder_name: str
        :param position: In case of two or more folders with the same name in the screen, you could choose by position in order
        :type position: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickFolder("Folder1")
        >>> # Second folder named as Folder1 in the same screen
        >>> oHelper.ClickFolder("Folder1", position=2)
        """
        self.wait_blocker()

        element = ""
        position -= 1

        self.wait_element(term=folder_name, scrap_type=enum.ScrapType.MIXED, optional_term=".tfolder.twidget, .button-bar a")

        endtime  = time.time() + self.config.time_out

        while(time.time() < endtime and not element):
            panels = self.web_scrap(term=".button-bar a", scrap_type=enum.ScrapType.CSS_SELECTOR,main_container = self.containers_selectors["GetCurrentContainer"])
            panels_filtered = self.filter_is_displayed(list(filter(lambda x: x.text == folder_name, panels)))
            if panels_filtered:
                if position > 0:
                    panel = panels_filtered[position] if position < len(panels_filtered) else None
                else:
                    panel = next(iter(panels_filtered), None)

                element = self.soup_to_selenium(panel) if panel else None

                if element:
                    self.scroll_to_element(element)#posiciona o scroll baseado na height do elemento a ser clicado.
                    self.set_element_focus(element)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click()", element)

        if not element:
            self.log_error("Couldn't find panel item.")

    def ClickBox(self, field, content_list="", select_all=False, grid_number=1):
        """
        Clicks on Checkbox elements of a grid.

        :param field: The column to identify grid rows.
        :type field: str
        :param content_list: Comma divided string with values that must be checked. - **Default:** "" (empty string)
        :type content_list: str
        :param select_all: Boolean if all options should be selected. - **Default:** False
        :type select_all: bool
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method to select a specific checkbox:
        >>> oHelper.ClickBox("Branch", "D MG 01 ")
        >>> #--------------------------------------------------
        >>> # Calling the method to select multiple checkboxes:
        >>> oHelper.ClickBox("Branch", "D MG 01 , D RJ 02")
        >>> #--------------------------------------------------
        >>> # Calling the method to select all checkboxes:
        >>> oHelper.ClickBox("Branch", select_all=True)
        """
        self.wait_blocker()
        print(f"ClickBox - Clicking on {content_list}")
        endtime = time.time() + self.config.time_out
        grid_number -= 1
        if content_list:
            self.wait_element_timeout(field)
        elif select_all:
            self.wait_element_timeout(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term="label span")

        grid = self.get_grid(grid_number)
        column_enumeration = list(enumerate(grid.select("thead label")))
        chosen_column = next(iter(list(filter(lambda x: field in x[1].text, column_enumeration))), None)
        if chosen_column:
            column_index = chosen_column[0]
        else:
            self.log_error("Couldn't find chosen column.")

        content_list = content_list.split(",")

        is_select_all_button = self.element_exists(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term="label span")

        if select_all and is_select_all_button:
            self.wait_element(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term="label span")
            element = next(iter(self.web_scrap(term="label.tcheckbox input", scrap_type=enum.ScrapType.CSS_SELECTOR)), None)
            if element:
                box = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                self.click(box())

        elif select_all and not is_select_all_button:
            th = next(iter(grid.select('th')))
            th_element = self.soup_to_selenium(th)
            th_element.click()

        elif content_list or (select_all and not is_select_all_button):
            class_grid = grid.attrs['class'][0]
            initial_containers = self.get_all_containers()

            for item in content_list:
                grid = self.get_grid(grid_number)
                self.ScrollGrid(column=field, match_value=item, grid_number=grid_number+1)
                get_current = lambda: self.selected_row(grid_number)
                column_enumeration = list(enumerate(grid.select("thead label")))
                chosen_column = next(iter(list(filter(lambda x: field in x[1].text, column_enumeration))), None)
                column_index = chosen_column[0] if chosen_column else self.log_error("Couldn't find chosen column.")
                self.wait_selected_row( grid_number, column_index, field)
                current = get_current()

                success = False
                while( time.time() < endtime and not success):
                    td = next(iter(current.select(f"td[id='{column_index}']")), None)
                    click_box_item = td.parent.select_one("td")
                    click_box_item_s = self.soup_to_selenium(click_box_item)
                    self.scroll_to_element(click_box_item_s)

                    if class_grid == 'tmsselbr':
                        ActionChains(self.driver).move_to_element(click_box_item_s).click(click_box_item_s).perform()
                        ActionChains(self.driver).move_to_element(click_box_item_s).send_keys_to_element(click_box_item_s, Keys.ENTER).perform()
                    elif class_grid != "tgrid":
                        ActionChains(self.driver).move_to_element(click_box_item_s).send_keys_to_element(click_box_item_s, Keys.ENTER).perform()
                    else:
                        self.double_click(click_box_item_s, click_type = enum.ClickType.ACTIONCHAINS)
                    self.wait_element_is_not_displayed(click_box_item)

                    end_containers = self.get_all_containers()
                    if end_containers and len(end_containers) > len(initial_containers):
                        print("ClickBox: New container found stopping attempts to click on the checkbox")
                        break

                    new_td = next(iter(get_current().select(f"td[id='{column_index}']")), None)
                    new_click_box_item = new_td.parent.select_one("td")
                    if new_click_box_item != click_box_item:
                        success = True

    def ScrollGrid(self, column, match_value, grid_number=1):
        """
        Scrolls Grid until a matching column is found.

        :param field: The column to be matched.
        :type field: str
        :param match_value: The value to be matched in defined column.
        :type match_value: str
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method to scroll to a column match:
        >>> oHelper.ScrollGrid(column="Branch",match_value="D MG 01 ")
        >>> #--------------------------------------------------
        >>> # Calling the method to scroll to a column match of the second grid:
        >>> oHelper.ScrollGrid(column="Branch", match_value="D MG 01 ", grid_number=2)
        """
        grid_number -= 1
        td_element = None
        actions = ActionChains(self.driver)
        
        self.wait_element_timeout(term = column, scrap_type = enum.ScrapType.TEXT, timeout = self.config.time_out , optional_term = 'label')
        endtime = time.time() + self.config.time_out
        
        grid = self.get_grid(grid_number)
        get_current = lambda: self.selected_row(grid_number)

        column_enumeration = list(enumerate(grid.select("thead label")))
        chosen_column = next(iter(list(filter(lambda x: column in x[1].text, column_enumeration))), None)
        column_index = chosen_column[0] if chosen_column else self.log_error("Couldn't find chosen column.")
            
        current = get_current()
        td = lambda: next(iter(current.select(f"td[id='{column_index}']")), None)

        frozen_table = next(iter(grid.select('table.frozen-table')),None)
        if (not self.click_grid_td(td()) and not frozen_table):
            self.log_error(" Couldn't click on column, td class or tr is not selected ")

        while( time.time() < endtime and  not td_element ):
            
            grid = self.get_grid(grid_number)
            current = get_current()

            td_list = grid.select(f"td[id='{column_index}']")
            td_element_not_filtered = next(iter(td_list), None)
            td_list_filtered  = list(filter(lambda x: x.text.strip() == match_value and self.element_is_displayed(x) ,td_list))
            td_element = next(iter(td_list_filtered), None)

            if not td_element and next(self.scroll_grid_check_elements_change(xpath_soup(td_element_not_filtered))):
                actions.key_down(Keys.PAGE_DOWN).perform()
                self.wait_element_is_not_displayed(td().parent)

        if not td_element:
            self.log_error("Scroll Grid couldn't find the element")

        if frozen_table:
            self.soup_to_selenium(td_element.next_sibling).click()
            
        self.click(self.soup_to_selenium(td_element))

    def click_grid_td(self, td_soup):
        """
         Click on a td element and checks if is selected

        :param td: The column to be matched.
        :type td: bs4 element
        
        >>> # Calling the method to click on td and check if is selected:
        >>> oHelper.click_grid_td(td)
        """
        success = None
        endtime = time.time() + 10

        while ( not success and time.time() < endtime ):
            try:
                td_selenium = lambda: self.soup_to_selenium(td_soup)
                tr_selenium_class = lambda: self.soup_to_selenium(td_soup.parent).get_attribute('class')
                td_is_selected = lambda: True if 'selected' in td_selenium().get_attribute('class') or 'selected' in tr_selenium_class() else False
                self.set_element_focus(td_selenium())
                td_selenium().click()
                if not td_is_selected():
                    self.wait_until_to( expected_condition = "visibility_of", element = td_selenium, timeout=True)
                    self.wait_until_to(expected_condition="element_to_be_clickable", element = td, locator = By.XPATH, timeout=True)
                    
                    success = td_is_selected()
                else:
                    success = td_is_selected()
            except:
                pass
        return success

    def scroll_grid_check_elements_change(self, xpath):
        """
        [Internal]
        Used to check PG_DOWN correct execute. 

        """
        elements_set = set()
        elements_set.add(xpath)
        yield True if xpath else False
        while(True):
            old_lenght = len(elements_set)
            elements_set.add(xpath)
            yield True if len(elements_set) > old_lenght and xpath  else False


    def selected_row(self, grid_number = 0):
        """
        [Internal]

        Returns the selected row in the grid.

        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method to return the selected row:
        >>> oHelper.selected_row(grid_number = 0)

        """
        row_selected = None
        grid = self.get_grid(grid_number)
        if grid:
            row = next(iter(grid.select('tbody tr.selected-row')), None)
            column = next(iter(grid.select('td.selected-cell')), None)
            row_selected = column.parent  if column else row

        return row_selected

    def wait_selected_row(self, grid_number = 0, column_index = 0, text = "default-text", time_out = 5):
        """
        [Internal]

        This method expects the selected line to be the line with the text value entered.
        
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 0
        :type grid_number: int
        :param column_index: The column index
        :type column_index: int
        :param text: The value of column to be matched
        :type text: string

        Usage:

        >>> # Calling the method to wait the selected row:
        >>> oHelper.wait_selected_row(grid_number = 0, column_index = 0, text= "value" )
        """
        success = False
        endtime = time.time() + time_out
        while( time.time() < endtime and not success):
            current = self.selected_row(grid_number)
            td = next(iter(current.select(f"td[id='{column_index}']")), None)
            success = td.text in text

    def get_grid(self, grid_number=0, grid_element = None):
        """
        [Internal]
        Gets a grid BeautifulSoup object from the screen.

        :param grid_number: The number of the grid on the screen.
        :type: int
        :return: Grid BeautifulSoup object
        :rtype: BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> my_grid = self.get_grid()
        """
        endtime = time.time() + 60
        grids = None
        while(time.time() < endtime and not grids):
            if not grid_element:
                grids = self.web_scrap(term=".tgetdados,.tgrid,.tcbrowse,.tmsselbr", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                grids = self.web_scrap(term= grid_element, scrap_type=enum.ScrapType.CSS_SELECTOR)

        if grids:
            grids = list(filter(lambda x: self.element_is_displayed(x), grids))
        else:
            self.log_error("Couldn't find grid.")

        if len(grids) - 1  >= grid_number:
            return grids[grid_number]
        else:
            self.log_error("Grid number out of bounds.")

    def check_mask(self, element):
        """
        [Internal]

        Checks whether the element has a mask or not.

        :param element: The element that must be checked.
        :type element: Selenium object

        :return: Boolean if element has a mask or not.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> self.check_mask(my_element)
        """
        reg = (r"^[1-9.\/-:\+]+|(@. )[1-9.\/-:\+]+")
        mask = element.get_attribute("picture")
        if mask is None:
            child = element.find_elements(By.CSS_SELECTOR, "input")
            if child:
                mask = child[0].get_attribute("picture")

        return (mask != "" and mask is not None and (re.findall(reg, mask)))

    def remove_mask(self, string):
        """
        [Internal]

        Removes special characters from received string.

        :param string: The string that would have its characters removed.
        :type string: str

        :return: The string with its special characters removed.
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> value_without_mask = self.remove_mask("111-111.111")
        >>> # value_without_mask == "111111111"
        """
        if type(string) is str:
            caracter = (r'[.\/+-]')
            if string[0:4] != 'http':
                match = re.findall(caracter, string)
                if match:
                    string = re.sub(caracter, '', string)

            return string

    def SetKey(self, key, grid=False, grid_number=1, additional_key="", wait_show = "", step = 3 ):
        """
        Press the desired key on the keyboard on the focused element.

        .. warning::
            If this methods is the first to be called, we strongly recommend using some wait methods like WaitShow().

        .. warning::           
            Before using this method, set focus on any element.

        Supported keys: F1 to F12, CTRL+Key, ALT+Key, Up, Down, Left, Right, ESC, Enter and Delete ...

        :param key: Key that would be pressed
        :type key: str
        :param grid: Boolean if action must be applied on a grid. (Usually with DOWN key)
        :type grid: bool
        :param grid_number: Grid number of which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
		:param additional_key: Key additional that would be pressed.
        :type additional_key: str
        :param wait_show: String that will hold the wait after press a key.
        :type wait_show: str
        :param step: The amount of time each step should wait. - **Default:** 3
        :type step: float

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetKey("ENTER")
        >>> #--------------------------------------
        >>> # Calling the method on a grid:
        >>> oHelper.SetKey("DOWN", grid=True)
        >>> #--------------------------------------
        >>> # Calling the method on the second grid on the screen:
        >>> oHelper.SetKey("DOWN", grid=True, grid_number=2)
        >>> #--------------------------------------
        >>> # Call the method with WaitShow when you expect a new window or text to appear on the screen:
        >>> oHelper.SetKey( key = "F12", wait_show="Parametros", step = 3 )
        >>> #--------------------------------------
        >>> # Calling the method with special keys (using parameter additional_key):
        >>> oHelper.SetKey(key="CTRL", additional_key="A")
        """
        self.wait_blocker()
        print(f"Key pressed: {key + '+' + additional_key if additional_key != '' else key }") 

        #JavaScript function to return focused element if DIV/Input OR empty if other element is focused

        script = """
        var getActiveElement = () => {
	        if(document.activeElement.tagName.toLowerCase() == "input" || document.activeElement.tagName.toLowerCase() == "div"){
		        if(document.activeElement.attributes["id"]){
			        return document.activeElement.attributes["id"].value
		        }else if(document.activeElement.parentElement.attributes["id"]){
			        return document.activeElement.parentElement.attributes["id"].value
		        }
            }
	        return ""
        }

        return getActiveElement()
        """
        key = key.upper()
        endtime = time.time() + self.config.time_out
        hotkey = ["CTRL","ALT"]
        grid_number-=1
        tries = 0
        success = False
        
        try:
            if key in hotkey and not additional_key:
                self.log_error("Additional key is empty")

            if key == "DOWN" and grid:
                grid_number = 0 if grid_number is None else grid_number
                self.grid_input.append(["", "", grid_number, True])
                return

            while(time.time() < endtime and not success):
                if key not in hotkey and self.supported_keys(key):
                    if grid:
                        if key != "DOWN":
                            self.LoadGrid()
                        self.send_action(action=ActionChains(self.driver).key_down(self.supported_keys(key)).perform)
                    elif tries > 0:
                        ActionChains(self.driver).key_down(self.supported_keys(key)).perform()
                        tries = 0
                    else:
                        Id = self.driver.execute_script(script)
                        element = lambda: self.driver.find_element_by_id(Id) if Id else self.driver.find_element(By.TAG_NAME, "html")
                        self.set_element_focus(element())
                        self.send_action(action=self.send_keys, element=element, value=self.supported_keys(key))
                        tries +=1

                elif additional_key:
                    self.send_action(action=ActionChains(self.driver).key_down(self.supported_keys(key)).send_keys(additional_key.lower()).key_up(self.supported_keys(key)).perform)

                if wait_show:
                    success = self.WaitShow(wait_show, timeout=step, throw_error = False)
                else:
                    success = True

 
        except WebDriverException as e:
            self.log_error(f"SetKey - Screen is not load: {e}")
        except Exception as error:
            self.log_error(str(error))

    def supported_keys(self, key = ""):
        """
        [Internal]
        """
        try:
            supported_keys = {
                "F1" : Keys.F1,
                "F2" : Keys.F2,
                "F3" : Keys.F3,
                "F4" : Keys.F4,
                "F5" : Keys.F5,
                "F6" : Keys.F6,
                "F7" : Keys.F7,
                "F8" : Keys.F8,
                "F9" : Keys.F9,
                "F10" : Keys.F10,
                "F11" : Keys.F11,
                "F12" : Keys.F12,
                "UP" : Keys.UP,
                "DOWN" : Keys.DOWN,
                "LEFT" : Keys.LEFT,
                "RIGHT" : Keys.RIGHT,
                "DELETE" : Keys.DELETE,
                "ENTER" : Keys.ENTER,
                "ESC" : Keys.ESCAPE,
                "CTRL" : Keys.CONTROL,
                "ALT" : Keys.ALT,
                "NUMPAD0" : Keys.NUMPAD0,
                "NUMPAD1" : Keys.NUMPAD1,
                "NUMPAD2" : Keys.NUMPAD2,
                "NUMPAD3" : Keys.NUMPAD3,
                "NUMPAD4" : Keys.NUMPAD4,
                "NUMPAD5" : Keys.NUMPAD5,
                "NUMPAD6" : Keys.NUMPAD6,
                "NUMPAD7" : Keys.NUMPAD7,
                "NUMPAD8" : Keys.NUMPAD8,
                "NUMPAD9" : Keys.NUMPAD9,
                "MULTIPLY" : Keys.MULTIPLY,
                "ADD" : Keys.ADD,
                "SEPARATOR" : Keys.SEPARATOR,
                "SUBTRACT" : Keys.SUBTRACT,
                "DECIMAL" : Keys.DECIMAL,
                "DIVIDE" : Keys.DIVIDE,  
                "META" : Keys.META,
                "COMMAND" : Keys.COMMAND,
                "NULL" : Keys.NULL, 
                "CANCEL" : Keys.CANCEL, 
                "HELP" : Keys.HELP,
                "BACKSPACE" : Keys.BACKSPACE, 
                "TAB" : Keys.TAB, 
                "CLEAR" : Keys.CLEAR, 
                "RETURN" : Keys.RETURN, 
                "SHIFT" : Keys.SHIFT, 
                "PAUSE" : Keys.PAUSE, 
                "ESCAPE" : Keys.ESCAPE, 
                "SPACE" : Keys.SPACE,
                "END" : Keys.END,
                "HOME" : Keys.HOME,
                "INSERT" : Keys.INSERT,
                "SEMICOLON" : Keys.SEMICOLON,
                "EQUALS" : Keys.EQUALS,
                "ARROW_LEFT" : Keys.ARROW_LEFT,
                "ARROW_UP" : Keys.ARROW_UP,
                "ARROW_RIGHT" : Keys.ARROW_RIGHT, 
                "ARROW_DOWN" : Keys.ARROW_DOWN,
                "BACK_SPACE" : Keys.BACK_SPACE,
                "LEFT_SHIFT" : Keys.LEFT_SHIFT,
                "LEFT_CONTROL" : Keys.LEFT_CONTROL,
                "LEFT_ALT" : Keys.LEFT_ALT, 
                "PAGE_UP" : Keys.PAGE_UP ,
                "PAGE_DOWN" : Keys.PAGE_DOWN 

            }

            return supported_keys[key.upper()]

        except KeyError:
            self.log_error("Key is not supported")

    def SetFocus(self, field, grid_cell, row_number, position):
        """
        Sets the current focus on the desired field.

        :param field: The field that must receive the focus.
        :type field: str
        :param grid_cell: Indicates if the element that deserve focus is on a grid.
        :type grid_cell: bool
        :param row_number: Number of row in case of multiples rows.
        :type row_number: int
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFocus("A1_COD")
        >>> oHelper.SetFocus("A1_COD", grid_cell = True)
        """
        if grid_cell:
            self.wait_element(field)
            
            self.ClickGridCell(field, row_number)
            time.sleep(1)
            ActionChains(self.driver).key_down(Keys.ENTER).perform()
            time.sleep(1)
        else:
            print(f"Setting focus on element {field}.")

            label = False if re.match(r"\w+(_)", field) else True

            if label:
                container = self.get_current_container()
                labels = container.select('label')

                label_text_filtered = re.sub(r"[:;*?]", "", field)
                label_filtered = next(iter(list(filter(
                    lambda x: re.sub(r"[:;*?]", "",  x.text) == label_text_filtered, labels))), None)

                if label_filtered and not self.element_is_displayed(label_filtered):
                    self.scroll_to_element( self.soup_to_selenium(label_filtered) )
                

            element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, optional_term="label", main_container = self.containers_selectors["Containers"], label=label, position=position)), None)
            if not element:
                element = next(iter(self.web_scrap(f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container = self.containers_selectors["Containers"], label=label, position=position)), None)
            if element and not self.element_is_displayed(element):
                self.scroll_to_element( self.soup_to_selenium(element) )

            try:
                element = self.soup_to_selenium(element)
                self.set_element_focus(element)
                if self.driver.switch_to_active_element() != element:
                    self.click(element, click_type=enum.ClickType.SELENIUM)
            except Exception as e:
                print(f"Warning: SetFocus: '{field}' - Exception {str(e)}")

    def click_check_radio_button(self, field, value, name_attr = False, position = 1):
        """
        [Internal]
        Identify and click on check or radio button.

        :param field: The field that would receive the input.
        :type field: str
        :param value: The value that must be on the checkbox or grid.
        :type value: bool

        :return: The element that changed value.
        :rtype: Selenium object

        Usage:

        >>> # Calling the method:
        >>> element = self.check_checkbox("CheckBox1", True)
        """
        print(f'Clicking in "{self.returns_printable_string(field)}"')

        position -= 1
        
        element_list = []

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not element_list):
            if re.match(r"\w+(_)", field):
                self.wait_element(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
                element_list = self.web_scrap(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR, position=position)
            else:
                self.wait_element(field, scrap_type=enum.ScrapType.MIXED, optional_term="label")
                #element = next(iter(self.web_scrap(term=field, scrap_type=enum.ScrapType.MIXED, optional_term=".tradiobutton .tradiobuttonitem label, .tcheckbox span")), None)
                element_list = self.web_scrap(term=field, scrap_type=enum.ScrapType.MIXED, optional_term=".tradiobutton .tradiobuttonitem label, .tcheckbox span", position=position)

        if not element_list:
            self.log_error("Couldn't find span element")

        if not element_list:
            self.log_error("Couldn't find span element")

        if element_list and len(element_list) -1 >= position:
            element = element_list[position]

        if 'input' not in element and element:
            input_element = next(iter(element.find_parent().select("input")), None)

        if not input_element:
            self.log_error("Couldn't find input element")

        xpath_input = lambda: self.driver.find_element_by_xpath(xpath_soup(input_element))

        if input_element.attrs['type'] == "checkbox" and "checked" in input_element.parent.attrs['class']:
            return None

        self.scroll_to_element(xpath_input())

        self.click(xpath_input())

    def result_checkbox(self, field, value):
        """
        [Internal]

        Checks expected value of a Checkbox element.

        :param field: The field whose value would be checked.
        :type field: str
        :param value: The expected value of the radio button.
        :type value: bool

        :return: Boolean if expected value was found on the element or not.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> assertion_value = self.result_checkbox("CheckBox1", True)
        """
        result = False
        time.sleep(1)
        lista = self.driver.find_elements(By.CSS_SELECTOR, ".tcheckbox.twidget")
        for line in lista:
            if line.is_displayed() and line.get_attribute('name').split('->')[1] == field:
                if "CHECKED" in line.get_attribute('class').upper():
                    result = True
        return result

    def clear_grid(self):
        """
        [Internal]

        Empties the global grid list variables.

        Usage:

        >>> # Calling the method:
        >>> self.clear_grid()
        """
        self.grid_input = []
        self.grid_check = []

    def input_grid_appender(self, column, value, grid_number=0, new=False, row=None, check_value = True):
        """
        [Internal]

        Adds a value to the input queue of a grid.

        :param column: The column of the grid that would receive the input.
        :type column: str
        :param value: The value that would be inputted.
        :type value: str
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 0
        :type grid_number: int
        :param new: Boolean value if this is a new line that should be added. - **Default:** 1
        :type new: bool
        :param row: Row number that will be filled
        :type row: int

        Usage:

        >>> # Calling the method:
        >>> self.input_grid_appender("A1_COD", "000001", 0)
        >>> # ---------------------------------------------
        >>> # Calling the method for a new line:
        >>> self.input_grid_appender("", "", 0, True)
        """
        if row is not None:
            row -= 1

        self.grid_input.append([column, value, grid_number, new, row, check_value])

    def check_grid_appender(self, line, column, value, grid_number=0):
        """
        [Internal]

        Adds a value to the check queue of a grid.

        :param line: The line of the grid that would be checked.
        :type line: int
        :param column: The column of the grid that would be checked.
        :type column: str
        :param value: The value that is expected.
        :type value: str
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 0
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> self.check_grid_appender(0,"A1_COD", "000001", 0)
        """
        self.grid_check.append([line, column, value, grid_number])

    def LoadGrid(self):
        """
        This method is responsible for running all actions of the input and check queues
        of a grid. After running, the queues would be empty.

        Must be called after SetValue and CheckResult calls that has the grid parameter set to True.

        Usage:

        >>> # After SetValue:
        >>> oHelper.SetValue("A1_COD", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #--------------------------------------
        >>> # After CheckResult:
        >>> oHelper.CheckResult("A1_COD", "000001", grid=True, line=1)
        >>> oHelper.LoadGrid()
        """

        x3_dictionaries = self.create_x3_tuple()

        initial_layer = 0
        if self.grid_input:
            self.wait_element(term=".tgetdados, .tgrid, .tcbrowse", scrap_type=enum.ScrapType.CSS_SELECTOR)

            if "tget" in self.get_current_container().next.attrs['class']:
                self.wait_element(self.grid_input[0][0])
            soup = self.get_current_DOM()
            initial_layer = len(soup.select(".tmodaldialog"))

        for field in self.grid_input:
            if field[3] and field[0] == "":
                self.new_grid_line(field)
            else:
                self.wait_blocker()
                print(f"Filling grid field: {field[0]}")
                self.fill_grid(field, x3_dictionaries, initial_layer)

        for field in self.grid_check:
            print(f"Checking grid field value: {field[1]}")
            self.check_grid(field, x3_dictionaries)

        self.clear_grid()

    def create_x3_tuple(self):
        """
        [Internal]

        Returns a tuple of dictionaries of field information based on all fields in the grid queues.

        :return: A tuple containing the needed x3 information.
        :rtype: Tuple of Dictionaries

        Usage:

        >>> # Calling the method:
        >>> x3_dictionaries = self.create_x3_tuple()
        """
        x3_dictionaries = ()
        inputs = list(map(lambda x: x[0], self.grid_input))
        checks = list(map(lambda x: x[1], self.grid_check))
        fields = list(filter(lambda x: "_" in x, inputs + checks))
        if fields:
            x3_dictionaries = self.get_x3_dictionaries(fields)
        return x3_dictionaries

    def fill_grid(self, field, x3_dictionaries, initial_layer):
        """
        [Internal]

        Fills the grid cell with the passed parameters.

        :param field: An item from the grid's input queue
        :type field: List of values
        :param x3_dictionaries: Tuple of dictionaries containing information extracted from x3.
        :type x3_dictionaries: Tuple of dictionaries
        :param initial_layer: The initial layer of elements of Protheus Webapp
        :type initial_layer: int

        Usage:

        >>> # Calling the method:
        >>> self.fill_grid(["A1_COD", "000001", 0, False], x3_dictionaries, 0)
        """

        field_to_label = {}
        field_to_valtype = {}
        field_to_len = {}

        current_value = ""
        column_name = ""
        rows = ""
        headers = ""
        columns = ""

        grids = None
        try_counter = 1
        grid_reload = True
        check_value = field[5]

        if(field[1] == True):
            field_one = 'is a boolean value'
        elif(field[1] == False):
            field_one = ''
        elif(isinstance(field[1],str)):
            field_one = self.remove_mask(field[1]).strip()

        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]
            field_to_valtype = x3_dictionaries[0]
            field_to_len = x3_dictionaries[1]
            
        if "_" in field[0]:
            try:
                column_name = field_to_label[field[0]].lower().strip()
            except:
                self.log_error("Couldn't find column '" + field[0] + "' in sx3 file. Try with the field label.")
        else:
            column_name = field[0].lower().strip()

        self.wait_element_timeout(term = column_name,
            scrap_type = enum.ScrapType.MIXED, timeout = self.config.time_out, optional_term = 'th label', main_container = 'body')

        endtime = time.time() + self.config.time_out
        while(self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body") and time.time() < endtime):
            print("Waiting for container to be active")
            time.sleep(1)
            
        if "tget" in self.get_current_container().next.attrs['class']:
            self.wait_element(field[0])

        endtime = time.time() + self.config.time_out
        while(self.remove_mask(current_value).strip().replace(',','') != field_one.replace(',','') and time.time() < endtime):
            
            endtime_row = time.time() + self.config.time_out
            while(time.time() < endtime_row and grid_reload):
                
                if not field[4]:
                    grid_reload = False

                container = self.get_current_container()

                if container:
                    try:
                        container_id = self.soup_to_selenium(container).get_attribute("id") if self.soup_to_selenium(container) else None
                    except Exception as err:
                        container_id = None
                        print(err)
                        pass
                    grids = container.select(".tgetdados, .tgrid, .tcbrowse")
                    grids = self.filter_displayed_elements(grids)

                if grids:
                    headers = self.get_headers_from_grids(grids)
                    if field[2] + 1 > len(grids):
                        grid_reload = True
                    else:
                        grid_id = grids[field[2]].attrs["id"]
                        if grid_id not in self.grid_counters:
                            self.grid_counters[grid_id] = 0

                        down_loop = 0
                        rows = grids[field[2]].select("tbody tr")
                else:
                    grid_reload = True
                
                if (field[4] is not None) and not (field[4] > len(rows) - 1 or field[4] < 0):
                    grid_reload = False

            if (field[4] is not None) and (field[4] > len(rows) - 1 or field[4] < 0):
                self.log_error(f"Couldn't select the specified row: {field[4] + 1}")

            if grids:
                if field[2] + 1 > len(grids):
                    self.log_error(f'{self.language.messages.grid_number_error} Grid number: {field[2] + 1} Grids in the screen: {len(grids)}')
            else:
                self.log_error("Grid element doesn't appear in DOM")

            row = rows[field[4]] if field[4] else self.get_selected_row(rows) if self.get_selected_row(rows) else(next(iter(rows), None))

            if row:
                while (int(row.attrs["id"]) < self.grid_counters[grid_id]) and (down_loop < 2) and self.down_loop_grid and field[4] is None and time.time() < endtime:
                    self.new_grid_line(field, False)
                    row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))
                    down_loop+=1
                self.down_loop_grid = False
                columns = row.select("td")
                if columns:
                    if column_name in headers[field[2]]:
                        column_number = headers[field[2]][column_name]

                        current_value = columns[column_number].text.strip()
                        xpath = xpath_soup(columns[column_number])
                        current_value = self.remove_mask(current_value).strip()

                        selenium_column = lambda: self.get_selenium_column_element(xpath) if self.get_selenium_column_element(xpath) else self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
                        self.scroll_to_element(selenium_column())
                        self.click(selenium_column())
                        self.set_element_focus(selenium_column())

                        soup = self.get_current_DOM()
                        tmodal_list = soup.select('.tmodaldialog.twidget.borderless')
                        tmodal_layer = len(tmodal_list) if tmodal_list else 0
                        while(time.time() < endtime and not self.element_exists(term=".tmodaldialog.twidget.borderless", scrap_type=enum.ScrapType.CSS_SELECTOR, position=tmodal_layer+1, main_container="body")):
                            time.sleep(1)
                            self.scroll_to_element(selenium_column())
                            self.set_element_focus(selenium_column())
                            self.click(selenium_column())
                            try:
                                ActionChains(self.driver).move_to_element(selenium_column()).send_keys_to_element(selenium_column(), Keys.ENTER).perform()
                            except WebDriverException:
                                try:
                                    self.send_keys(selenium_column(), Keys.ENTER)
                                except WebDriverException:
                                    pass
                            except:
                                pass

                            time.sleep(1)
                            if(field[1] == True):
                                field_one = ''
                                break

                        if(field[1] == True): break # if boolean field finish here.
                        self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body")
                        soup = self.get_current_DOM()
                        new_container = self.zindex_sort(soup.select(".tmodaldialog.twidget"), True)[0]
                        child = new_container.select("input")
                        child_type = "input"
                        option_text = ""
                        if not child:
                            child = new_container.select("select")
                            child_type = "select"

                        if child_type == "input":

                            time.sleep(2)
                            selenium_input = lambda: self.driver.find_element_by_xpath(xpath_soup(child[0]))
                            self.wait_element(term=xpath_soup(child[0]), scrap_type=enum.ScrapType.XPATH)
                            valtype = selenium_input().get_attribute("valuetype")
                            lenfield = len(self.get_element_value(selenium_input()))
                            user_value = field[1]
                            check_mask = self.check_mask(selenium_input())
                            if check_mask:
                                if (check_mask[0].startswith('@D') and user_value == ''):
                                    user_value = '00000000'
                                user_value = self.remove_mask(user_value)

                            self.wait_until_to( expected_condition = "visibility_of", element = selenium_input, timeout=True)
                            self.set_element_focus(selenium_input())
                            self.click(selenium_input())
                            if "tget" in self.get_current_container().next.attrs['class']:
                                bsoup_element = self.get_current_container().next
                                self.wait_until_to(expected_condition="element_to_be_clickable", element = bsoup_element, locator = By.XPATH, timeout=True)
                                self.try_send_keys(selenium_input, user_value, try_counter)

                                if try_counter < 2:
                                    try_counter += 1
                                else:
                                    try_counter = 0

                                if (("_" in field[0] and field_to_len != {} and int(field_to_len[field[0]]) > len(field[1])) or lenfield > len(field[1])):
                                    if (("_" in field[0] and field_to_valtype != {} and field_to_valtype[field[0]] != "N") or valtype != "N"):
                                        self.send_keys(selenium_input(), Keys.ENTER)
                                    else:
                                        if not (re.match(r"[0-9]+,[0-9]+", user_value)):
                                            self.send_keys(selenium_input(), Keys.ENTER)
                                        else:
                                            self.wait_element_timeout(term= ".tmodaldialog.twidget", scrap_type= enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, presence=False, main_container="body")
                                            if self.element_exists(term=".tmodaldialog.twidget", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body"):
                                                self.wait_until_to(expected_condition="element_to_be_clickable", element = bsoup_element, locator = By.XPATH, timeout=True)
                                                self.send_keys(selenium_input(), Keys.ENTER)
                                
                                elif lenfield == len(field[1]) and self.get_current_container().attrs['id'] != container_id:
                                    try:
                                        self.send_keys(selenium_input(), Keys.ENTER)
                                    except:
                                        pass
                                    
                            try_endtime = self.config.time_out / 4
                            while try_endtime > 0:
                                element_exist = self.wait_element_timeout(term=xpath_soup(child[0]), scrap_type=enum.ScrapType.XPATH, timeout = 10, presence=False)
                                time.sleep(1)
                                if element_exist:
                                    current_value = self.get_element_text(selenium_column())
                                    if current_value == None:
                                        current_value = ''
                                    break
                                else:
                                    try_endtime = try_endtime - 10
                                    containers = self.get_current_DOM().select(self.containers_selectors["GetCurrentContainer"])
                                    if child[0].parent.parent in containers:
                                        containers.remove(child[0].parent.parent)
                                    container_current = next(iter(self.zindex_sort(containers, True)))
                                    if container_current.attrs['id'] != container_id:
                                        print("Consider using the waithide and setkey('ESC') method because the input can remain selected.")
                                        return
                        else:
                            option_text_list = list(filter(lambda x: field[1] == x[0:len(field[1])], map(lambda x: x.text ,child[0].select('option'))))
                            option_value_dict = dict(map(lambda x: (x.attrs["value"], x.text), child[0].select('option')))
                            option_value = self.get_element_value(self.driver.find_element_by_xpath(xpath_soup(child[0])))
                            option_text = next(iter(option_text_list), None)
                            if not option_text:
                                self.log_error("Couldn't find option")
                            if (option_text != option_value_dict[option_value]):
                                self.select_combo(child[0], field[1])
                                if field[1] in option_text[0:len(field[1])]:
                                    current_value = field[1]
                            else:
                                self.send_keys(self.driver.find_element_by_xpath(xpath_soup(child[0])), Keys.ENTER)
                                current_value = field[1]
            
            if not check_value:
                break

        if ( check_value and self.remove_mask(current_value).strip().replace(',','') != field_one.replace(',','')):
            self.search_for_errors()
            self.check_grid_error(grids, headers, column_name, rows, columns, field)
            self.log_error(f"Current value: {current_value} | Couldn't fill input: {field_one} value in Column: '{column_name}' of Grid: '{headers[field[2]].keys()}'.")

    def get_selenium_column_element(self, xpath):
        """
        [Internal]

        Tries to get the selenium element out of a grid column.
        Workaround method to be used instead of a lambda function on fill_grid method.

        :param xpath: The xpath to the column.
        :type xpath: str

        Usage:

        >>> #  Calling the method:
        >>> self.get_selenium_column_element(xpath)
        """
        try:
            return self.driver.find_element_by_xpath(xpath)
        except:
            return False

    def try_recover_lost_line(self, field, grid_id, row, headers, field_to_label):
        """
        [Internal]

        Tries to recover the position if a new line is lost.

        Workaround method to keep trying to get the right row fill_grid method.

        :param field: An item from the grid's input queue
        :type field: List of values
        :param grid_id: The grid's ID
        :type grid_id: str
        :param row: The current row
        :type row: Beautiful Soup object
        :param headers: List of dictionaries with each grid's headers
        :type headers: List of Dictionaries
        :param field_to_label: Dictionary from the x3 containing the field to label relationship.
        :type field_to_label: Dict

        Usage:

        >>> # Calling the method:
        >>> self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
        """
        ret = None
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not ret):
            if self.config.debug_log:
                print("Recovering lost line")
            while ( time.time() < endtime and int(row.attrs["id"]) < self.grid_counters[grid_id]):
                self.new_grid_line(field, False)
                row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))

            columns = row.select("td")
            if columns:
                if "_" in field[0]:
                    column_name = field_to_label[field[0]]
                else:
                    column_name = field[0]
                
                column_name = column_name.lower()

                if column_name not in headers[field[2]]:
                    self.log_error(f"{self.language.messages.grid_column_error} Coluna: '{column_name}' Grid: '{headers[field[2]].keys()}'")

                column_number = headers[field[2]][column_name]
                xpath = xpath_soup(columns[column_number])
                ret = self.get_selenium_column_element(xpath)

        return ret
 
    def check_grid(self, field, x3_dictionaries, get_value=False):
        """
        [Internal]

        Checks the grid cell with the passed parameters.

        :param field: An item from the grid's check queue
        :type field: List of values
        :param x3_dictionaries: Tuple of dictionaries containing information extracted from x3.
        :type x3_dictionaries: Tuple of dictionaries
        :param get_value: Boolean value if check_grid should return its value.
        :type get_value: bool

        :return: If get_value flag is True, it will return the captured value.
        :return type: str

        Usage:

        >>> # Calling the method:
        >>> self.check_grid([0, "A1_COD", "000001", 0], x3_dictionaries, False)
        """
        text = ""
        column_name = ""

        field_to_label = {}
        
        grids = None
        columns = None
        headers = None
        rows = None

        success  = False

        endtime = time.time() + self.config.time_out
        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]

        while(self.element_exists(term=".tmodaldialog .ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=3, main_container="body") and time.time() < endtime):
            if self.config.debug_log:
                print("Waiting for container to be active")
            time.sleep(1)

        while(time.time() < endtime and not success):

            containers = self.web_scrap(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            container = next(iter(self.zindex_sort(containers, True)), None)

            if container:
                grids = container.select(".tgetdados, .tgrid, .tcbrowse")
                grids = self.filter_displayed_elements(grids)

            if grids:
                headers = self.get_headers_from_grids(grids)
                column_name = ""

                if field[3] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                rows = grids[field[3]].select("tbody tr")
                
                if rows:
                    if field[0] > len(rows):
                        self.log_error(self.language.messages.grid_line_error) 

                    field_element = next(iter(field), None)
                   
                    if field_element != None and len(rows) -1 >= field_element:
                        columns = rows[field_element].select("td")
                        
                if columns and rows:

                    if "_" in field[1]:
                        column_name = field_to_label[field[1]].lower()
                    else:
                        column_name = field[1].lower()

                    if column_name in headers[field[3]]:
                        column_number = headers[field[3]][column_name]
                        text = columns[column_number].text.strip()
                        success = True

                    if success and get_value and text:
                        return text

        field_name = f"({field[0]}, {column_name})"
        self.log_result(field_name, field[2], text)
        print(f"Collected value: {text}")
        if not success:
            self.check_grid_error( grids, headers, column_name, rows, columns, field )

    def check_grid_error(self, grid, headers, column_name, rows, columns, field):
        """
        [Internal]

        """
        error = False

        if not grid:
            self.log_error("Couldn't find grids.")
            error = True

        if not error and column_name not in headers[field[3]]:
            self.log_error(f"{self.language.messages.grid_column_error} Coluna: '{column_name}' Grid: '{headers[field[3]].keys()}'")
            error = True
        
        if not error and not columns:
            self.log_error("Couldn't find columns.")

        if not error and not rows:
            self.log_error("Couldn't find rows.")
            error = True

        return
        

    def new_grid_line(self, field, add_grid_line_counter=True):
        """
        [Internal]

        Creates a new line on the grid.

        :param field: An item from the grid's input queue
        :type field: List of values
        :param add_grid_line_counter: Boolean if counter should be incremented when method is called. - **Default:** True
        :type add_grid_line_counter: bool

        Usage:

        >>> # Calling the method:
        >>> self.new_grid_line(["", "", 0, True])
        """
        grids = ''
        endtime = time.time() + self.config.time_out
        self.down_loop_grid = True
        while(not grids and time.time() < endtime):
            soup = self.get_current_DOM()

            containers = soup.select(".tmodaldialog.twidget")
            if containers:
                containers = self.zindex_sort(containers, True)
                grids = self.filter_displayed_elements(containers[0].select(".tgetdados, .tgrid"))

            time.sleep(1)

        if grids:
            if field[2] > len(grids):
                self.log_error(self.language.messages.grid_number_error)
            rows = grids[field[2]].select("tbody tr")
            row = self.get_selected_row(rows)
            if row:
                columns = row.select("td")
                if columns:
                    second_column = lambda: self.driver.find_element_by_xpath(xpath_soup(columns[1]))
                    # self.scroll_to_element(second_column())
                    self.driver.execute_script("$('.horizontal-scroll').scrollLeft(-400000);")
                    self.set_element_focus(second_column())
                    self.wait_until_to(expected_condition="visibility_of_element_located", element = columns[0], locator=By.XPATH )
                    
                    ActionChains(self.driver).move_to_element(second_column()).send_keys_to_element(second_column(), Keys.DOWN).perform()

                    endtime = time.time() + self.config.time_out
                    while (time.time() < endtime and not(self.element_exists(term=".tgetdados tbody tr, .tgrid tbody tr", scrap_type=enum.ScrapType.CSS_SELECTOR, position=len(rows)+1))):
                        if self.config.debug_log:
                            print("Waiting for the new line to show")
                        time.sleep(1)

                    if (add_grid_line_counter):
                        self.add_grid_row_counter(grids[field[2]])
                else:
                    self.log_error("Couldn't find columns.")
            else:
                self.log_error("Couldn't find rows.")
        else:
            self.log_error("Couldn't find grids.")

    def ClickGridCell(self, column, row_number=1, grid_number=1):
        """
        Clicks on a Cell of a Grid.

        :param column: The column that should be clicked.
        :type column: str
        :param row_number: Grid line that contains the column field to be checked.- **Default:** 1
        :type row_number: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickGridCell("Product", 1)
        """
        success = False
        grids = None
        row_number -= 1
        grid_number -= 1
        column_name = ""
        column = column.strip()
        column_element_old_class = None
        columns =  None
        rows = None
        
        self.wait_blocker()
        self.wait_element(term=".tgetdados tbody tr, .tgrid tbody tr, .tcbrowse", scrap_type=enum.ScrapType.CSS_SELECTOR)
        self.wait_element_timeout(term = column, scrap_type = enum.ScrapType.TEXT, timeout = self.config.time_out , optional_term = 'label')
        
        endtime = time.time() + self.config.time_out

        if re.match(r"\w+(_)", column):
            column_name = self.get_x3_dictionaries([column])[2][column].lower()
        else:
            column_name = column.lower()

        while(not success and time.time() < endtime):

            containers = self.web_scrap(term=".tmodaldialog,.ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            container = next(iter(self.zindex_sort(containers, True)), None)
            if container:
                grids = self.filter_displayed_elements(container.select(".tgetdados, .tgrid, .tcbrowse"))

                if grids:
                    grids = list(filter(lambda x:x.select("tbody tr"), grids))      
                    headers = self.get_headers_from_grids(grids)
                    if grid_number < len(grids):
                        rows = grids[grid_number].select("tbody tr")
                    if rows:
                        if row_number < len(rows):
                            columns = rows[row_number].select("td")
                    if columns:
                        if column_name in headers[grid_number]:
                            column_number = headers[grid_number][column_name]
                            column_element = lambda : self.driver.find_element_by_xpath(xpath_soup(columns[column_number]))
                            if column_element_old_class == None:
                                column_element_old_class = column_element().get_attribute("class")

                            self.wait_until_to(expected_condition="element_to_be_clickable", element = columns[column_number], locator = By.XPATH, timeout=True)
                            self.click(column_element())
                            self.wait_element_is_focused(element_selenium = column_element, time_out = 2)

                            if column_element_old_class != column_element().get_attribute("class") or 'selected' in column_element().get_attribute("class") :
                                self.wait_until_to(expected_condition="element_to_be_clickable", element = columns[column_number], locator = By.XPATH, timeout=True)
                                self.wait_blocker()
                                success = True
                            elif grids[grid_number] and "tcbrowse" in grids[grid_number].attrs['class']:
                                time.sleep(0.5)
                                success = True

        if not success:
            self.log_error(f"Couldn't Click on grid cell \ngrids:{grids}\nrows: {rows} ")


    def ClickGridHeader( self, column = 1, column_name = '', grid_number = 1):
        """
        Clicks on a Cell of a Grid Header.

        :param column: The column index that should be clicked.
        :type column: int
        :param column_name: The column index that should be clicked.
        :type row_number: str
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickGridHeader(column = 1 , grid_number =  1)
        >>> oHelper.ClickGridHeader(column_name = 'Código' , grid_number =  1)
        >>> oHelper.ClickGridHeader(column = 1 , grid_number =  2)
        """
        grid_number -= 1
        column -=1 if column > 0 else 0

        self.wait_element(term=".tgetdados tbody tr, .tgrid tbody tr, .tcbrowse", scrap_type=enum.ScrapType.CSS_SELECTOR)
        grid  = self.get_grid(grid_number)
        header = self.get_headers_from_grids(grid)
        if not column_name:
            column_element = grid.select('thead label')[column].parent.parent
            column_element_selenium = self.soup_to_selenium(column_element)
            self.set_element_focus(column_element_selenium)
            self.wait_until_to(expected_condition="element_to_be_clickable", element = column_element, locator = By.XPATH )
            column_element_selenium.click()
        else:
            column_name =column_name.lower()
            header = self.get_headers_from_grids(grid)

            if column_name in header[grid_number]:
                column_number = header[grid_number][column_name]

            column_element = grid.select('thead label')[column_number].parent.parent
            column_element_selenium = self.soup_to_selenium(column_element)
            self.set_element_focus(column_element_selenium)
            self.wait_until_to(expected_condition="element_to_be_clickable", element = column_element, locator = By.XPATH )
            column_element_selenium.click()
            
                
        

    def search_column_index(self, grid, column):
        column_enumeration = list(enumerate(grid.select("thead label")))
        chosen_column = next(iter(list(filter(lambda x: column in x[1].text, column_enumeration))), None)
        if chosen_column:
            column_index = chosen_column[0]
        else: 
            self.log_error("Couldn't find chosen column.")

        return column_index

    def get_x3_dictionaries(self, fields): 
        """
        [Internal]

        Generates the dictionaries with field comparisons from the x3 file,

        Dictionaries:Field to Type, Field to Size, Field to Title.

        :param fields: List of fields that must be located in x3.
        :type fields: List of str

        :return: The three x3 dictionaries in a Tuple.
        :trype: Tuple of Dictionary

        Usage:

        >>> # Calling the method:
        >>> x3_dictionaries = self.get_x3_dictionaries(field_list)
        """
        prefixes = list(set(map(lambda x:x.split("_")[0] + "_" if "_" in x else "", fields)))
        regex = self.generate_regex_by_prefixes(prefixes)

        #caminho do arquivo csv(SX3)
        path = os.path.join(os.path.dirname(__file__), r'core\\data\\sx3.csv')

        #DataFrame para filtrar somente os dados da tabela informada pelo usuário oriundo do csv.
        data = pd.read_csv(path, sep=';', encoding='latin-1', header=None, error_bad_lines=False,
                        index_col='Campo', names=['Campo', 'Tipo', 'Tamanho', 'Titulo', 'Titulo_Spa', 'Titulo_Eng', None], low_memory=False)
        df = pd.DataFrame(data, columns=['Campo', 'Tipo', 'Tamanho', 'Titulo', 'Titulo_Spa', 'Titulo_Eng', None])
        if not regex:
            df_filtered = df.query("Tipo=='C' or Tipo=='N' or Tipo=='D' ")
        else:
            df_filtered = df.filter(regex=regex, axis=0)

        if self.config.language == "es-es":
            df_filtered.Titulo = df_filtered.loc[:,('Titulo_Spa')].str.strip()
        elif self.config.language == "en-us":
            df_filtered.Titulo = df_filtered.loc[:,('Titulo_Eng')].str.strip()
        else:
            df_filtered.Titulo = df_filtered.loc[:,('Titulo')].str.strip()

        df_filtered.index = df_filtered.index.map(lambda x: x.strip())

        dict_ = df_filtered.to_dict()

        return (dict_['Tipo'], dict_['Tamanho'], dict_['Titulo'])

    def generate_regex_by_prefixes(self, prefixes):
        """
        [Internal]

        Returns a regex string created by combining all field prefixes.

        :param prefixes: Prefixes of fields to be combined in a regex.
        :type prefixes: List of str

        Usage:

        >>> # Calling the method:
        >>> regex = self.generate_regex_by_prefixes(field_prefixes)
        """
        filtered_prefixes = list(filter(lambda x: x != "", prefixes))
        regex = ""
        for prefix in filtered_prefixes:
            regex += "^" + prefix + "|"

        return regex[:-1]

    def get_headers_from_grids(self, grids):
        """
        [Internal]

        Returns the headers of each grid in *grids* parameter.

        :param grids: The grids to extract the headers.
        :type grids: List of BeautifulSoup objects

        :return: List of Dictionaries with each header value and index.
        :rtype: List of Dict

        Usage:

        >>> # Calling the method:
        >>> headers = self.get_headers_from_grids(grids)
        """
        headers = []
        for item in grids:
            labels = item.select("thead tr label")
            if labels:
                keys = list(map(lambda x: x.text.strip().lower(), labels))
                values = list(map(lambda x: x[0], enumerate(labels)))
                headers.append(dict(zip(keys, values)))
        return headers

    def add_grid_row_counter(self, grid):
        """
        [Internal]

        Adds the counter of rows to the global dictionary.

        :param grid: The grid whose rows are being controlled.
        :type grid: BeautifulSoup object.

        Usage:

        >>> # Calling the method:
        >>> self.add_grid_row_counter(grid)
        """
        grid_id = grid.attrs["id"]

        if grid_id not in self.grid_counters:
            self.grid_counters[grid_id] = 0
        else:
            self.grid_counters[grid_id]+=1
    
    def wait_element_is_not_displayed(self, element_soup, timeout = 5 , step=0.3):
        """
        [Internal]

        Wait element.is_displayed() return false
        :param element_soup: The element soup.
        :type element_soup: BeautifulSoup object.
        :param timeout: The maximum amount of time of wait. - **Default:** 5.0
        :type timeout: float
        :param step: The amount of time each step should wait. - **Default:** 0.1
        :type step: float

        Usage:

        >>> # Calling the method:
        >>> self.wait_element_is_not_displayed(soup_element, 10, 0.5)
        """
        endtime = time.time() + timeout
        try:
            print('Waiting for element to disappear')
            while(self.element_is_displayed(element_soup) and time.time() <= endtime):
                time.sleep(step)
        except Exception:
            return

    def wait_element_is_focused(self, element_selenium = None, time_out = 5, step = 0.1):
        """
        [ Internal ]
        Wait element Lose focus
        """
        endtime = time.time() + time_out
        while( element_selenium and time.time() < endtime and self.switch_to_active_element() != element_selenium() ):
            time.sleep(step)

    def wait_element_is_not_focused(self, element_selenium = None, time_out = 5, step = 0.1):
        """
        [ Internal ]
        Wait element Lose focus
        """
        endtime = time.time() + time_out
        while( element_selenium and time.time() < endtime and self.switch_to_active_element() == element_selenium() ):
            time.sleep(step)

    def switch_to_active_element(self):
        """
        [Internal]
        Call switch_to_active_element method
        """
        try:
            self.driver.switch_to_active_element()
        except NoSuchElementException:
            return None
        except Exception as e:
            print(f"Warning switch_to_active_element() exception : {str(e)}")
            return None

    def wait_element(self, term, scrap_type=enum.ScrapType.TEXT, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog", check_error=True):
        """
        [Internal]

        Waits until the desired element is located on the screen.

        :param term: The first search term. A text or a selector.
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param presence: If the element should exist or not in the screen. - **Default:** False
        :type presence: bool
        :param position: If the element should exist at a specific position. e.g. The fourth button. - **Default:** 0
        :type position: int
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str

        Usage:

        >>> # Calling the method:
        >>> self.wait_element(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        """
        endtime = time.time() + self.config.time_out
        if self.config.debug_log:
            print("Waiting for element")

        if presence:
            while (not self.element_exists(term, scrap_type, position, optional_term, main_container, check_error) and time.time() < endtime):
                time.sleep(0.1)
        else:
            while (self.element_exists(term, scrap_type, position, optional_term, main_container, check_error) and time.time() < endtime):
                time.sleep(0.1)

        if time.time() > endtime:
            if term == "[name='cGetUser']":
                self.close_resolution_screen()
            else:
                if ".ui-button.ui-dialog-titlebar-close[title='Close']" in term:
                    return False
                self.restart_counter += 1
                self.log_error(f"Element {term} not found!")

        presence_endtime = time.time() + 10
        if presence:

            if self.config.debug_log:
                print("Element found! Waiting for element to be displayed.")

            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error)), None)
            
            if element is not None:

                sel_element = lambda:self.soup_to_selenium(element)
                sel_element_isdisplayed = False

                while(not sel_element_isdisplayed and time.time() < presence_endtime):
                    try:
                        if sel_element != None:
                            sel_element_isdisplayed = sel_element().is_displayed()
                        else:
                            sel_element = lambda:self.soup_to_selenium(element)
                        time.sleep(0.1)
                    except AttributeError:
                        pass
                    except StaleElementReferenceException:
                        pass


    def wait_element_timeout(self, term, scrap_type=enum.ScrapType.TEXT, timeout=5.0, step=0.1, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog, body", check_error=True):
        """
        [Internal]

        Waits until the desired element is located on the screen or until the timeout is met.

        :param term: The first search term. A text or a selector.
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param timeout: The maximum amount of time of wait. - **Default:** 5.0
        :type timeout: float
        :param timeout: The amount of time each step should wait. - **Default:** 0.1
        :type timeout: float
        :param presence: If the element should exist or not in the screen. - **Default:** False
        :type presence: bool
        :param position: If the element should exist at a specific position. e.g. The fourth button. - **Default:** 0
        :type position: int
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str

        Usage:

        >>> # Calling the method:
        >>> self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button", timeout=10, step=0.1)
        """
        success = False
        if presence:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if self.element_exists(term, scrap_type, position, optional_term, main_container, check_error):
                    success = True
                    break
        else:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if not self.element_exists(term, scrap_type, position, optional_term, main_container, check_error):
                    success = True
                    break

        if presence and success:
            if self.config.debug_log:
                print("Element found! Waiting for element to be displayed.")
            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error)), None)
            if element is not None:
                sel_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                endtime = time.time() + timeout
                while(time.time() < endtime and not self.element_is_displayed(element)):
                    try:
                        time.sleep(0.1)
                        self.scroll_to_element(sel_element())
                        if(sel_element().is_displayed()):
                            break
                    except:
                        continue
        return success

    def get_selected_row(self, rows):
        """
        [Internal]

        From a list of rows, filter the selected one.

        :param rows: List of rows.
        :type rows: List of Beautiful Soup objects

        :return: The selected row.
        :rtype: Beautiful Soup object.

        Usage:

        >>> # Calling the method:
        >>> selected_row = self.get_selected_row(rows)
        """
        filtered_rows = list(filter(lambda x: len(x.select("td.selected-cell")), rows))
        if filtered_rows:
            return next(iter(filtered_rows))
        else:
            filtered_rows = list(filter(lambda x: "selected-row" == self.soup_to_selenium(x).get_attribute('class'), rows))
            if filtered_rows:
                return next(iter(list(filter(lambda x: "selected-row" == self.soup_to_selenium(x).get_attribute('class'), rows))), None)

    def SetFilePath(self, value, button = ""):
        """
        Fills the path screen with the desired path 
        
        .. warning::
            Necessary informed the button name or the program will select the current button name.

        :param value: Path to be inputted.
        :type value: str
        :param button: Name button from path screen.
        :type button: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFilePath(r"C:\\folder")
        >>> oHelper.SetFilePath(r"C:\\folder","save")
        """
        self.wait_element(self.language.file_name)
        element = self.driver.find_element(By.CSS_SELECTOR, ".filepath input")
        if element:
            self.driver.execute_script("document.querySelector('#{}').value='';".format(element.get_attribute("id")))
            self.send_keys(element, value)
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".tremoteopensave button")
        if elements:
            for line in elements:
                if button != "":
                    if line.text.strip().upper() == button.upper():
                        self.click(line)
                        break
                elif line.text.strip().upper() == self.language.open.upper():
                     self.click(line)
                     break
                elif line.text.strip().upper() == self.language.save.upper():
                     self.click(line)
                     break
                else:
                    self.log_error(f"Button: {button} not found")

    def MessageBoxClick(self, button_text):
        """
        Clicks on desired button inside a Messagebox element.

        :param button_text: Desired button to click.
        :type button_text: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.MessageBoxClick("Ok")
        """
        self.wait_element(".messagebox-container", enum.ScrapType.CSS_SELECTOR)

        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")
        container = soup.select(".messagebox-container")
        if container:
            buttons = container[0].select(".ui-button")
            button = list(filter(lambda x: x.text.lower() == button_text.lower(), buttons))
            if button:
                selenium_button = self.driver.find_element_by_xpath(xpath_soup(button[0]))
                self.click(selenium_button)

    def get_enchoice_button_ids(self, layer):
        """
        [Internal]

        If current layer level has an enchoice, returns all buttons' ids.

        :param layer: Current layer level that the application is.
        :type layer: int

        :return: List with enchoice's buttons' ids.
        :rtype: List of str

        Usage:

        >>> # Calling the method:
        >>> self.get_enchoice_button_ids(current_layer)
        """
        try:
            soup = self.get_current_DOM()
            current_layer = self.zindex_sort(soup.select(".tmodaldialog"), False)[layer - 1]
            buttons = list(filter(lambda x: x.text.strip() != "", current_layer.select(".tpanel button")))
            return list(map(lambda x: x.parent.attrs["id"], buttons))
        except Exception as error:
            print(error)
            return []

    def CheckView(self, text, element_type="help"):
        """
        Checks if a certain text is present in the screen at the time and takes an action.

        "help" - alerts with messages of errors.

        :param text: Text to be checked.
        :type text: str
        :param element_type: Type of element. - **Default:** "help"
        :type element_type: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.CheckView("Processing")
        """
        if element_type == "help":
            print(f"Checking text on screen: {text}")
            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=".tsay", check_error=False)
            if not self.element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay", check_error=False):
                self.errors.append(f"{self.language.messages.text_not_found}({text})")

    def try_send_keys(self, element_function, key, try_counter=0):
        """
        [Internal]

        Tries to send value to element using different techniques.
        Meant to be used inside of a loop.

        :param element_function: The function that returns the element that would receive the value.
        :type element_function: function object
        :param key: The value that would be sent to the element.
        :type key: str or selenium.webdriver.common.keys
        :param try_counter: This counter will decide which technique should be used. - **Default:** 0
        :type try_counter: int

        Usage:

        >>> # Calling the method:
        >>> self.try_send_keys(selenium_input, user_value, try_counter)
        """
        self.wait_until_to( expected_condition = "visibility_of", element = element_function )
        
        if try_counter == 0:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            element_function().send_keys(key)
        elif try_counter == 1:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            ActionChains(self.driver).move_to_element(element_function()).send_keys_to_element(element_function(), key).perform()
        else:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            ActionChains(self.driver).move_to_element(element_function()).send_keys(key).perform()

    def find_label_element(self, label_text, container= None, position = 1, input_field=True, direction=None):
        """
        [Internal]

        Find input element next to label containing the label_text parameter.

        :param label_text: The label text to be searched
        :type label_text: str
        :param container: The main container object to be used
        :type container: BeautifulSoup object

        :return: A list containing a BeautifulSoup object next to the label
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> self.find_label_element("User:", container_object)
        """
        try:
            if container:
                elements = self.filter_label_element(label_text, container)
            if elements:
                for element in elements:
                    elem = self.search_element_position(label_text, position, input_field, direction)
                    if elem:
                        return elem

                    #Checking previous and next element:
                    next_sibling = element.find_next_sibling("div")
                    second_next_sibling = next_sibling.find_next_sibling("div")

                    previous_sibling = element.find_next_sibling("div")
                    second_previous_sibling = previous_sibling.find_next_sibling("div")

                    #If current element is tsay and next or second next element is tget or tcombobox => return tget or tcombobox
                    if (hasattr(element, "attrs") and "class" in element.attrs
                        and "tsay" in element.attrs["class"]
                        and (hasattr(next_sibling, "attrs") and "class" in next_sibling.attrs and "id" in next_sibling.attrs
                        and ("tget" in next_sibling.attrs["class"] or "tcombobox" in next_sibling.attrs["class"])
                        and next_sibling.attrs["id"] not in self.used_ids)
                        or (hasattr(second_next_sibling, "attrs") and "class" in second_next_sibling.attrs and "id" in second_next_sibling.attrs
                        and ("tget" in second_next_sibling.attrs["class"] or "tcombobox" in second_next_sibling.attrs["class"])
                        and second_next_sibling.attrs["id"] not in self.used_ids)):

                        if (("tget" in next_sibling.attrs["class"]
                                or "tcombobox" in next_sibling.attrs["class"])
                                and next_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[next_sibling.attrs["id"]] = container.attrs["id"]
                            return [next_sibling]
                        elif (("tget" in second_next_sibling.attrs["class"]
                                or "tcombobox" in second_next_sibling.attrs["class"])
                                and second_next_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[second_next_sibling.attrs["id"]] = container.attrs["id"]
                            return [second_next_sibling]
                        else:
                            return[]

                    #If current element is tsay and previous or second previous element is tget or tcombobox => return tget or tcombobox
                    elif (hasattr(element, "attrs") and "class" in element.attrs
                        and "tsay" in element.attrs["class"]
                        and (hasattr(previous_sibling, "attrs") and "class" in previous_sibling.attrs and "id" in previous_sibling.attrs
                        and ("tget" in previous_sibling.attrs["class"] or "tcombobox" in previous_sibling.attrs["class"])
                        and previous_sibling.attrs["id"] not in self.used_ids)
                        or (hasattr(second_previous_sibling, "attrs") and "class" in second_previous_sibling.attrs and "id" in second_previous_sibling.attrs
                        and ("tget" in second_previous_sibling.attrs["class"] or "tcombobox" in second_previous_sibling.attrs["class"])
                        and second_previous_sibling.attrs["id"] not in self.used_ids)):

                        if (("tget" in previous_sibling.attrs["class"]
                                or "tcombobox" in previous_sibling.attrs["class"])
                                and previous_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[previous_sibling.attrs["id"]] = container.attrs["id"]
                            return [previous_sibling]
                        elif (("tget" in second_previous_sibling.attrs["class"]
                                or "tcombobox" in second_previous_sibling.attrs["class"])
                                and second_previous_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[second_previous_sibling.attrs["id"]] = container.attrs["id"]
                            return [second_previous_sibling]
                        else:
                            return []

                    #If element is not tsay => return it
                    elif (hasattr(element, "attrs") and "class" in element.attrs
                        and "tsay" not in element.attrs["class"]):
                        return self.search_element_position(label_text)
                        
                #If label exists but there is no element associated with it => return empty list
                if not element:
                    return []
                else:
                    return self.search_element_position(label_text)
            else:
                return []
        except AttributeError:
            return self.search_element_position(label_text)
            
    def log_error(self, message, new_log_line=True, skip_restart=False):
        """
        [Internal]

        Finishes execution of test case with an error and creates the log information for that test.

        :param message: Message to be logged
        :type message: str
        :param new_log_line: Boolean value if Message should be logged as new line or not. - **Default:** True
        :type new_log_line: bool

        Usage:

        >>> #Calling the method:
        >>> self.log_error("Element was not found")
        """
        self.clear_grid()
        print(f"Warning log_error {message}")

        if self.config.smart_test:
            print(f"***System Info*** in log_error():")
            system_info()

        routine_name = self.config.routine if ">" not in self.config.routine else self.config.routine.split(">")[-1].strip()
        routine_name = routine_name if routine_name else "error"

        stack_item = self.log.get_testcase_stack()
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number} {message}"
        self.message = log_message
        self.expected = False
        self.log.seconds = self.log.set_seconds(self.log.initial_time)
        self.log.testcase_seconds = self.log.set_seconds(self.log.testcase_initial_time)
        self.log.ct_method, self.log.ct_number = self.log.ident_test()

        if self.config.new_log:
            self.execution_flow()

        if self.config.screenshot:
            self.log.take_screenshot_log(self.driver, stack_item, test_number)

        if new_log_line:
            self.log.new_line(False, log_message)
        if ((stack_item != "setUpClass") or (stack_item == "setUpClass" and self.restart_counter == 3)):
            self.log.save_file()
        if not self.config.skip_restart and len(self.log.list_of_testcases()) > 1 and self.config.initial_program != '':
            self.restart()
        elif self.config.coverage and self.config.initial_program != '':
            self.restart()
        else:            
            try:
                self.driver.close()
            except Exception as e:
                print(f"Warning Log Error Close {str(e)}")

        if self.restart_counter > 2:

            if self.config.num_exec and stack_item == "setUpClass" and self.log.checks_empty_line():
                if not self.num_exec.post_exec(self.config.url_set_end_exec):
                    self.restart_counter = 3
                    self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")
                
            if (stack_item == "setUpClass") :
                try:
                    self.driver.close()
                except Exception as e:
                    print(f"Warning Log Error Close {str(e)}")

        if ((stack_item != "setUpClass") or (stack_item == "setUpClass" and self.restart_counter == 3)):
            if self.restart_counter >= 3:
                self.restart_counter = 0
            self.assertTrue(False, log_message)
        
    def ClickIcon(self, icon_text):
        """
        Clicks on an Icon button based on its tooltip text or Alt attribute title.

        :param icon_text: The tooltip/title text.
        :type icon_text: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickIcon("Add")
        >>> oHelper.ClickIcon("Edit")
        """
        icon = ""
        success = False
        filtered_buttons = None
        
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not icon and not success):
            self.wait_element(term=".ttoolbar, .tbtnbmp", scrap_type=enum.ScrapType.CSS_SELECTOR)
            soup = self.get_current_DOM()
            container = next(iter(self.zindex_sort(soup.select(".tmodaldialog"))), None)
            container = container if container else soup
            tbtnbmp_img = self.on_screen_enabled(container.select(".tbtnbmp > img"))
            tbtnbmp_img_str = " ".join(str(x) for x in tbtnbmp_img) if tbtnbmp_img else ''

            if icon_text not in tbtnbmp_img_str:
                container = self.get_current_container()
                tbtnbmp_img = self.on_screen_enabled(container.select(".tbtnbmp > img"))
            
            if tbtnbmp_img:
                icon = next(iter(list(filter(lambda x: icon_text == self.soup_to_selenium(x).get_attribute("alt"), tbtnbmp_img))), None)

            else:
                buttons = self.on_screen_enabled(container.select("button[style]"))
                print("Searching for Icon")
                if buttons:
                    filtered_buttons = self.filter_by_tooltip_value(buttons, icon_text)
                    if filtered_buttons:
                        icon = next(iter(filtered_buttons), None)

            if icon:
                element = lambda: self.soup_to_selenium(icon)
                self.set_element_focus(element())
                success = self.click(element())

        if not icon:
            self.log_error(f"Couldn't find Icon: {icon_text}.")
        if not success:
            self.log_error(f"Couldn't click Icon: {icon_text}.")

    def AddParameter(self, parameter, branch, portuguese_value, english_value="", spanish_value=""):
        """
        Adds a parameter to the queue of parameters to be set by SetParameters method.

        :param parameter: The parameter name.
        :type parameter: str
        :param branch: The branch to be filled in parameter edit screen.
        :type branch: str
        :param portuguese_value: The value for a portuguese repository.
        :type portuguese_value: str
        :param english_value: The value for an english repository.
        :type english_value: str
        :param spanish_value: The value for a spanish repository.
        :type spanish_value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        """
        self.parameters.append([parameter.strip(), branch, portuguese_value, english_value, spanish_value])

    def SetParameters(self):
        """
        Sets the parameters in CFG screen. The parameters must be passed with calls for **AddParameter** method.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        self.parameter_screen(restore_backup=False)

    def RestoreParameters(self):
        """
        Restores parameters to previous value in CFG screen. Should be used after a **SetParameters** call.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        self.parameter_screen(restore_backup=True)

    def parameter_screen(self, restore_backup):
        """
        [Internal]

        Internal method of SetParameters and RestoreParameters.

        :param restore_backup: Boolean if method should restore the parameters.
        :type restore_backup: bool

        Usage:

        >>> # Calling the method:
        >>> self.parameter_screen(restore_backup=False)
        """
        label_param = None
        exception = None
        stack = None

        try:
            self.driver_refresh()
        except Exception as error:
            exception = error

        if not exception:
            if self.config.browser.lower() == "chrome":
                try:
                    self.wait_until_to( expected_condition = "alert_is_present" )
                    self.driver.switch_to_alert().accept()
                except:
                    pass

            self.Setup("SIGACFG", self.config.date, self.config.group, self.config.branch, save_input=False)
            self.SetLateralMenu(self.config.parameter_menu if self.config.parameter_menu else self.language.parameter_menu, save_input=False)

            self.wait_element(term=".ttoolbar", scrap_type=enum.ScrapType.CSS_SELECTOR)
            self.wait_element_timeout(term="img[src*=bmpserv1]", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=5.0, step=0.5)

            if self.element_exists(term="img[src*=bmpserv1]", scrap_type=enum.ScrapType.CSS_SELECTOR):
                
                endtime = time.time() + self.config.time_out

                while(time.time() < endtime and not label_param):

                    container = self.get_current_container()
                    img_serv1 = next(iter(container.select("img[src*='bmpserv1']")), None )
                    label_serv1 = next(iter(img_serv1.parent.select('label')), None)
                    
                    if label_serv1:
                        self.ClickTree(label_serv1.text.strip())
                        self.wait_element_timeout(term="img[src*=bmpparam]", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=5.0, step=0.5)
                        container = self.get_current_container()
                        img_param = next(iter(container.select("img[src*='bmpparam']")), None )
                        if img_param and img_param.parent.__bool__():
                            label_param = next(iter(img_param.parent.select('label')), None)

                            self.ClickTree(label_param.text.strip())

                if not label_param:
                    self.log_error(f"Couldn't find Icon")

            self.ClickIcon(self.language.search)

            self.fill_parameters(restore_backup=restore_backup)
            self.parameters = []
            self.ClickIcon(self.language.exit)
            time.sleep(1)

            if self.config.coverage:
                self.driver_refresh()
            else:
                self.Finish()

            self.Setup(self.config.initial_program, self.config.date, self.config.group, self.config.branch, save_input=not self.config.autostart)

            if ">" in self.config.routine:
                self.SetLateralMenu(self.config.routine, save_input=False)
            else:
                self.Program(self.config.routine)
        else:
            stack = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('tearDownClass', x.function), inspect.stack())))), None)
            if(stack and not stack.lower()  == "teardownclass"):
                self.restart_counter += 1
                self.log_error(f"Wasn't possible execute parameter_screen() method Exception: {exception}")


    def fill_parameters(self, restore_backup):
        """
        [Internal]

        Internal method of fill_parameters.
        Searches and edits all parameters in the queue.

        :param restore_backup: Boolean if method should restore the parameters.
        :type restore_backup: bool

        Usage:

        >>> # Calling the method:
        >>> self.fill_parameters(restore_backup=False)
        """
        parameter_list = self.backup_parameters if restore_backup else self.parameters
        for parameter in parameter_list:
            self.SetValue(self.language.search_by, parameter[0])
            self.used_ids = []
            self.SetButton(self.language.search2)
            self.ClickIcon(self.language.edit)

            if not restore_backup:
                current_branch = self.GetValue("X6_FIL")
                current_pt_value = self.GetValue("X6_CONTEUD")
                current_en_value = self.GetValue("X6_CONTENG")
                current_spa_value = self.GetValue("X6_CONTSPA")

                self.backup_parameters.append([parameter[0], current_branch.strip(), current_pt_value.strip(), current_en_value.strip(), current_spa_value.strip()])

            self.SetValue("X6_FIL", parameter[1]) if parameter[1] else None
            self.SetValue("X6_CONTEUD", parameter[2]) if parameter[2] else None
            self.SetValue("X6_CONTENG", parameter[3]) if parameter[3] else None
            self.SetValue("X6_CONTSPA", parameter[4]) if parameter[4] else None

            self.SetButton(self.language.save)

    def filter_by_tooltip_value(self, element_list, expected_text):
        """
        [Internal]

        Filters elements by finding the tooltip value that is shown when mouseover event
        is triggered.

        :param element_list: The list to be filtered
        :type element_list: Beautiful Soup object list
        :param expected_text: The expected tooltip text.
        :type expected_text: str

        :return: The filtered list of elements.
        :rtype: Beautiful Soup object list

        Usage:

        >>> # Calling the method:
        >>> filtered_elements = self.filter_by_tooltip_value(my_element_list, "Edit")
        """
        return list(filter(lambda x: self.check_element_tooltip(x, expected_text), element_list))

    def check_element_tooltip(self, element, expected_text, contains=False):
        """
        [Internal]

        Internal method of ClickIcon.

        Fires the MouseOver event of an element, checks tooltip text, fires the MouseOut event and
        returns a boolean whether the tooltip has the expected text value or not.

        :param element: The target element object.
        :type element: BeautifulSoup object
        :param expected_text: The text that is expected to exist in button's tooltip.
        :type expected_text: str

        :return: Boolean value whether element has tooltip text or not.
        :rtype: bool

        Usage:

        >>> # Call the method:
        >>> has_add_text = self.check_element_tooltip(button_object, "Add")
        """
        has_text = False

        element_function = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
        self.driver.execute_script(f"$(arguments[0]).mouseover()", element_function())
        time.sleep(1)
        tooltips = self.driver.find_elements(By.CSS_SELECTOR, ".ttooltip")
        if not tooltips:
            tooltips = self.get_current_DOM().select('.ttooltip')
        if tooltips:
            has_text = (len(list(filter(lambda x: expected_text.lower() in x.text.lower(), tooltips))) > 0 if contains else (tooltips[0].text.lower() == expected_text.lower()))
        self.driver.execute_script(f"$(arguments[0]).mouseout()", element_function())
        return has_text

    def WaitFieldValue(self, field, expected_value):
        """
        Wait until field has expected value.
        Recommended for Trigger fields.

        :param field: The desired field.
        :type field: str
        :param expected_value: The expected value.
        :type expected_value: str

        Usage:

        >>> # Calling method:
        >>> self.WaitFieldValue("CN0_DESCRI", "MY DESCRIPTION")
        """
        print(f"Waiting for field {field} value to be: {expected_value}")
        field = re.sub(r"(\:*)(\?*)", "", field).strip()
        self.wait_element(field)

        field_soup = self.get_field(field)

        if not field_soup:
            self.log_error(f"Couldn't find field {field}")

        field_element = lambda: self.driver.find_element_by_xpath(xpath_soup(field_soup))

        success = False
        endtime = time.time() + 60

        while(time.time() < endtime and not success):
            if ((field_element().text.strip() == expected_value) or
                (field_element().get_attribute("value").strip() == expected_value)):
                success = True
            time.sleep(0.5)

    def assert_result(self, expected=True):
        """
        [Internal]

        Asserts the result based on the expected value.

        :param expected: Expected value
        :type expected: bool

        Usage :

        >>> #Calling the method:
        >>> self.assert_result(True)
        """
        self.expected = expected
        log_message = f"{self.log.ident_test()[1]} - "
        self.log.seconds = self.log.set_seconds(self.log.initial_time)

        if self.grid_input or self.grid_check:
            self.log_error("Grid fields were queued for input/check but weren't added/checked. Verify the necessity of a LoadGrid() call.")

        if self.errors:
            
            if self.expected:
                for field_msg in self.errors:
                    log_message += (" " + field_msg)
            else:
                log_message = ""
            
            self.expected = not self.expected

        if self.expected:
            self.message = "" if not self.errors else log_message
            self.log.new_line(True, self.message)
        else:
            self.message = self.language.assert_false_message if not self.errors else log_message
            self.log.new_line(False, self.message)

        self.log.save_file()

        self.errors = []

        print(self.message) if self.message else None
        
        if self.expected:
            self.assertTrue(True, "Passed")
        else:
            self.assertTrue(False, self.message)

        self.message = ""

        
    def ClickCheckBox(self, label_box_name, position=1):
        """
        Clicks on a Label in box on the screen.

        :param label_box_name: The label box name
        :type label_box_name: str
        :param position: position label box on interface
        :type position: int

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickCheckBox("Search",1)
        """
        if position > 0:

            self.wait_element(label_box_name)

            container = self.get_current_container()
            if not container:
                self.log_error("Couldn't locate container.")

            labels_boxs = container.select("span")
            filtered_labels_boxs = list(filter(lambda x: label_box_name.lower() in x.text.lower(), labels_boxs))                
        
            if position <= len(filtered_labels_boxs):
                position -= 1
                label_box = filtered_labels_boxs[position].parent
                if 'tcheckbox' in label_box.get_attribute_list('class'):
                    label_box_element = lambda: self.soup_to_selenium(label_box)                
                    self.click(label_box_element())
                else:
                    self.log_error("Index the Ckeckbox invalid.")                
            else:
                self.log_error("Index the Ckeckbox invalid.")
        else:
            self.log_error("Index the Ckeckbox invalid.")


    def ClickLabel(self, label_name):
        """
        Clicks on a Label on the screen.

        :param label_name: The label name
        :type label_name: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickLabel("Search")
        """
        label = ''
        self.wait_element(label_name)
        endtime = time.time() + self.config.time_out
        while(not label and time.time() < endtime):
            container = self.get_current_container()
            if not container:
                self.log_error("Couldn't locate container.")
                
            labels = container.select("label")
            filtered_labels = list(filter(lambda x: label_name.lower() in x.text.lower(), labels))
            filtered_labels = list(filter(lambda x: EC.element_to_be_clickable((By.XPATH, xpath_soup(x))), filtered_labels))
            label = next(iter(filtered_labels), None)
            
        if not label:
            self.log_error("Couldn't find any labels.")

        label_element = lambda: self.soup_to_selenium(label)
        
        self.scroll_to_element(label_element())
        self.wait_until_to(expected_condition="element_to_be_clickable", element = label, locator = By.XPATH )
        self.set_element_focus(label_element())
        self.wait_until_to(expected_condition="element_to_be_clickable", element = label, locator = By.XPATH )
        self.click(label_element())

    def get_current_container(self):
        """
        [Internal]

        An internal method designed to get the current container.
        Returns the BeautifulSoup object that represents this container or NONE if nothing is found.

        :return: The container object
        :rtype: BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> container = self.get_current_container()
        """
        soup = self.get_current_DOM()
        containers = self.zindex_sort(soup.select(self.containers_selectors["GetCurrentContainer"]), True)
        return next(iter(containers), None)

    def get_all_containers(self):
        """
        [Internal]

        An internal method designed to get all containers.
        Returns the List of BeautifulSoup object that represents this containers or NONE if nothing is found.

        :return: List containers object
        :rtype: List BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> container = self.get_all_containers()
        """
        soup = self.get_current_DOM()
        containers = soup.select(self.containers_selectors["AllContainers"])
        return containers

    def ClickTree(self, treepath, right_click=False, position=1):
        """
        Clicks on TreeView component.

        :param treepath: String that contains the access path for the item separate by ">" .
        :type string: str
        :param right_click: Clicks with the right button of the mouse in the last element of the tree.
        :type string: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickTree("element 1 > element 2 > element 3")
        >>> # Right Click example:
        >>> oHelper.ClickTree("element 1 > element 2 > element 3", right_click=True)
        """
        self.click_tree(treepath, right_click, position)
        
    def click_tree(self, treepath, right_click, position):
        """
        [Internal]
        Take treenode and label to filter and click in the toggler element to expand the TreeView.
        """

        print(f"Clicking on Tree: {treepath}")

        hierarchy=None

        position -= 1

        labels = list(map(str.strip, treepath.split(">")))

        for row, label in enumerate(labels):

            self.wait_blocker()

            last_item = True if row == len(labels)-1 else False

            success = False

            try_counter = 0

            label_filtered = label.lower().strip()

            try:
                if self.tree_base_element and label_filtered == self.tree_base_element[0]:
                    self.scroll_to_element(self.tree_base_element[1])
            except:
                pass

            endtime = time.time() + self.config.time_out

            while((time.time() < endtime) and (try_counter < 3 and not success)):

                tree_node = self.find_tree_bs(label_filtered)

                tree_node_filtered = list(filter(lambda x: "hidden" not in x.parent.parent.parent.parent.attrs['class'], tree_node))

                elements = list(filter(lambda x: label_filtered in x.text.lower().strip() and self.element_is_displayed(x), tree_node_filtered))

                if elements:

                    if position:
                        elements = elements[position] if len(elements) >= position + 1 else next(iter(elements))
                        if hierarchy:
                             elements = elements if elements.attrs['hierarchy'].startswith(hierarchy) and elements.attrs['hierarchy'] != hierarchy else None
                    else:
                        elements = list(filter(lambda x: self.element_is_displayed(x), elements))

                        if hierarchy:
                            elements = list(filter(lambda x: x.attrs['hierarchy'].startswith(hierarchy) and x.attrs['hierarchy'] != hierarchy, elements))

                    for element in elements:
                        if not success:
                            element_class = next(iter(element.select(".toggler, .lastchild, .data")), None)

                            if "data" in element_class.get_attribute_list("class"):
                                element_class =  element_class.select("img, span")

                            for element_class_item in element_class:
                                if not success:

                                    element_click = lambda: self.soup_to_selenium(element_class_item)
                                    try:
                                        if last_item:
                                            start_time = time.time()
                                            self.wait_blocker()
                                            self.scroll_to_element(element_click())
                                            element_click().click()
                                            if self.check_toggler(label_filtered):
                                                success = self.check_hierarchy(label_filtered)
                                                if success and right_click:
                                                    self.send_action(action=self.click, element=element_click, right_click=right_click)
                                            else:
                                                if right_click:
                                                    self.send_action(action=self.click, element=element_click, right_click=right_click)
                                                success = self.clicktree_status_selected(label_filtered)
                                        else:
                                            self.tree_base_element = label_filtered, self.soup_to_selenium(element_class_item)
                                            self.scroll_to_element(element_click())
                                            element_click().click()
                                            success = self.check_hierarchy(label_filtered)

                                        try_counter += 1
                                    except:
                                        pass

                            if not success:
                                try:
                                    element_click = lambda: self.soup_to_selenium(element_class_item.parent)
                                    self.scroll_to_element(element_click())
                                    element_click().click()
                                    success = self.clicktree_status_selected(label_filtered) if last_item and not self.check_toggler(label_filtered) else self.check_hierarchy(label_filtered)
                                except:
                                    pass

            if not last_item:
                treenode_selected = self.treenode_selected(label_filtered)
                hierarchy = treenode_selected.attrs['hierarchy']
                            
        if not success:
            self.log_error(f"Couldn't click on tree element {label}.")

    def find_tree_bs(self, label):
        """
        [Internal]

        Search the label string in current container and return a treenode element.
        """

        tree_node = ""
        
        self.wait_element(term=label, scrap_type=enum.ScrapType.MIXED, optional_term=".ttreenode, .data")

        endtime = time.time() + self.config.time_out

        while (time.time() < endtime and not tree_node):

            container = self.get_current_container()

            tree_node = container.select(".ttreenode")

        if not tree_node:
            self.log_error("Couldn't find tree element.")

        return(tree_node)
    
    def clicktree_status_selected(self, label_filtered, check_expanded=False):
        """
        [Internal]
        """

        treenode_selected = None

        success = True

        container_function = lambda: self.get_current_container() if success else self.get_current_DOM()

        endtime = time.time() + self.config.time_out
        while ((time.time() < endtime) and not treenode_selected):

            container = container_function()

            tr = container.select("tr")

            tr_class = list(filter(lambda x: "class" in x.attrs, tr))

            ttreenode = list(filter(lambda x: "ttreenode" in x.attrs['class'], tr_class))

            treenode_selected = list(filter(lambda x: "selected" in x.attrs['class'], ttreenode))

            if not treenode_selected:
                success = not success

        if not check_expanded:
            if list(filter(lambda x: label_filtered == x.text.lower().strip(), treenode_selected)):
                return True
            else:
                return False
        else:
            tree_selected = next(iter(list(filter(lambda x: label_filtered == x.text.lower().strip(), treenode_selected))), None)
            if tree_selected.find_all_next("span"):
                if "toggler" in next(iter(tree_selected.find_all_next("span"))).attrs['class']:
                    return "expanded" in next(iter(tree_selected.find_all_next("span")), None).attrs['class']
            else:
                return False
    
    def check_toggler(self, label_filtered):
        """
        [Internal]
        """
        tree_selected = self.treenode_selected(label_filtered)

        if tree_selected:
            if tree_selected.find_all_next("span"):
                try:
                    return "toggler" in next(iter(tree_selected.find_all_next("span")), None).attrs['class']
                except:
                    return False
            else:
                return False
        else:
            return False

    def treenode_selected(self, label_filtered):
        """
        [Internal]
        Returns a tree node selected by label
        """

        ttreenode = self.treenode()

        treenode_selected = list(filter(lambda x: "selected" in x.attrs['class'], ttreenode)) 

        return next(iter(list(filter(lambda x: label_filtered == x.text.lower().strip(), treenode_selected))), None)

    def treenode(self):
        """

        :return: treenode bs4 object
        """

        container = self.get_current_container()

        tr = container.select("tr")

        tr_class = list(filter(lambda x: "class" in x.attrs, tr))

        return list(filter(lambda x: "ttreenode" in x.attrs['class'], tr_class))

    def check_hierarchy(self, label):
        """

        :param label:
        :return: True or False
        """

        counter = 1

        node_check = None

        while (counter <= 3 and not node_check):

            treenode_parent_id = self.treenode_selected(label).attrs['id']

            treenode = list(filter(lambda x: self.element_is_displayed(x), self.treenode()))

            node_check = next(iter(list(filter(lambda x: treenode_parent_id == x.attrs['parentid'], treenode))), None)

            counter += 1

        return True if node_check else self.clicktree_status_selected(label, check_expanded=True)

    def GridTree(self, column , tree_path, right_click = False):
        """
        Clicks on Grid TreeView component.

        :param treepath: String that contains the access path for the item separate by ">" .
        :type string: str
        :param right_click: Clicks with the right button of the mouse in the last element of the tree.
        :type string: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.GridTree("element 1 > element 2 > element 3")
        >>> # Right GridTree example:
        >>> oHelper.GridTree("element 1 > element 2 > element 3", right_click=True)
        
        """ 

        endtime = time.time() + self.config.time_out

        tree_list = list(map(str.strip, tree_path.split(">")))
        last_item = tree_list.pop()

        grid = self.get_grid(grid_element = '.tcbrowse')
        column_index = self.search_column_index(grid, column)

        while(time.time() < endtime and tree_list ):

            len_grid_lines = self.expand_treeGrid(column, tree_list[0])

            grid = self.get_grid(grid_element = '.tcbrowse')
            column_index = self.search_column_index(grid, column)

            if self.lenght_grid_lines(grid) > len_grid_lines:
                tree_list.remove(tree_list[0])
            else:
                len_grid_lines = self.expand_treeGrid(column, tree_list[0])
                tree_list.remove(tree_list[0])

        grid = self.get_grid(grid_element = '.tcbrowse')
        column_index = self.search_column_index(grid, column)
        
        div = self.search_grid_by_text(grid, last_item, column_index)
        self.wait_until_to(expected_condition="element_to_be_clickable", element = div, locator = By.XPATH )
        div_s = self.soup_to_selenium(div)
        time.sleep(2)#TODO alterar antes de subir na master
        self.click((div_s), enum.ClickType.SELENIUM , right_click)

    def expand_treeGrid(self, column, item):
        """
        [Internal]
          
        Search for a column and expand the tree
        Returns len of grid lines

        """
        grid = self.get_grid(grid_element = '.tcbrowse')
        column_index = self.search_column_index(grid, column)
        len_grid_lines = self.lenght_grid_lines(grid)
        div = self.search_grid_by_text(grid, item, column_index)
        line = div.parent.parent
        td = next(iter(line.select('td')), None)
        self.expand_tree_grid_line(td)
        self.wait_gridTree(len_grid_lines)
        return len_grid_lines

    def expand_tree_grid_line(self, element_soup):
        """
        [Internal]
        Click on a column and send the ENTER key
        
        """
        self.wait_until_to(expected_condition="element_to_be_clickable", element = element_soup, locator = By.XPATH )
        element_selenium = lambda: self.soup_to_selenium(element_soup)
        element_selenium().click()
        self.wait_blocker()
        self.wait_until_to(expected_condition="element_to_be_clickable", element = element_soup, locator = By.XPATH )
        self.send_keys(element_selenium(), Keys.ENTER)
        
    def wait_gridTree(self, n_lines):
        """
        [Internal]
        Wait until the GridTree line count increases or decreases.

        """
        endtime = time.time() + self.config.time_out
        grid = self.get_grid(grid_element = '.tcbrowse')
        
        while (time.time() < endtime and n_lines == self.lenght_grid_lines(grid) ):
            grid = self.get_grid(grid_element = '.tcbrowse')


    def search_grid_by_text(self, grid, text, column_index):
        """
        [Internal]
        Searches for text in grid columns
        Returns the div containing the text
        
        """
        columns_list = grid.select('td')
        columns_list_filtered = list(filter(lambda x: int(x.attrs['id']) == column_index  ,columns_list))
        div_list = list(map(lambda x: next(iter(x.select('div')), None)  ,columns_list_filtered))
        div = next(iter(list(filter(lambda x: (text.strip() == x.text.strip() and x.parent.parent.attrs['id'] != '0') ,div_list))), None)
        return div
    
    def lenght_grid_lines(self, grid):
        """
        [Internal]
        Returns the leght of grid.
        
        """
        grid_lines = grid.select("tbody tr")
        return len(grid_lines)
                
    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Calling the method
        >>> self.TearDown()
        """

        if self.config.new_log:
            self.execution_flow()

        webdriver_exception = None
        timeout = 1500
        string = "Aguarde... Coletando informacoes de cobertura de codigo."

        if self.config.coverage:
            try:
                self.driver_refresh()
            except WebDriverException as e:
                webdriver_exception = e

            if webdriver_exception:
                message = f"Wasn't possible execute self.driver.refresh() Exception: {next(iter(webdriver_exception.msg.split(':')), None)}"
                print(message)

            if not webdriver_exception and not self.tss:
                self.wait_element(term="[name='cGetUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')
                self.user_screen()
                self.environment_screen()
                self.Finish()
            elif not webdriver_exception:
                self.SetupTSS(self.config.initial_program, self.config.environment )
                self.SetButton(self.language.exit)
                self.SetButton(self.language.yes)

            if (self.search_text(selector=".tsay", text=string) and not webdriver_exception):
                self.WaitProcessing(string, timeout)

        if self.config.num_exec:
            if not self.num_exec.post_exec(self.config.url_set_end_exec):
                self.restart_counter = 3
                self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

        try:
            self.driver.close()
        except Exception as e:
            print(f"Warning tearDown Close {str(e)}")
            
    def containers_filter(self, containers):
        """
        [Internal]
        Filter and remove tsvg class an return a container_filtered
        
        Usage:

        >>> #Calling the method
        >>> containers = self.containers_filter(containers)
        """
        class_remove = "tsvg"
        container_filtered = []

        for container in containers:
            iscorrect = True
            container_class = list(filter(lambda x: "class" in x.attrs, container.select("div")))
            if list(filter(lambda x: class_remove in x.attrs['class'], container_class)):
                iscorrect = False
            if iscorrect:
                container_filtered.append(container)

        return container_filtered

    def filter_label_element(self, label_text, container):
        """
        [Internal]
        Filter and remove a specified character with regex, return only displayed elements if > 1.

        Usage:

        >>> #Calling the method
        >>> elements = self.filter_label_element(label_text, container)
        """
        
        elements = list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"([\s\?:\*\.]+)?"))))
        return list(filter(lambda x: self.element_is_displayed(x), elements)) if len(elements) > 1 else elements

    def filter_is_displayed(self, elements):
        """
        [Internal]
        Returns only displayed elements.

        Usage:

        >>> #Calling the method
        >>> elements = self.filter_is_displayed(elements)
        """
        return list(filter(lambda x: self.element_is_displayed(x), elements))

    def element_is_displayed(self, element):
        """
        [Internal]

        """
        element_selenium = self.soup_to_selenium(element)
        if element_selenium:
            return element_selenium.is_displayed()
        else:
            return False

    def search_text(self, selector, text):
        """
        [Internal]
        Return a element based on text and selector.

        Usage:

        >>> #Calling the method
        >>> element = self.search_text(selector, text)
        """
        container = self.get_current_container()

        if container:
            container_selector = container.select(selector)

            if container_selector:
                self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=10, step=1, main_container="body", check_error = False)

            return next(iter(list(filter(lambda x: text in re.sub(r"\t|\n|\r", " ", x.text), container_selector))), None)

    def pop_dict_itens(self, dict_, element_id):
        """
        [Internal]
        """
        new_dictionary = {k: v  for k, v in dict_.items() if v == element_id}

        for key in list(new_dictionary.keys()):
            dict_.pop(key)

        return dict_

    def get_program_name(self):
        """
        [Internal]
        """
        stack_item_splited = next(iter(map(lambda x: x.filename.split("\\"), filter(lambda x: "TESTSUITE.PY" in x.filename.upper() or "TESTCASE.PY" in x.filename.upper(), inspect.stack()))), None)

        if stack_item_splited:
            get_file_name = next(iter(list(map(lambda x: "TESTSUITE.PY" if "TESTSUITE.PY" in x.upper() else "TESTCASE.PY", stack_item_splited))))

            program_name = next(iter(list(map(lambda x: re.findall(fr"(\w+)(?:{get_file_name})", x.upper()), filter(lambda x: ".PY" in x.upper(), stack_item_splited)))), None)

            if program_name:
                return next(iter(program_name))
            else:
                return None
        else:
            return None

    def GetText(self, string_left="", string_right=""):
        """
        This method returns a string from modal based on the string in the left or right position that you send on parameter.

        If the string_left was filled then the right side content is return.

        If the string_right was filled then the left side content is return.

        If no parameter was filled so the full content is return.

        :param string_left: String of the left side of content.
        :type string_left: str
        :param string_right: String of the right side of content.
        :type string_right: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.GetText(string_left="Left Text", string_right="Right Text")
        >>> oHelper.GetText(string_left="Left Text")
        >>> oHelper.GetText()
        """

        return self.get_text(string_left, string_right)

    def get_text(self, string_left, string_right):
        """

        :param string:
        :return:
        """
        if string_left:
            string = string_left
        else:
            string = string_right

        if string:
            self.wait_element(string)

        container = self.get_current_container()

        labels = container.select('label')

        label = next(iter(list(filter(lambda x: string.lower() in x.text.lower(), labels))))

        return self.get_text_position(label.text, string_left, string_right)

    def get_text_position(self, text="", string_left="", string_right=""):
        """

        :param string_left:
        :param srting_right:
        :return:
        """
        if string_left and string_right:
            return text[len(string_left):text.index(string_right)].strip()
        elif string_left:
            return text[len(string_left):].strip()
        elif string_right:
            return text[:-len(string_right)].strip()
        else:
            return text.strip()

    def wait_smart_erp_environment(self):
        """
        [Internal]
        """
        content = False
        endtime = time.time() + self.config.time_out

        print("Waiting for SmartERP environment assembly")

        while not content and (time.time() < endtime):
            try:
                soup = self.get_current_DOM()

                content = True if next(iter(soup.select("img[src*='resources/images/parametersform.png']")), None) else False
            except AttributeError:
                pass

    def wait_until_to(self, expected_condition = "element_to_be_clickable", element = None, locator = None , timeout=False):
        """
        [Internal]
        
        This method is responsible for encapsulating "wait.until".
        """

        expected_conditions_dictionary = {

            "element_to_be_clickable" : EC.element_to_be_clickable,
            "presence_of_all_elements_located" : EC.presence_of_all_elements_located,
            "visibility_of" : EC.visibility_of,
            "alert_is_present" : EC.alert_is_present,
            "visibility_of_element_located" : EC.visibility_of_element_located
        }

        if not element and expected_condition != "alert_is_present" : self.log_error("Error method wait_until_to() - element is None")

        element = xpath_soup(element) if locator == By.XPATH else element

        if timeout:
            setattr(self.wait, '_timeout', self.config.time_out / 10)

        try:

            if locator:
                self.wait.until(expected_conditions_dictionary[expected_condition]((locator, element)))
            elif element:
                self.wait.until(expected_conditions_dictionary[expected_condition]( element() ))
            elif expected_condition == "alert_is_present":
                self.wait.until(expected_conditions_dictionary[expected_condition]())

        except TimeoutException as e:
            print(f"Warning waint_until_to TimeoutException - Expected Condition: {expected_condition}")
            pass

        if timeout:
            setattr(self.wait, '_timeout', self.config.time_out)


    def CheckHelp(self, text, button, text_help, text_problem, text_solution, verbosity):
        """
        Checks if some help screen is present in the screen at the time and takes an action.

        :param text: Text to be checked.
        :type text: str
        :param text_help: Only the help text will be checked.
        :type text_help: str
        :param text_problem: Only the problem text will be checked.
        :type text_problem: str
        :param text_solution: Only the solution text will be checked.
        :type text_solution: str
        :param button: Button to be clicked.
        :type button: str
        :param verbosity: Check the text with high accuracy.
        :type verbosity: bool

        Usage:
        
        >>> # Calling method to check all window text.
        >>> oHelper.CheckHelp("TK250CADRE Problema: Essa reclamação já foi informada anteriormente. Solução: Informe uma reclamação que ainda não tenha sido cadastrada nessa tabela.", "Fechar")
        >>> # Calling method to check help text only.
        >>> oHelper.CheckHelp(text_help="TK250CADRE", button="Fechar")
        >>> # Calling method to check problem text only.
        >>> oHelper.CheckHelp(text_problem="Problema: Essa reclamação já foi informada anteriormente.", button="Fechar")
        >>> # Calling method to check problem text only.
        >>> oHelper.CheckHelp(text_solution="Solução: Informe uma reclamação que ainda não tenha sido cadastrada nessa tabela.", button="Fechar")
        >>> # Calling the method to check only the problem text with high precision.
        >>> oHelper.CheckHelp(text_problem="Problema: Essa reclamação já foi informada anteriormente.", button="Fechar", verbosity=True)
        """

        text_help_extracted     = ""
        text_problem_extracted  = ""
        text_solution_extracted = ""
        text_extracted = ""

        if not button:
            button = self.get_single_button().text

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not text_extracted):
            
            print(f"Checking Help on screen: {text}")
            # self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=".tsay", check_error=False)
            self.wait_element_timeout(term=text_help, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5,
                                      optional_term=".tsay", check_error=False)
            container = self.get_current_container()
            container_filtered = container.select(".tsay")
            container_text = ''
            for x in range(len(container_filtered)):
                container_text += container_filtered[x].text + ' '

            try:
                text_help_extracted     = container_text[container_text.index(self.language.checkhelp):container_text.index(self.language.checkproblem)]
                text_problem_extracted  = container_text[container_text.index(self.language.checkproblem):container_text.index(self.language.checksolution)]
                text_solution_extracted = container_text[container_text.index(self.language.checksolution):]
            except:
                pass

            if text_help:
                text = text_help
                text_extracted = text_help_extracted
            elif text_problem:
                text = text_problem
                text_extracted = text_problem_extracted
            elif text_solution:
                text = text_solution
                text_extracted = text_solution_extracted
            else:
                text_extracted = container_text

            if text_extracted:
                self.check_text_container(text, text_extracted, container_text, verbosity)
                self.SetButton(button, check_error=False)
                self.wait_element(term=text, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", presence=False, main_container = self.containers_selectors["AllContainers"], check_error=False)

        if not text_extracted:
            self.log_error(f"Couldn't find: '{text}', text on display window is: '{container_text}'")

    def check_text_container(self, text_user, text_extracted, container_text, verbosity):
        if verbosity == False:
            if text_user.replace(" ","") in text_extracted.replace(" ",""):
                print(f"Help on screen Checked: {text_user}")
                return
            else:
                print(f"Couldn't find: '{text_user}', text on display window is: '{container_text}'")
        else:
            if text_user in text_extracted:
                print(f"Help on screen Checked: {text_user}")
                return
            else:
                print(f"Couldn't find: '{text_user}', text on display window is: '{container_text}'")

    def get_single_button(self):
        """
        [Internal]
        """
        container = self.get_current_container()
        buttons = container.select("button")
        button_filtered = next(iter(filter(lambda x: x.text != "", buttons)))
        if not button_filtered:
            self.log_error(f"Couldn't find button")
        return button_filtered

    def ClickMenuPopUpItem(self, label, right_click, position = 1):
        """
        Clicks on MenuPopUp Item based in a text

        :param text: Text in MenuPopUp to be clicked.
        :type text: str
        :param right_click: Button to be clicked.
        :type button: bool
        :param position: index item text
        :type position: int
        
        Usage:

        >>> # Calling the method.
        >>> oHelper.ClickMenuPopUpItem("Label")
        >>> # Calling the method using position.
        >>> oHelper.ClickMenuPopUpItem("Label", position = 2)
        """
        position -= 1

        self.wait_element(term=label, scrap_type=enum.ScrapType.MIXED, main_container="body", optional_term=".tmenupopup")

        label = label.lower().strip()

        endtime = time.time() + self.config.time_out

        tmenupopupitem_filtered = ""

        while(time.time() < endtime and not tmenupopupitem_filtered):

            tmenupopupitem = self.tmenupopupitem()

            if tmenupopupitem:

                tmenupopupitem_displayed = list(filter(lambda x: self.element_is_displayed(x), tmenupopupitem))

                tmenupopupitem_filtered = list(filter(lambda x: x.text.lower().strip() == label, tmenupopupitem_displayed))

                if tmenupopupitem_filtered and len(tmenupopupitem_filtered) -1 >= position:
                    tmenupopupitem_filtered = tmenupopupitem_filtered[position]

        if not tmenupopupitem_filtered:
            self.log_error(f"Couldn't find tmenupopupitem: {label}")

        tmenupopupitem_element = lambda: self.soup_to_selenium(tmenupopupitem_filtered)

        if right_click:
            self.click(tmenupopupitem_element(), right_click=right_click)
        else:
            self.click(tmenupopupitem_element())

    def tmenupopupitem(self):
        """

        :return:
        """

        soup = self.get_current_DOM()

        body = next(iter(soup.select("body")))

        return body.select(".tmenupopupitem")
    
    def get_release(self):
        """
        Gets the current release of the Protheus.

        :return: The current release of the Protheus.
        :type: str
        
        Usage:

        >>> # Calling the method:
        >>> oHelper.get_release()
        >>> # Conditional with method:
        >>> # Situation: Have a input that only appears in release greater than or equal to 12.1.023
        >>> if self.oHelper.get_release() >= '12.1.023':
        >>>     self.oHelper.SetValue('AK1_CODIGO', 'codigoCT001)
        """

        return self.log.release

    def try_click(self, element):
        """
        [Internal]
        """
        try:
            self.soup_to_selenium(element).click()
        except:
            pass
        
    def on_screen_enabled(self, elements):
        """
        [Internal]

        Returns a list if selenium displayed and enabled methods is True.
        """
        if elements:
            is_displayed = list(filter(lambda x: self.element_is_displayed(x), elements))
            
            return list(filter(lambda x: self.soup_to_selenium(x).is_enabled(), is_displayed))

    def update_password(self):
        """
        [Internal]
        Update the password in the Protheus password change request screen
        """
        container = self.get_current_container()
        if container and self.element_exists(term=self.language.change_password, scrap_type=enum.ScrapType.MIXED, main_container=".tmodaldialog", optional_term=".tsay"):
            user_login = self.GetValue(self.language.user_login)
            if user_login == self.config.user or self.config.user.lower() == "admin":
                self.SetValue(self.language.current_password, self.config.password)
                self.SetValue(self.language.nem_password, self.config.password)
                self.SetValue(self.language.confirm_new_password, self.config.password)
                self.SetButton(self.language.finish)
                self.wait_element(self.language.database, main_container=".twindow")
    
    def ClickListBox(self, text):
        """
        Clicks on Item based in a text in a window tlistbox

        :param text: Text in windows to be clicked.
        :type text: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.ClickListBox("text")
        """

        self.wait_element(term='.tlistbox', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container=".tmodaldialog")
        container = self.get_current_container()
        tlist = container.select(".tlistbox")
        list_option = tlist[0].select("option")
        list_option_filtered = list(filter(lambda x: self.element_is_displayed(x), list_option))
        element = next(iter(filter(lambda x: x.text == text, list_option_filtered)), None)
        element_selenium = self.soup_to_selenium(element)
        self.wait_until_to(expected_condition="element_to_be_clickable", element = element, locator = By.XPATH )
        element_selenium.click()

    def ClickImage(self, img_name, double_click=False):
        """
        Clicks in an Image button. They must be used only in case that 'ClickIcon' doesn't  support. 
        :param img_name: Image to be clicked.
        :type img_name: src

        Usage:

        >>> # Call the method:  
        >>> oHelper.ClickImage("img_name")  
        >>> oHelper.ClickImage("img_name",double_click=True)
        """
        self.wait_element(term="div.tbtnbmp > img, div.tbitmap > img", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container =  self.containers_selectors["ClickImage"])

        success = None
        endtime = time.time() + self.config.time_out

        while(time.time() < endtime and not success):

            img_list = self.web_scrap(term="div.tbtnbmp > img, div.tbitmap > img", scrap_type=enum.ScrapType.CSS_SELECTOR , main_container = self.containers_selectors["ClickImage"])
            img_list_filtered = list(filter(lambda x: img_name == self.img_src_filtered(x),img_list))
            img_soup = next(iter(img_list_filtered), None)

            if img_soup:
                    element_selenium = lambda: self.soup_to_selenium(img_soup)
                    self.set_element_focus(element_selenium())
                    self.wait_until_to(expected_condition="element_to_be_clickable", element = img_soup, locator = By.XPATH, timeout=True)
                    if double_click:
                        success = self.double_click(element_selenium())
                    else:
                        success = self.click(element_selenium())
        return success

    def img_src_filtered(self, img_soup):
        
        """
        [Internal]
        Return an image source filtered.
        """

        img_src_string = self.soup_to_selenium(img_soup).get_attribute("src")
        return next(iter(re.findall('[\w\_\-]+\.', img_src_string)), None).replace('.','')

    def try_element_to_be_clickable(self, element):
        """
        Try excpected condition element_to_be_clickable by XPATH or ID 
        """
        try:
            self.wait_until_to(expected_condition="element_to_be_clickable", element = element, locator = By.XPATH)
        except:
            if 'id' in element.find_parent('div').attrs:
                self.wait_until_to(expected_condition="element_to_be_clickable", element = element.find_previous("div").attrs['id'], locator = By.ID )
            else:
                pass

    def open_csv(self, csv_file, delimiter, column, header, filter_column, filter_value):
        """
        Returns a dictionary when the file has a header in another way returns a list
        The folder must be entered in the CSVPath parameter in the config.json. Ex:

        >>> config.json
        >>> "CsvPath" : "C:\\temp"

        :param csv_file: .csv file name
        :type csv_file: str
        :param delimiter: Delimiter option such like ';' or ',' or '|'
        :type delimiter: str
        :param column: To files with Header is possible return only a column by header name or Int value for no header files 
        :type column: str
        :param header: Indicate with the file contains a Header or not default is Header None
        :type header: bool
        :param filter_column: Is possible to filter a specific value by column and value content, if value is int starts with number 1
        :type filter_column: str or int
        :param filter_value: Value used in pair with filter_column parameter
        :type filter_value: str

        >>> # Call the method:
        >>> file_csv = test_helper.OpenCSV(delimiter=";", csv_file="no_header.csv")

        >>> file_csv_no_header_column = self.oHelper.OpenCSV(column=0, delimiter=";", csv_file="no_header_column.csv")

        >>> file_csv_column = self.oHelper.OpenCSV(column='CAMPO', delimiter=";", csv_file="header_column.csv", header=True)

        >>> file_csv_pipe = self.oHelper.OpenCSV(delimiter="|", csv_file="pipe_no_header.csv")

        >>> file_csv_header = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True)

        >>> file_csv_header_column = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True)

        >>> file_csv_header_pipe = self.oHelper.OpenCSV(delimiter="|", csv_file="pipe_header.csv", header=True)

        >>> file_csv_header_filter = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True, filter_column='CAMPO', filter_value='A00_FILIAL')

        >>> file_csv _no_header_filter = self.oHelper.OpenCSV(delimiter=";", csv_file="no_header.csv", filter_column=0, filter_value='A00_FILIAL')
        """

        has_header = 'infer' if header else None
        
        if self.config.csv_path:
            data = pd.read_csv(f"{self.config.csv_path}\\{csv_file}", sep=delimiter, encoding='latin-1', error_bad_lines=False, header=has_header, index_col=False)
            df = pd.DataFrame(data)
            df = df.dropna(axis=1, how='all')

            filter_column_user = filter_column
            
            if filter_column and filter_value:
                if isinstance(filter_column, int):
                    filter_column_user = filter_column - 1
                df = self.filter_dataframe(df, filter_column_user, filter_value)
            elif (filter_column and not filter_value) or (filter_value and not filter_column):
                print('WARNING: filter_column and filter_value is necessary to filter rows by column content. Data wasn\'t filtered') 
                
            return self.return_data(df, has_header, column)
        else:
            self.log_error("CSV Path wasn't found, please check 'CSVPath' key in the config.json.")

    def filter_dataframe(self, df, column, value):
        """
        [Internal]
        """
        return df[df[column] == value]

    def return_data(self, df, has_header, column):
        """
        [Internal]
        """
        if has_header == 'infer':
            return df[column].to_dict() if column else df.to_dict()
        else:
            return df[column].values.tolist() if isinstance(column, int) else df.values.tolist()

    def open_url_coverage(self, url='', initial_program='', environment=''):
        """
        [Internal]
        Open a webapp url with line parameters
        :param url: server url.
        :type url: str
        :param initial_program: program name.
        :type initial_program: str
        :param environment: environment server.
        :type environment: str
        Usage:
        >>> # Call the method:  
        >>> self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)
        """
        self.driver.get(f"{url}/?StartProg=CASIGAADV&A={initial_program}&Env={environment}") 
        
    def returns_printable_string(self, string):
        """
        Returns a string only is printable characters
        [Internal]
        :param string: string value
        :type string: str
        """
        return "".join(list(filter(lambda x: x.isprintable(), string)))

    def get_config_value(self, json_key):
        """

        :param json_key: Json Key in config.json
        :type json_key: str
        :return: Json Key item in config.json
        """
        json_key = json_key.lower()

        config_dict = dict((k.lower(), v) for k, v in self.config.json_data.items())

        if list(filter(lambda x: json_key in x, config_dict.keys())):
            return config_dict[json_key]
        else:
            self.log_error("Doesn't contain that key in json object")

    def send_action(self, action = None, element = None, value = None, right_click=False, ratio=None):
        """

        Sends an action to element and compare it object state change.
    
        :param action: selenium function as a reference like click, actionchains or send_keys.
        :param element: selenium element as a reference
        :param value: send keys value
        :param right_click: True if you want a right click
        :return: True if there was a change in the object
        """

        soup_before_event = self.get_current_DOM()

        soup_after_event = soup_before_event

        soup_select = None

        success = False

        container_id = self.container_id()

        counter = 1

        endtime = time.time() + self.config.time_out

        try:

            while ((time.time() < endtime and not success)):

                print("CLICK SEND_ACTION!!!")
                
                self.wait_blocker()

                self.send_action_click(action, element, value, right_click)

                timeout_tries = time.time() + self.config.time_out / 2

                while ((time.time() < timeout_tries and not success)):

                    if soup_select:
                        soup_after_event = soup_select
                    elif soup_select == []:
                        soup_after_event = soup_before_event
                    else:
                        soup_after_event = self.get_current_DOM()

                    if ratio:

                        if counter == 3:
                            self.search_for_errors()

                        current_ratio, success = self.soup_compare_ratio(soup_before_event, soup_after_event, ratio)
                        print(f"Current Ratio: {round(current_ratio, 2)}% - Target Ratio: {ratio}%")
                        if soup_before_event != soup_after_event and not success:
                            if container_id and (self.container_id() == container_id) and counter == 3:
                                current_ratio, success = self.soup_compare_ratio(soup_before_event, soup_after_event, ratio=0.004)
                                print(f"Current Ratio: {current_ratio}% - Target Ratio: 0.004%")

                        counter += 1

                        if counter > 3:
                            counter = 1

                    elif soup_before_event != soup_after_event:
                        success = True

        except Exception as e:
            if self.config.smart_test or self.config.debug_log:
                print(f"Warning Exception send_action {str(e)}")
            return False

        if self.config.smart_test or self.config.debug_log:
            print(f"send_action method result = {soup_before_event != soup_after_event}")
        return soup_before_event != soup_after_event

    def get_soup_select(self, selector):
        """
        Get a soup select object.
    
        :param selector: Css selector
        :return: Return a soup select object
        """
        soup =  self.get_current_DOM()

        return soup.select(selector)

    def check_mot_exec(self):
        """
        Check MotExec key content
        
        :return:
        """
        m = re.match(pattern='((^TIR$)|(^TIR_))', string=self.config.issue)
        if m:
            self.driver.close()
            self.assertTrue(False, f'Current "MotExec" are using a reserved word: "{m.group(0)}", please check "config.json" key and execute again.')

    def soup_compare_ratio(self, soup_before=None, soup_after=None, ratio=9.0):
        """

        :return:
        """

        m = SequenceMatcher(None, str(soup_before), str(soup_after))

        current_ratio = m.quick_ratio()

        current_ratio_convert = (current_ratio * 100 - 100) * -1

        return current_ratio_convert, (current_ratio_convert >= ratio)

    def container_id(self):
        """

        :return:
        """

        container = self.get_current_container()

        if container  and 'id' in container.attrs:
            return container.attrs['id']
        else:
            return []

    def send_action_click(self, action, element, value, right_click):
        """

        :param action:
        :param element:
        :param value:
        :param right_click:
        :return:
        """

        if right_click:
            soup_select = self.get_soup_select(".tmenupopupitem")
            if not soup_select:
                action(element(), right_click=right_click)
        elif value:
            action(element(), value)
        elif element:
            self.set_element_focus(element())
            action(element())
        elif action:
            action()
