import re
import time
import pandas as pd
import inspect
import os
import random
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
from tir.technologies.core.base import Base

class WebappInternal(Base):
    """
    Internal implementation of Protheus Webapp class.

    This class contains all the methods defined to run Selenium Interface Tests on Protheus Webapp.

    Internal methods should have the **[Internal]** tag and should not be accessible to the user.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str

    Usage:

    >>> # Inside __init__ method in Webapp class of main.py
    >>> def __init__(self, config_path):
    >>>     self.__webapp = WebappInternal()
    """
    def __init__(self, config_path=""):
        """
        Definition of each global variable:

        base_container: A variable to contain the layer element to be used on all methods.

        grid_check: List with fields from a grid that must be checked in the next LoadGrid call.

        grid_counters: A global counter of grids' last row to be filled.

        grid_input: List with fields from a grid that must be filled in the next LoadGrid call.

        used_ids: List of element ids already captured by a label search.
        """
        super().__init__(config_path)


        self.base_container = ".tmodaldialog"

        self.grid_check = []
        self.grid_counters = {}
        self.grid_input = []
        self.down_loop_grid = False

        self.used_ids = []

        self.parameters = []
        self.backup_parameters = []

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
        if save_input:
            self.config.initialprog = initial_program
            self.config.date = date
            self.config.group = group
            self.config.branch = branch
            self.config.module = module

        if not self.config.valid_language:
            self.config.language = self.get_language()
            self.language = LanguagePack(self.config.language)

        if not self.config.skip_environment:
            self.program_screen(initial_program)

        self.user_screen()
        self.environment_screen()

        while(not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")):
            self.close_coin_screen()
            self.close_modal()

        if save_input:
            self.set_log_info()

    def program_screen(self, initial_program="", environment=""):
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
        self.wait_element(term='#inputStartProg', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        self.wait_element(term='#inputEnv', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        soup = self.get_current_DOM()

        print("Filling Initial Program")
        start_prog_element = next(iter(soup.select("#inputStartProg")), None)
        if start_prog_element is None:
            self.log_error("Couldn't find Initial Program input element.")
        start_prog = lambda: self.driver.find_element_by_xpath(xpath_soup(start_prog_element))
        start_prog().clear()
        self.send_keys(start_prog(), initial_program)

        print("Filling Environment")
        env_element = next(iter(soup.select("#inputEnv")), None)
        if env_element is None:
            self.log_error("Couldn't find Environment input element.")
        env = lambda: self.driver.find_element_by_xpath(xpath_soup(env_element))
        env().clear()
        self.send_keys(env(), self.config.environment)

        button = self.driver.find_element(By.CSS_SELECTOR, ".button-ok")
        self.click(button)

    def user_screen(self):
        """
        [Internal]

        Fills the user login screen of Protheus with the user and password located on config.json.

        Usage:

        >>> # Calling the method
        >>> self.user_screen()
        """
        self.wait_element(term="[name='cGetUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')

        soup = self.get_current_DOM()

        print("Filling User")
        user_element = next(iter(soup.select("[name='cGetUser']")), None)
        if user_element is None:
            self.log_error("Couldn't find User input element.")

        user = lambda: self.driver.find_element_by_xpath(xpath_soup(user_element))
        self.set_element_focus(user())
        self.double_click(user())
        self.send_keys(user(), Keys.HOME)
        self.send_keys(user(), self.config.user)
        self.send_keys(user(), Keys.ENTER)

        # loop_control = True

        # while(loop_control):
        print("Filling Password")
        password_element = next(iter(soup.select("[name='cGetPsw']")), None)
        if password_element is None:
            self.log_error("Couldn't find User input element.")

        password = lambda: self.driver.find_element_by_xpath(xpath_soup(password_element.find_parent()))
        self.set_element_focus(password())
        self.click(password())
        self.send_keys(password(), Keys.HOME)
        self.send_keys(password(), self.config.password)
        self.send_keys(password(), Keys.ENTER)

        button_element = next(iter(list(filter(lambda x: self.language.enter in x.text, soup.select("button")))), None)
        if button_element is None:
            self.log_error("Couldn't find Enter button.")

        button = lambda: self.driver.find_element_by_xpath(xpath_soup(button_element))
        self.click(button())

            # self.wait_element_timeout(term=self.language.password, scrap_type=enum.ScrapType.MIXED, timeout=10, step=1, presence=False, optional_term="label", main_container="body")
            # loop_control = self.element_exists(term=self.language.password, scrap_type=enum.ScrapType.MIXED, optional_term="label", main_container="body")

        # self.wait_element(term=self.language.user, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="label", main_container="body")

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
            container = None
        else:
            label = self.language.enter
            container = ".twindow"

        self.wait_element(self.language.database, main_container=container)

        print("Filling Date")
        base_date = next(iter(self.web_scrap(term="[name='dDataBase'] input, [name='__dInfoData'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)), None)
        if base_date is None:
            self.log_error("Couldn't find Date input element.")
        date = lambda: self.driver.find_element_by_xpath(xpath_soup(base_date))
        self.double_click(date())
        self.send_keys(date(), Keys.HOME)
        self.send_keys(date(), self.config.date)

        print("Filling Group")
        group_element = next(iter(self.web_scrap(term="[name='cGroup'] input, [name='__cGroup'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)), None)
        if group_element is None:
            self.log_error("Couldn't find Group input element.")
        group = lambda: self.driver.find_element_by_xpath(xpath_soup(group_element))
        self.double_click(group())
        self.send_keys(group(), Keys.HOME)
        self.send_keys(group(), self.config.group)

        print("Filling Branch")
        branch_element = next(iter(self.web_scrap(term="[name='cFil'] input, [name='__cFil'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)), None)
        if branch_element is None:
            self.log_error("Couldn't find Branch input element.")
        branch = lambda: self.driver.find_element_by_xpath(xpath_soup(branch_element))
        self.double_click(branch())
        self.send_keys(branch(), Keys.HOME)
        self.send_keys(branch(), self.config.branch)

        print("Filling Environment")
        environment_element = next(iter(self.web_scrap(term="[name='cAmb'] input", scrap_type=enum.ScrapType.CSS_SELECTOR, label=True, main_container=container)), None)
        if environment_element is None:
            self.log_error("Couldn't find Module input element.")
        env = lambda: self.driver.find_element_by_xpath(xpath_soup(environment_element))
        if ("disabled" not in environment_element.parent.attrs["class"] and env().is_enabled()):
            self.double_click(env())
            self.send_keys(env(), Keys.HOME)
            self.send_keys(env(), self.config.module)

        buttons = self.filter_displayed_elements(self.web_scrap(label, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container=container), True)
        button_element = next(iter(buttons), None)
        if button_element is None:
            self.log_error(f"Couldn't find {label} button.")
        button = lambda: self.driver.find_element_by_xpath(xpath_soup(button_element))
        self.click(button())

        self.wait_element(term=self.language.database, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="input", main_container=container)

    def ChangeEnvironment(self):
        """
        Clicks on the change environment area of Protheus Webapp and
        fills the environment screen with the values passed on the Setup method.

        Usage:

        >>> # Calling the method:
        >>> oHelper.ChangeEnvironment()
        """
        element = next(iter(self.web_scrap(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container="body")), None)
        if element:
            self.click(self.driver.find_element_by_xpath(xpath_soup(element)))
            self.environment_screen(True)

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
        if modals and self.element_exists(term=".tmodaldialog .tbrowsebutton", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"):
            buttons = modals[0].select(".tbrowsebutton")
            if buttons:
                close_button = next(iter(list(filter(lambda x: x.text == self.language.close, buttons))))
                time.sleep(0.5)
                selenium_close_button = lambda: self.driver.find_element_by_xpath(xpath_soup(close_button))
                if close_button:
                    try:
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(close_button))))
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
        if modals and self.element_exists(term="Moedas", scrap_type=enum.ScrapType.MIXED, optional_term="label", main_container="body"):
            self.SetButton(self.language.confirm)

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
        self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tmodaldialog")))

        soup = self.get_current_DOM()
        labels = list(soup.select(".tmodaldialog .tpanel .tsay"))

        release_element = next(iter(filter(lambda x: x.text.startswith("Release"), labels)), None)
        database_element = next(iter(filter(lambda x: x.text.startswith("Top DataBase"), labels)), None)

        if release_element:
            release = release_element.text.split(":")[1].strip()
            self.log.release = release
            self.log.version = release.split(".")[0]

        if database_element:
            self.log.database = database_element.text.split(":")[1].strip()

        self.SetButton(self.language.close)

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
        print(f"Setting program: {program}")
        self.wait_element(term="[name=cGet]", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        soup = self.get_current_DOM()
        tget = next(iter(soup.select("[name=cGet]")), None)
        if tget:
            tget_img = next(iter(tget.select("img")), None)

            if tget_img is None:
                self.log_error("Couldn't find Program field.")

            s_tget = lambda : self.driver.find_element_by_xpath(xpath_soup(tget))
            s_tget_img = lambda : self.driver.find_element_by_xpath(xpath_soup(tget_img))

            self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(tget))))
            self.double_click(s_tget())
            self.set_element_focus(s_tget())
            self.send_keys(s_tget(), Keys.BACK_SPACE)
            self.send_keys(s_tget(), program)
            self.click(s_tget_img())

    def SearchBrowse(self, term, key=None, identifier=None, index=False):
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
        """
        print(f"Searching: {term}")
        if index and isinstance(key, int):
            key -= 1
        browse_elements = self.get_search_browse_elements(identifier)
        if key:
            self.search_browse_key(key, browse_elements, index)
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
        self.wait_element_timeout(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        soup = self.get_current_DOM()
        search_index = self.get_panel_name_index(panel_name) if panel_name else 0
        containers = self.zindex_sort(soup.select(".tmodaldialog"), reverse=True)
        container = next(iter(containers), None)
        if not container:
            self.log_error("Couldn't find container of element.")

        try:
            browse_div = container.select("[style*='fwskin_seekbar_ico']")[search_index].find_parent().find_parent()
        except IndexError:
            self.log_error("Search element wasn't found.")
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
        if index and not isinstance(search_key, int):
            self.log_error("If index parameter is True, key must be a number!")

        sel_browse_key = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[0]))
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(search_elements[0]))))
        self.set_element_focus(sel_browse_key())
        self.click(sel_browse_key())

        soup = self.get_current_DOM()
        if not index:
            tradiobuttonitens = soup.select(".tradiobuttonitem")
            tradio_index = 0
            tradiobutton_texts = list(map(lambda x: x.text[0:-3].strip() if re.match(r"\.\.\.$", x.text) else x.text.strip(), tradiobuttonitens))
            tradiobutton_text = next(iter(list(filter(lambda x: search_key in x, tradiobutton_texts))), None)
            if not tradiobutton_text:
                tradiobutton_text = self.filter_by_tooltip_value(tradiobuttonitens, search_key)
                if not tradiobutton_text:
                    self.log_error(f"Key not found: {search_key}")

            tradio_index = tradiobutton_texts.index(tradiobutton_text)

            tradiobuttonitem = tradiobuttonitens[tradio_index]
            trb_input = next(iter(tradiobuttonitem.select("input")), None)
            if not trb_input:
                self.log_error("Couldn't find key input.")
        else:
            tradiobuttonitens = soup.select(".tradiobuttonitem input")
            if len(tradiobuttonitens) < search_key + 1:
                self.log_error("Key index out of range.")
            trb_input = tradiobuttonitens[search_key]

        sel_input = lambda: self.driver.find_element_by_xpath(xpath_soup(trb_input))
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(trb_input))))
        self.click(sel_input())


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
        sel_browse_input = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[1]))
        sel_browse_icon = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[2]))

        current_value = self.get_element_value(sel_browse_input())

        while (current_value.rstrip() != term.strip()):
            self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(search_elements[2]))))
            self.click(sel_browse_input())
            self.set_element_focus(sel_browse_input())
            self.send_keys(sel_browse_input(), Keys.DELETE)
            sel_browse_input().clear()
            self.set_element_focus(sel_browse_input())
            sel_browse_input().send_keys(term.strip())
            current_value = self.get_element_value(sel_browse_input())
        self.send_keys(sel_browse_input(), Keys.ENTER)

        self.double_click(sel_browse_icon())
        return True

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

    def SetValue(self, field, value, grid=False, grid_number=1, ignore_case=True, row=None):
        """
        Sets value of an input element.

        :param field: The field name or label to receive the value
        :type field: str
        :param value: The value to be inputted on the element.
        :type value: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param grid_number: Grid number of which grid should be inputted when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param ignore_case: Boolean if case should be ignored or not. - **Default:** True
        :type ignore_case: bool
        :param row: Row number that will be filled 
        :type row: int

        Usage:

        >>> # Calling method to input value on a field:
        >>> oHelper.SetValue("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is a grid:
        >>> oHelper.SetValue("Client", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is on the second grid of the screen:
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2)
        >>> oHelper.LoadGrid()
        """
        if grid:
            self.input_grid_appender(field, value, grid_number - 1, row=row)
        elif isinstance(value, bool):
            self.click_check_radio_button(field, value)
        else:
            self.input_value(field, value, ignore_case)

    def input_value(self, field, value, ignore_case=True):
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

        :returns: True if succeeded, False if it failed.
        :rtype: bool

        Usage:

        >>> # Calling the method
        >>> self.input_value("A1_COD", "000001")
        """

        field = re.sub(r"(\:*)(\?*)", "", field).strip()

        self.wait_element(field)
        success = False
        endtime = time.time() + 60

        while(time.time() < endtime and not success):
            unmasked_value = self.remove_mask(value)

            print(f"Looking for element: {field}")

            if field.lower() == self.language.From.lower():
                element = self.get_field("cDeCond", name_attr=True)
            elif field.lower() == self.language.To.lower():
                element = self.get_field("cAteCond", name_attr=True)
            else:
                element = self.get_field(field)

            if not element:
                continue

            input_field = lambda: self.driver.find_element_by_xpath(xpath_soup(element))

            valtype = "C"
            main_value = unmasked_value if value != unmasked_value and self.check_mask(input_field()) else value

            interface_value = self.get_web_value(input_field())
            current_value = interface_value.strip()
            interface_value_size = len(interface_value)
            user_value_size = len(value)

            if not input_field().is_enabled() or "disabled" in element.attrs:
                self.log_error(self.create_message(['', field],enum.MessageType.DISABLED))

            if element.name == "input":
                valtype = element.attrs["valuetype"]

            self.scroll_to_element(input_field())

            try:
                #Action for Combobox elements
                if ((hasattr(element, "attrs") and "class" in element.attrs and "tcombobox" in element.attrs["class"]) or
                (hasattr(element.find_parent(), "attrs") and "class" in element.find_parent().attrs and "tcombobox" in element.find_parent().attrs["class"])):
                    #self.wait.until(EC.visibility_of(input_field()))
                    self.set_element_focus(input_field())
                    self.select_combo(element, main_value)
                    current_value = self.get_web_value(input_field()).strip()
                #Action for Input elements
                else:
                    self.wait.until(EC.visibility_of(input_field()))
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(element))))
                    self.double_click(input_field())

                    #if Character input
                    if valtype != 'N':
                        self.set_element_focus(input_field())
                        self.send_keys(input_field(), Keys.DELETE)
                        self.send_keys(input_field(), Keys.HOME)
                        self.send_keys(input_field(), main_value)
                    #if Number input
                    else:
                        tries = 0
                        while(tries < 3):
                            self.set_element_focus(input_field())
                            self.send_keys(input_field(), Keys.DELETE)
                            self.send_keys(input_field(), Keys.BACK_SPACE)
                            self.click(input_field())
                            input_field().send_keys(main_value)
                            current_number_value = self.get_web_value(input_field())
                            if self.remove_mask(current_number_value).strip() == main_value:
                                break
                            tries+=1

                    if user_value_size < interface_value_size:
                        self.send_keys(input_field(), Keys.ENTER)

                    if self.check_mask(input_field()):
                        current_value = self.remove_mask(self.get_web_value(input_field()).strip())
                        if re.findall(r"\s", current_value):
                            current_value = re.sub(r"\s", "", current_value)
                    else:
                        current_value = self.get_web_value(input_field()).strip()
                    
                    if current_value != "":
                        print(f"Current field value: {current_value}")

                if ((hasattr(element, "attrs") and "class" in element.attrs and "tcombobox" in element.attrs["class"]) or
                (hasattr(element.find_parent(), "attrs") and "class" in element.find_parent().attrs and "tcombobox" in element.find_parent().attrs["class"])):
                    current_value = current_value[0:len(str(value))]

                if re.match(r"^●+$", current_value):
                    success = len(current_value) == len(str(value).strip())
                elif ignore_case:
                    success = current_value.lower() == main_value.lower()
                else:
                    success = current_value == main_value
            except:
                continue

        if not success:
            self.log_error(f"Could not input value {value} in field {field}")

    def get_field(self, field, name_attr=False):
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
        endtime = time.time() + 60
        element =  None
        while(time.time() < endtime and element is None):
            if re.match(r"\w+(_)", field) or name_attr:
                element = next(iter(self.web_scrap(f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)), None)
            else:
                element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True)), None)

        if element:
            element_children = next((x for x in element.contents if x.name in ["input", "select"]), None)
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
        elif element.tag_name == "select":
            current_select = int(element.get_attribute('value'))
            selected_element = element.find_elements(By.CSS_SELECTOR, "option")[current_select]
            web_value = selected_element.text
        else:
            web_value = element.get_attribute("value")

        return web_value

    def CheckResult(self, field, user_value, grid=False, line=1, grid_number=1):
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
        """
        if grid:
            self.check_grid_appender(line - 1, field, user_value, grid_number - 1)
        elif isinstance(user_value, bool):
            current_value = self.result_checkbox(field, user_value)
            self.log_result(field, user_value, current_value)
        else:
            field = re.sub(r"(\:*)(\?*)", "", field).strip()

            self.wait_element(field)
            element = self.get_field(field)
            if not element:
                self.log_error(f"Couldn't find element: {field}")

            field_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))

            endtime = time.time() + 10
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
        if not grid:
            element = self.get_field(field)

            selenium_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))

            value = self.get_web_value(selenium_element())
        else:
            field_array = [line-1, field, "", grid_number-1]
            x3_dictionaries = self.create_x3_tuple()
            value = self.check_grid(field_array, x3_dictionaries, get_value=True)

        return value

    def restart(self):
        """
        [Internal]

        Restarts the Protheus Webapp and fills the initial screens.

        Usage:

        >>> # Calling the method:
        >>> self.restart()
        """
        self.driver.refresh()
        try:
            self.driver.switch_to_alert().accept()
        except:
            pass

        if not self.config.skip_environment:
            self.program_screen(self.config.initialprog)
        self.user_screen()
        self.environment_screen()

        while(not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")):
            self.close_modal()

        if ">" in self.config.routine:
            self.SetLateralMenu(self.config.routine, save_input=False)
        else:
            self.set_program(self.config.routine)

    def LogOff(self):
        """
        Logs out of the Protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.LogOff()
        """
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
        self.SetButton(self.language.finish)

    def web_scrap(self, term, scrap_type=enum.ScrapType.TEXT, optional_term=None, label=False, main_container=None):
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
            endtime = time.time() + 60
            container =  None
            while(time.time() < endtime and container is None):
                soup = self.get_current_DOM()

                self.search_for_errors(soup)

                if self.config.log_file:
                    with open(f"{term + str(scrap_type) + str(optional_term) + str(label) + str(main_container) + str(random.randint(1, 101)) }.txt", "w") as text_file:
                        text_file.write(f" HTML CONTENT: {str(soup)}")

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                containers = self.zindex_sort(soup.select(container_selector), reverse=True)

                container = next(iter(containers), None)

            if container is None:
                raise Exception("Couldn't find container")

            if (scrap_type == enum.ScrapType.TEXT):
                if label:
                    return self.find_label_element(term, container)
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

    def search_for_errors(self,soup):
        """
        [Internal]

        Searches for errors and alerts in the screen.

        :param soup: Beautiful Soup object to be checked.
        :type soup: Beautiful Soup object

        Usage:

        >>> # Calling the method:
        >>> self.search_for_errors(soup)
        """
        message = ""
        top_layer = next(iter(self.zindex_sort(soup.select(".tmodaldialog, .ui-dialog"), True)), None)
        if not top_layer:
            return None

        icon_alert = next(iter(top_layer.select("img[src*='fwskin_info_ico.png']")), None)
        icon_error_log = next(iter(top_layer.select("img[src*='openclosing.png']")), None)
        critical_box = next(iter(top_layer.select(".tmessagebox")), None)
        if not icon_alert and not icon_error_log and not critical_box:
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

        elif critical_box:
            error_paragraphs = critical_box.text.split("\n\n")
            error_message = f"Error Log: {error_paragraphs[0]}" if len(error_paragraphs) > 2 else "Error Log: Server down."
            message = error_message.replace("\n", " ")

        self.driver.save_screenshot( self.get_function_from_stack() +".png")
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

    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container=".tmodaldialog,.ui-dialog"):
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
        if self.config.debug_log:
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

                self.search_for_errors(soup)

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container
                containers = self.zindex_sort(soup.select(container_selector), reverse=True)
                container = next(iter(containers), None)
                if not container:
                    return False

                try:
                    container_element = self.driver.find_element_by_xpath(xpath_soup(container))
                except:
                    return False
            else:
                container_element = self.driver

            element_list = container_element.find_elements(by, selector)
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)
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
        for menuitem in menu_itens:
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".tmenu")))
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tmenu .tmenuitem")))
            self.wait_element(term=menuitem, scrap_type=enum.ScrapType.MIXED, optional_term=".tmenuitem", main_container="body")
            subMenuElements = menu.select(".tmenuitem")
            endTime =   time.time() + 90
            while not subMenuElements or len(subMenuElements) < self.children_element_count(f"#{child.attrs['id']}", ".tmenuitem"):
                menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
                subMenuElements = menu.select(".tmenuitem")
                if time.time() > endTime and (not subMenuElements or len(subMenuElements) < self.children_element_count(".tmenu", ".tmenuitem")):
                    self.log_error(f"Couldn't find menu item: {menuitem}")
            submenu = ""
            child = list(filter(lambda x: x.text.startswith(menuitem), subMenuElements))[0]
            submenu = lambda: self.driver.find_element_by_xpath(xpath_soup(child))
            if subMenuElements and submenu():
                self.scroll_to_element(submenu())
                ActionChains(self.driver).move_to_element(submenu()).click().perform()
                if count < len(menu_itens) - 1:
                    self.wait_element(term=menu_itens[count], scrap_type=enum.ScrapType.MIXED, optional_term=".tmenuitem", main_container="body")
                    menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
            else:
                self.log_error(f"Error - Menu Item does not exist: {menuitem}")
            count+=1

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

    def SetButton(self, button, sub_item=""):
        """
        Method that clicks on a button on the screen.

        :param button: Button to be clicked.
        :type button: str
        :param sub_item: Sub item to be clicked inside the first button. - **Default:** "" (empty string)
        :type sub_item: str

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> oHelper.SetButton("Add")
        >>> #-------------------------------------------------
        >>> # Calling the method to click on a sub item inside a button.
        >>> oHelper.SetButton("Other Actions", "Process")
        """
        print(f"Clicking on {button}")
        try:
            soup_element  = ""
            if (button.lower() == "x"):
                self.wait_element(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button", timeout=10, step=0.1)

            layers = 0
            if button == self.language.confirm:
                layers = len(self.driver.find_elements(By.CSS_SELECTOR, ".tmodaldialog"))

            success = False
            endtime = time.time() + 10
            while(time.time() < endtime and not soup_element):
                soup_objects = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button")

                if soup_objects:
                    soup_element = lambda : self.driver.find_element_by_xpath(xpath_soup(soup_objects[0]))

            if (button.lower() == "x" and self.element_exists(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)):
                element = self.driver.find_element(By.CSS_SELECTOR, ".ui-button.ui-dialog-titlebar-close[title='Close']")
                self.scroll_to_element(element)
                time.sleep(2)
                self.click(element)

            if not soup_element:
                soup_objects = self.web_scrap(term=self.language.other_actions, scrap_type=enum.ScrapType.MIXED, optional_term="button")

                if soup_objects:
                    soup_element = lambda : self.driver.find_element_by_xpath(xpath_soup(soup_objects[0]))
                else:
                    self.log_error("Couldn't find element")

                self.scroll_to_element(soup_element())#posiciona o scroll baseado na height do elemento a ser clicado.
                self.click(soup_element())

                success = self.click_sub_menu(button if button.lower() != self.language.other_actions.lower() else sub_item)
                if success:
                    return
                else:
                    self.log_error(f"Element {button} not found!")

            if soup_element:
                if button in self.language.no_actions:
                    self.idwizard = []

                self.scroll_to_element(soup_element())#posiciona o scroll baseado na height do elemento a ser clicado.
                self.click(soup_element())

            # if button != self.language.other_actions:

            if sub_item:
                soup_objects = self.web_scrap(term=sub_item, scrap_type=enum.ScrapType.MIXED, optional_term=".tmenupopupitem", main_container="body")

                if soup_objects:
                    soup_element = lambda : self.driver.find_element_by_xpath(xpath_soup(soup_objects[0]))
                else:
                    self.log_error("Couldn't find element")

                self.click(soup_element())

            if button == self.language.save and soup_objects[0].parent.attrs["id"] in self.get_enchoice_button_ids(layers):
                self.wait_element_timeout(term="", scrap_type=enum.ScrapType.MIXED, optional_term="[style*='fwskin_seekbar_ico']", timeout=10, step=0.1)
                self.wait_element_timeout(term="", scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="[style*='fwskin_seekbar_ico']", timeout=10, step=0.1)
            elif button == self.language.confirm and soup_objects[0].parent.attrs["id"] in self.get_enchoice_button_ids(layers):
                self.wait_element_timeout(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=layers + 1, main_container="body", timeout=10, step=0.1)

        except ValueError as error:
            print(error)
            self.log_error(f"Button {button} could not be located.")
        except AssertionError:
            raise
        except Exception as error:
            print(error)
            self.log_error(str(error))

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

    def WaitHide(self, itens):
        """
        Search string that was sent and wait hide the elements.
        e.g. "Item1,Item2,Item3"

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitHide("Processing")
        """
        itens = list(map(str.strip, itens.split(",")))
        print("Waiting processing...")
        while True:
            soup = self.get_current_DOM()
            elements = soup.find_all('div', string=(itens))
            if not elements:
                break
            time.sleep(5)

    def WaitShow(self,itens):
        """
        Search string that was sent and wait show the elements.
        e.g. "Item1,Item2,Item3"

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitShow("Processing")
        """
        itens = list(map(str.strip, itens.split(",")))
        print("Waiting processing...")
        while True:
            soup = self.get_current_DOM()
            elements = soup.find_all('div', string=(itens))
            if elements:
                break
            time.sleep(5)

    def WaitProcessing(self, itens):
        """
        Uses WaitShow and WaitHide to Wait a Processing screen

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitProcessing("Processing")
        """
        self.WaitShow(itens)

        self.WaitHide(itens)


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

    def ClickFolder(self, folder_name):
        """
        Clicks on folder elements on the screen.

        :param folder_name: Which folder item should be clicked.
        :type folder_name: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickFolder("Folder1")
        """
        self.wait_element(term=folder_name, scrap_type=enum.ScrapType.MIXED, optional_term=".tfolder.twidget")
        self.wait_element(term=folder_name, scrap_type=enum.ScrapType.MIXED, optional_term=".button-bar a")
        #Retira o ToolTip dos elementos focados.
        #self.move_to_element(self.driver.find_element_by_tag_name("html"))

        #try:#Tento pegar o elemento da aba de forma direta sem webscraping
        #    element = lambda: self.driver.find_element_by_link_text(item)
        #except:#caso contrário efetuo o clique na aba com webscraping
        soup = self.get_current_DOM()
        panels = soup.select(".button-bar a")
        panel = next(iter(list(filter(lambda x: x.text == folder_name, panels))))
        element = ""
        if panel:
            element = lambda: self.driver.find_element_by_xpath(xpath_soup(panel))
        if element:
            self.scroll_to_element(element())#posiciona o scroll baseado na height do elemento a ser clicado.
            self.set_element_focus(element())
            time.sleep(1)
            self.driver.execute_script("arguments[0].click()", element())
        else:
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
        grid_number -= 1
        if content_list:
            self.wait_element_timeout(field)
        elif select_all:
            self.wait_element_timeout(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term="label span")

        endtime = time.time() + 60
        grids = None
        while(time.time() < endtime and not grids):
            grids = self.web_scrap(term=".tgetdados,.tgrid,.tcbrowse", scrap_type=enum.ScrapType.CSS_SELECTOR)

        if grids:
            if len(grids) > 1:
                grids = self.filter_displayed_elements(grids,False)
            else:
                grids = self.filter_displayed_elements(grids,True)
        else:
            self.log_error("Couldn't find grid.")

        grid = grids[grid_number]
        column_enumeration = list(enumerate(grid.select("thead label")))
        chosen_column = next(iter(list(filter(lambda x: field in x[1].text, column_enumeration))), None)
        if chosen_column:
            column_index = chosen_column[0]
        else:
            self.log_error("Couldn't find chosen column.")

        content_list = content_list.split(",")

        if select_all:
            self.wait_element(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term="label span")
            element = next(iter(self.web_scrap(term="label.tcheckbox input", scrap_type=enum.ScrapType.CSS_SELECTOR)), None)
            if element:
                box = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                self.click(box())

        elif content_list:
            self.wait_element(content_list[0]) # wait columns

            class_grid = grid.attrs['class'][0]

            column_elements = grid.select(f"td[id='{column_index}']")
            filtered_column_elements = list(filter(lambda x: x.text.strip() in content_list, column_elements))

            for column_element in filtered_column_elements:
                element = self.driver.find_element_by_xpath(xpath_soup(column_element))
                self.scroll_to_element(element)
                self.click(element)
                if class_grid != 'tcbrowse':
                    self.double_click(element)
                else:
                    self.send_keys(element, Keys.ENTER)
        else:
            self.log_error(f"Couldn't locate content: {content_list}")

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
        caracter = (r'[.\/+-]')
        if string[0:4] != 'http':
            match = re.findall(caracter, string)
            if match:
                string = re.sub(caracter, '', string)

        return string

    def SetKey(self, key, grid=False, grid_number=1):
        """
        Press the desired key on the keyboard on the focused element.

        Supported keys: F1 to F12, Up, Down, Left, Right, Enter and Delete

        :param key: Key that would be pressed
        :type key: str
        :param grid: Boolean if action must be applied on a grid. (Usually with DOWN key)
        :type grid: bool
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetKey("ENTER")
        >>> #--------------------------------------
        >>> # Calling the method on a grid:
        >>> oHelper.SetKey("DOWN", grid=True)
        >>> #--------------------------------------
        >>> # Calling the method on the second grid on the screen:
        >>> oHelper.SetKey("DOWN", grid=True, grid_number=2)
        """
        print(f"Key pressed: {key}")
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
            "LEFT": Keys.LEFT,
            "RIGHT": Keys.RIGHT,
            "DELETE" : Keys.DELETE,
            "ENTER": Keys.ENTER
        }

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
        grid_number-=1
        try:
            Id = self.driver.execute_script(script)
            if Id:
                element = self.driver.find_element_by_id(Id)
            else:
                element = self.driver.find_element(By.TAG_NAME, "html")

            if key.upper() in supported_keys:
                if key.upper() == "DOWN" and grid:
                    #self.UTSetValue('aItens','newline','0')
                    if grid_number is None:
                        grid_number = 0
                    self.grid_input.append(["", "", grid_number, True])
                else:
                    self.set_element_focus(element)
                    self.send_keys(element, supported_keys[key.upper()])
            else:
                self.log_error("Key is not supported")

        except Exception as error:
            self.log_error(str(error))

    def SetFocus(self, field):
        """
        Sets the current focus on the desired field.

        :param field: The field that must receive the focus.
        :type field: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFocus("A1_COD")
        """
        print(f"Setting focus on element {field}.")
        element = lambda: self.driver.find_element_by_xpath(xpath_soup(self.get_field(field)))
        self.set_element_focus(element())

    def click_check_radio_button(self, field, value):
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

        if re.match(r"\w+(_)", field):
            self.wait_element(field)
            element = next(iter(self.web_scrap(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)), None)
        else:
            self.wait_element(field, scrap_type=enum.ScrapType.MIXED, optional_term="label")
            element = next(iter(self.web_scrap(term=field, scrap_type=enum.ScrapType.MIXED, optional_term=".tradiobutton .tradiobuttonitem label, .tcheckbox span")), None)


        if not element:
            self.log_error("Couldn't find span element")

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

    def input_grid_appender(self, column, value, grid_number=0, new=False, row=None):
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
            
        self.grid_input.append([column, value, grid_number, new, row])

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

        self.wait_element(term=".tgetdados, .tgrid", scrap_type=enum.ScrapType.CSS_SELECTOR)

        x3_dictionaries = self.create_x3_tuple()

        initial_layer = 0
        if self.grid_input:
            soup = self.get_current_DOM()
            initial_layer = len(soup.select(".tmodaldialog"))

        for field in self.grid_input:
            if field[3] and field[0] == "":
                self.new_grid_line(field)
            else:
                print(f"Filling grid field: {field[0]}")
                self.fill_grid(field, x3_dictionaries, initial_layer)

        for field in self.grid_check:
            print(f"Checking grid field value: {field[0]}")
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

        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]
            field_to_valtype = x3_dictionaries[0]
            field_to_len = x3_dictionaries[1]

        while(self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body")):
            print("Waiting for container to be active")
            time.sleep(1)

        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog")
        if containers:
            containers = self.zindex_sort(containers, True)

            grids = containers[0].select(".tgetdados, .tgrid")

            grids = self.filter_displayed_elements(grids)
            if grids:
                headers = self.get_headers_from_grids(grids)
                grid_id = grids[field[2]].attrs["id"]
                if grid_id not in self.grid_counters:
                    self.grid_counters[grid_id] = 0

                column_name = ""
                if field[2] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)
                down_loop = 0
                rows = grids[field[2]].select("tbody tr")
                
                if (field[4] is not None) and (field[4] > len(rows) - 1 or field[4] < 0):
                    self.log_error(f"Couldn't select the specified row: {field[4] + 1}")
                    
                row = self.get_selected_row(rows) if field[4] == None else rows[field[4]]

                if row:
                    while (int(row.attrs["id"]) < self.grid_counters[grid_id]) and (down_loop < 2) and self.down_loop_grid and field[4] is None:
                        self.new_grid_line(field, False)
                        row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))
                        down_loop+=1
                    self.down_loop_grid = False
                    columns = row.select("td")
                    if columns:
                        if "_" in field[0]:
                            try:
                                column_name = field_to_label[field[0]].lower()
                            except:
                                self.log_error("Couldn't find column '" + field[0] + "' in sx3 file. Try with the field label.")
                        else:
                            column_name = field[0].lower()

                        if column_name not in headers[field[2]]:
                            self.log_error(self.language.messages.grid_column_error)

                        column_number = headers[field[2]][column_name]

                        current_value = columns[column_number].text.strip()
                        xpath = xpath_soup(columns[column_number])

                        try_counter = 0

                        while(self.remove_mask(current_value).strip() != self.remove_mask(field[1]).strip()):

                            selenium_column = lambda: self.get_selenium_column_element(xpath) if self.get_selenium_column_element(xpath) else self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
                            self.scroll_to_element(selenium_column())
                            self.click(selenium_column())
                            self.set_element_focus(selenium_column())

                            while(not self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body")):
                                time.sleep(1)
                                self.scroll_to_element(selenium_column())
                                self.set_element_focus(selenium_column())
                                self.click(selenium_column())
                                ActionChains(self.driver).move_to_element(selenium_column()).send_keys_to_element(selenium_column(), Keys.ENTER).perform()
                                time.sleep(1)

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
                                if self.check_mask(selenium_input()):
                                    user_value = self.remove_mask(user_value)

                                self.wait.until(EC.visibility_of(selenium_input()))
                                self.set_element_focus(selenium_input())
                                self.click(selenium_input())
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
                                                self.send_keys(selenium_input(), Keys.ENTER)

                                self.wait_element(term=xpath_soup(child[0]), scrap_type=enum.ScrapType.XPATH, presence=False)
                                time.sleep(1)
                                current_value = self.get_element_text(selenium_column())

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
                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

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
        if self.config.debug_log:
            print("Recovering lost line")
        while int(row.attrs["id"]) < self.grid_counters[grid_id]:
            self.new_grid_line(field, False)
            row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))

        columns = row.select("td")
        if columns:
            if "_" in field[0]:
                column_name = field_to_label[field[0]]
            else:
                column_name = field[0]

            if column_name not in headers[field[2]]:
                self.log_error(self.language.messages.grid_column_error)

            column_number = headers[field[2]][column_name]
            xpath = xpath_soup(columns[column_number])
            ret = self.get_selenium_column_element(xpath)
            while not ret:
                ret = self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
            return ret
        else:
            return False

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
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> self.check_grid([0, "A1_COD", "000001", 0], x3_dictionaries, False)
        """
        field_to_label = {}
        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]

        while(self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=3, main_container="body")):
            if self.config.debug_log:
                print("Waiting for container to be active")
            time.sleep(1)

        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog.twidget")
        if containers:

            containers = self.zindex_sort(containers, True)
            grids = self.filter_displayed_elements(containers[0].select(".tgetdados, .tgrid"))
            if grids:

                headers = self.get_headers_from_grids(grids)
                column_name = ""
                if field[3] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                rows = grids[field[3]].select("tbody tr")
                if rows:
                    if field[0] > len(rows):
                        self.log_error(self.language.messages.grid_line_error)

                    columns = rows[field[0]].select("td")
                    if columns:
                        if "_" in field[1]:
                            column_name = field_to_label[field[1]].lower()
                        else:
                            column_name = field[1].lower()

                        if column_name not in headers[field[3]]:
                            self.log_error(self.language.messages.grid_column_error)

                        column_number = headers[field[3]][column_name]
                        text = columns[column_number].text.strip()

                        if get_value:
                            return text

                        field_name = f"({field[0]}, {column_name})"
                        self.log_result(field_name, field[2], text)
                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

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
        self.down_loop_grid = True

        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog.twidget")
        if containers:

            containers = self.zindex_sort(containers, True)
            grids = self.filter_displayed_elements(containers[0].select(".tgetdados, .tgrid"))
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
                        self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath_soup(columns[0]))))
                        ActionChains(self.driver).move_to_element(second_column()).send_keys_to_element(second_column(), Keys.DOWN).perform()

                        while not(self.element_exists(term=".tgetdados tbody tr, .tgrid tbody tr", scrap_type=enum.ScrapType.CSS_SELECTOR, position=len(rows)+1)):
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
        row_number -= 1
        grid_number -= 1
        column_name = ""

        if re.match(r"\w+(_)", column):
            column_name = self.get_x3_dictionaries([column])[2][column].lower()
        else:
            column_name = column.lower()

        containers = self.web_scrap(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        if not containers:
            self.log_error("Couldn't find controller.")

        container = next(iter(self.zindex_sort(containers, True)), None)
        grids = self.filter_displayed_elements(container.select(".tgetdados, .tgrid"))
        if not grids:
            self.log_error("Couldn't find any grid.")

        headers = self.get_headers_from_grids(grids)
        if grid_number > len(grids):
            self.log_error(self.language.messages.grid_number_error)

        rows = grids[grid_number].select("tbody tr")
        if not rows:
            self.log_error("Couldn't find rows.")

        if row_number > len(rows):
            self.log_error(self.language.messages.grid_line_error)

        columns = rows[row_number].select("td")
        if not columns:
            self.log_error("Couldn't find columns.")

        if column_name not in headers[grid_number]:
            self.log_error(self.language.messages.grid_column_error)

        column_number = headers[grid_number][column_name]
        column_element = lambda : self.driver.find_element_by_xpath(xpath_soup(columns[column_number]))

        self.click(column_element())

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
                        index_col='Campo', names=['Campo', 'Tipo', 'Tamanho', 'Título', None], low_memory=False)
        df = pd.DataFrame(data, columns=['Campo', 'Tipo', 'Tamanho', 'Título', None])
        if not regex:
            df_filtered = df.query("Tipo=='C' or Tipo=='N' or Tipo=='D' ")
        else:
            df_filtered = df.filter(regex=regex, axis=0)

        #Retiro os espaços em branco da coluna Campo e Titulo.
        df_filtered['Título'] = df_filtered['Título'].map(lambda x: x.strip())
        df_filtered.index = df_filtered.index.map(lambda x: x.strip())

        dict_ = df_filtered.to_dict()

        return (dict_['Tipo'], dict_['Tamanho'], dict_['Título'])

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

    def wait_element(self, term, scrap_type=enum.ScrapType.TEXT, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog"):
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
        endtime = time.time() + self.config.timeout
        print("Waiting for element")

        if presence:
            while (not self.element_exists(term, scrap_type, position, optional_term, main_container) and time.time() < endtime):
                time.sleep(0.1)
        else:
            while (self.element_exists(term, scrap_type, position, optional_term, main_container) and time.time() < endtime):
                time.sleep(0.1)

        if time.time() > endtime:
            self.log_error(f"Element {term} not found!")

        presence_endtime = time.time() + 10
        if presence:
            if self.config.debug_log:
                print("Element found! Waiting for element to be displayed.")
            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)), None)
            if element is not None:
                sel_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                while(not sel_element().is_displayed() and time.time() < presence_endtime):
                    time.sleep(0.1)

    def wait_element_timeout(self, term, scrap_type=enum.ScrapType.TEXT, timeout=5.0, step=0.1, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog"):
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
                if self.element_exists(term, scrap_type, position, optional_term, main_container):
                    success = True
                    break
        else:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if not self.element_exists(term, scrap_type, position, optional_term, main_container):
                    success = True
                    break

        if presence and success:
            if self.config.debug_log:
                print("Element found! Waiting for element to be displayed.")
            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)), None)
            if element is not None:
                sel_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                while(not sel_element().is_displayed()):
                    time.sleep(0.1)

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

    def SetFilePath(self, value):
        """
        Fills the path screen with desired path.

        :param value: Path to be inputted.
        :type value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFilePath(r"C:\\folder")
        """
        self.wait_element("Nome do Arquivo:")
        element = self.driver.find_element(By.CSS_SELECTOR, ".filepath input")
        if element:
            self.driver.execute_script("document.querySelector('#{}').value='';".format(element.get_attribute("id")))
            self.send_keys(element, value)
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".tremoteopensave button")
        if elements:
            for line in elements:
                if line.text.strip().upper() == "ABRIR":
                    self.click(line)
                    break

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

        "help" - closes element.

        :param text: Text to be checked.
        :type text: str
        :param element_type: Type of element. - **Default:** "help"
        :type element_type: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.CheckView("Processing")
        """
        if element_type == "help":
            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=".tsay")
            if not self.element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay"):
                self.errors.append(self.language.messages.text_not_found)
            else:
                self.SetButton(self.language.close)

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
        self.wait.until(EC.visibility_of(element_function()))
        if try_counter == 0:
            element_function().send_keys(key)
        elif try_counter == 1:
            ActionChains(self.driver).move_to_element(element_function()).send_keys_to_element(element_function(), key).perform()
        else:
            ActionChains(self.driver).move_to_element(element_function()).send_keys(key).perform()

    def find_label_element(self, label_text, container):
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
        element = next(iter(list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"(\s*)?([\*\?]{1})?(\s*)?$"))))), None)
        if element is None:
            return []

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
                self.used_ids.append(next_sibling.attrs["id"])
                return [next_sibling]
            elif (("tget" in second_next_sibling.attrs["class"]
                    or "tcombobox" in second_next_sibling.attrs["class"])
                    and second_next_sibling.attrs["id"] not in self.used_ids):
                self.used_ids.append(second_next_sibling.attrs["id"])
                return [second_next_sibling]
            else:
                return []

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
                self.used_ids.append(previous_sibling.attrs["id"])
                return [previous_sibling]
            elif (("tget" in second_previous_sibling.attrs["class"]
                    or "tcombobox" in second_previous_sibling.attrs["class"])
                    and second_previous_sibling.attrs["id"] not in self.used_ids):
                self.used_ids.append(second_previous_sibling.attrs["id"])
                return [second_previous_sibling]
            else:
                return []

        #If element is not tsay => return it
        elif (hasattr(element, "attrs") and "class" in element.attrs
            and "tsay" not in element.attrs["class"]):
            return [element]

        #If label exists but there is no element associated with it => return empty list
        else:
            return []

    def log_error(self, message, new_log_line=True):
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
        stack_item = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function), inspect.stack())))), None)
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number} {message}"
        self.log.set_seconds()
        self.driver.save_screenshot("error.png")

        if new_log_line:
            self.log.new_line(False, log_message)
        self.log.save_file()
        self.restart()
        self.assertTrue(False, log_message)

    def ClickIcon(self, icon_text):
        """
        Clicks on an Icon button based on its tooltip text.

        :param icon_text: The tooltip text.
        :type icon_text: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickIcon("Add")
        >>> oHelper.ClickIcon("Edit")
        """
        self.wait_element(term=".tmodaldialog button[style]", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        soup = self.get_current_DOM()
        container = next(iter(self.zindex_sort(soup.select(".tmodaldialog"))), None)
        container = container if container else soup
        buttons = container.select("button[style]")
        print("Searching for Icon")
        filtered_buttons = self.filter_by_tooltip_value(buttons, icon_text)
        #filtered_buttons = list(filter(lambda x: self.check_element_tooltip(x, icon_text), buttons))

        button = next(iter(filtered_buttons), None)
        if not button:
            self.log_error("Couldn't find Icon button.")

        button_element = lambda: self.driver.find_element_by_xpath(xpath_soup(button))

        self.click(button_element())

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
        self.parameters.append([parameter, branch, portuguese_value, english_value, spanish_value])

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
        self.driver.refresh()
        if self.config.browser.lower() == "chrome":
            try:
                self.wait.until(EC.alert_is_present())
                self.driver.switch_to_alert().accept()
            except:
                pass

        self.Setup("SIGACFG", self.config.date, self.config.group, self.config.branch, save_input=False)
        self.SetLateralMenu(self.config.parameter_menu if self.config.parameter_menu else self.language.parameter_menu, save_input=False)
        self.ClickIcon(self.language.search)

        self.fill_parameters(restore_backup=restore_backup)

        self.LogOff()

        self.Setup(self.config.initialprog, self.config.date, self.config.group, self.config.branch, save_input=False)
        self.Program(self.config.routine)

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

            self.SetValue("X6_FIL", parameter[1])
            self.SetValue("X6_CONTEUD", parameter[2])
            self.SetValue("X6_CONTENG", parameter[3])
            self.SetValue("X6_CONTSPA", parameter[4])

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

    def check_element_tooltip(self, element, expected_text):
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
        element_function = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
        self.driver.execute_script(f"$(arguments[0]).mouseover()", element_function())
        time.sleep(0.5)
        tooltips = self.driver.find_elements(By.CSS_SELECTOR, ".ttooltip")
        has_text = (tooltips and tooltips[0].text.lower() == expected_text.lower())
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

    def assert_result(self, expected):
        """
        [Internal]

        Asserts the result based on the expected value.

        :param expected: Expected value
        :type expected: bool

        Usage :

        >>> #Calling the method:
        >>> self.assert_result(True)
        """
        expected_assert = expected
        msg = "Passed"
        stack_item = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function), inspect.stack())))), None)
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number}"
        self.log.set_seconds()

        if self.grid_input or self.grid_check:
            self.log_error("Grid fields were queued for input/check but weren't added/checked. Verify the necessity of a LoadGrid() call.")

        if self.errors:
            expected = not expected

            for field_msg in self.errors:
                log_message += (" " + field_msg)

            msg = log_message

            self.log.new_line(False, log_message)
        else:
            self.log.new_line(True, "")

        self.log.save_file()

        self.errors = []
        print(msg)
        if expected_assert:
            self.assertTrue(expected, msg)
        else:
            self.assertFalse(expected, msg)