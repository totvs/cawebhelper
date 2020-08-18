import re
import time
import inspect
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import tir.technologies.core.enumerations as enum
from tir.technologies.core.language import LanguagePack
from tir.technologies.core.third_party.xpath_soup import xpath_soup
from tir.technologies.core.base import Base


class MobileInternal(Base):

    def __init__(self, config_path="", autostart=True):
        super().__init__(config_path, autostart)
        # put here the global attributes


    def Setup(self):
        """
        Prepare the App for the test case.
        """
        if not self.config.valid_language:
            self.config.language = self.get_language()
            self.language = LanguagePack(self.config.language)


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


    def currentDOM(self):
        """
        [Internal]

        Returns current HTML DOM parsed as a BeautifulSoup object

        :returns: BeautifulSoup parsed DOM
        :rtype: BeautifulSoup object

        Usage:

        >>> #Calling the method
        >>> soup = self.currentDOM()
        """
        try:
            soup = self.get_current_DOM()
            if not soup:
                raise Exception("Search for erros cound't find DOM")
            return soup
        except Exception as e:
            self.log_error(str(e))


    def User_screen(self, show_password=False):
        """
        Fills the user login screen of Web App with the user and password and alias located on config.json.

        :param show_password: if True shows the password. - **Default:** False
        :type bool

        Usage:

        >>> # Calling the method
        >>> oHelper.user_screen()
        """
        try:
            if show_password:
                self.Checkbox('Exibir Senha')
            self.SetValue(self.language.user, self.config.user)
            self.SetValue(self.language.password, self.config.password)
        except Exception as e:
            self.log_error(str(e))


    def SetButton(self, term, sub_item=""):
        """
        Method that clicks on a button on the screen.

        :param term: Button to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> oHelper.SetButton("Add")
        """
        try:
            if not term:
                raise Exception("Enter text that makes it possible to locate the desired button.")
            else:
                print(f"Clicking on {sub_item} {term}" if sub_item else f"Clicking on {term}")
            webContainer = self.buttonBack(term=term)
            if webContainer is '':
                webContainer = self.buttonInner(term=term, sub_item=sub_item)
            if webContainer is '':
                self.buttonCard(term=term)
        except Exception as e:
            self.log_error(str(e))


    def buttonBack(self, term):
        """
        [Internal]

        Method that clicks on a button on the screen.
        Button with selector 'button.back-button'

        :param term: Button to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> self.buttonBack("Add")
        """
        webContainer = ''
        optional_term = 'button.back-button'
        if self.wait_element(term=term, scrap_type=enum.ScrapType.TEXT, log_error=False) and self.wait_element(term='.show-back-button', log_error=False):
            self.wait_element(term=optional_term)
            container = self.currentDOM()
            elements = container.select(optional_term)
            for element in elements:
                webContainer = element.find_next_sibling("div")
                if webContainer and term.upper().strip() == webContainer.text.upper().strip():
                    webElement = self.driver.find_element_by_xpath(xpath_soup(element))
                    if webElement.is_displayed():
                        self.waitElementTimeout()
                        webElement.click()
                        self.waitElementTimeout()
                        break
                    else:
                        webContainer = ''
                else:
                    webContainer = ''
        return webContainer


    def buttonInner(self, term, sub_item=""):
        """
        [Internal]

        Method that clicks on a button on the screen.
        Button with selector '.tab-button-text, .button-inner, .totvs-button'

        :param term: Button to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> self.buttonInner("Add")
        """
        webContainer = ''
        optional_term = '.tab-button-text, .button-inner, .totvs-button'
        if self.wait_element(term=term, scrap_type=enum.ScrapType.TEXT, log_error=False) and self.wait_element(term=optional_term):
            self.waitElementTimeout()
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=optional_term, container=container, comparation='contains')
            if len(webContainer) > 1:
                if sub_item and 'button-inner' in optional_term:
                    listAux = [x for x in webContainer if sub_item.upper().strip() in self.find_first_div_parent(x).h1.text.upper().strip()]
                    if listAux:
                        webContainer = next(iter( listAux ))
                    else:
                        raise Exception("The button element not found.")
                else:
                    listAux = [x for x in webContainer if hasattr(x.find_parent(), "attrs") and "class" in x.find_parent().attrs and "alert-button" in x.find_parent().attrs["class"] and x.find_parent().attrs["ion-button"] == "alert-button"]
                    webContainer = listAux if listAux else webContainer
                    webContainer = next(iter(webContainer))
            if webContainer:
                while not self.driver.find_element_by_xpath(xpath_soup(webContainer)).is_displayed():
                    time.sleep(0.1)
                    print('The button element is not visible.')
                self.waitElementTimeout()
                self.driver.find_element_by_xpath(xpath_soup(webContainer)).click()
                self.waitElementTimeout()
            else:
                webContainer = ''
        return webContainer


    def buttonCard(self, term):
        """
        [Internal]

        Method that clicks on a button on the screen.
        Button with selector 'button.card-buttom-white'

        :param term: Button to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> self.buttonCard("Add")
        """
        webContainer = ''
        seekTerm = '.input-wrapper > ion-label.label.label-md'
        optional_term = 'button.card-buttom-white'
        if self.wait_element(term=term, scrap_type=enum.ScrapType.TEXT, log_error=False) and self.wait_element(term=seekTerm):
            self.waitElementTimeout()
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=seekTerm, container=container, comparation='contains')
            if webContainer:
                webBackup = webContainer
                webContainer = self.webContainer(term=term, optional_term=optional_term, container=container)
                if not webContainer:
                    webContainer = webBackup if type(webBackup) is not list or len(webBackup) == 1 else webBackup[0]
            else:
                raise Exception("The button element not found.")
            self.waitElementTimeout()
            self.driver.find_element_by_xpath(xpath_soup(webContainer)).click()
            self.waitElementTimeout()
        return webContainer


    def wait_element(self, term, scrap_type=enum.ScrapType.CSS_SELECTOR, presence=True, main_container="body", log_error=True):
        """
        [Internal]

        Waits until the desired element is located on the screen.

        :param term: The first search term. A text or a selector.
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param presence: If the element should exist or not in the screen. - **Default:** False
        :type presence: bool
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str
        :param log_error: Controls whether to generate error log. - **Default:** True
        :type log_error: bool

        Usage:

        >>> # Calling the method:
        >>> self.wait_element(term='input[class*="searchbar-input"]')
        """
        try:
            endtime = time.time() + self.config.time_out
            if presence:
                while (not self.element_exists(term=term, scrap_type=scrap_type, main_container=main_container) and time.time() < endtime):
                    time.sleep(0.1)
            if time.time() > endtime:
                if log_error:
                    self.log_error(f"Element {term} not found!")
                return False
            return True
        except Exception as e:
            self.log_error(str(e))


    def ClickFolder(self, term):
        """
        Clicks on folder elements on the screen.

        :param term: Which folder item should be clicked.
        :type term: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickFolder("Folder1")
        """
        try:
            if not term:
                raise Exception("Enter text that makes it possible to locate the desired folder.")
            else:
                print(f"Clicking on {term}")
            optional_term=".segment-button"
            self.wait_element(term=optional_term)
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=optional_term, container=container, xsplit='(')
            self.waitElementTimeout()
            self.driver.find_element_by_xpath(xpath_soup(webContainer)).click()
        except Exception as e:
            self.log_error(str(e))


    def Checkbox(self, term):
        """
        Clicks on checkbox elements on the screen.

        :param term: Text to be searched
        :type button: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Checkbox('Exibir Senha')
        """
        try:
            if not term:
                raise Exception("Enter text that allows you to locate the desired checkbox.")
            else:
                print(f"Clicking on {term}")
            webContainer = self.checkItem(term=term, selector1='.lookup-list > div > .item', xsplit='Filial')
            if not webContainer:
                webContainer = self.checkInner(term=term, selector1='.show-pass', selector2='.show-pass .item-inner .input-wrapper .label-md', selector3='.item-cover .button-inner')
            if not webContainer:
                webContainer = self.checkText(term=term, selector1='div[class*="select-icon"]', selector2='.select-text')
            if not webContainer:
                webContainer = self.checkDiv(term=term, selector1='div > ion-list.list.list-md', selector2='div.item-inner', xsplit='(')
            if not webContainer:
                webContainer = self.checkIon(term=term, selector1='ion-checkbox.checkbox')
            if not webContainer:
                raise Exception("Couldn't find checkbox element.")
            self.waitElementTimeout()
            self.driver.find_element_by_xpath(xpath_soup(webContainer)).click()
            self.waitElementTimeout()
        except Exception as e:
            self.log_error(str(e))


    def checkItem(self, term, selector1, xsplit):
        """
        [Internal]

        Method that clicks on checkbox elements on the screen.
        Checkbox with selector '.lookup-list > div > .item'

        :param term: Checkbox to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular checkbox:
        >>> self.checkItem("Exibir Senha")
        """
        webContainer = []
        if self.wait_element(term=selector1, log_error=False):
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=selector1, container=container, xsplit=xsplit)
        return webContainer


    def checkInner(self, term, selector1, selector2, selector3):
        """
        [Internal]

        Method that clicks on checkbox elements on the screen.
        Checkbox with selector '.show-pass .item-inner .input-wrapper .label-md'

        :param term: Checkbox to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular checkbox:
        >>> self.checkInner("Exibir Senha")
        """
        webContainer = []
        if self.wait_element(term=selector1, log_error=False):
            # Toggle
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=selector2, container=container)
            if not webContainer:
                raise Exception("Couldn't find checkbox element.")
            webContainer = next(iter(container.select(selector3)))
        return webContainer


    def checkText(self, term, selector1, selector2):
        """
        [Internal]

        Method that clicks on checkbox elements on the screen.
        Checkbox with selector '.select-text'

        :param term: Checkbox to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular checkbox:
        >>> self.checkText("Exibir Senha")
        """
        webContainer = []
        if self.wait_element(term=selector1, log_error=False):
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=selector2, container=container)
        return webContainer


    def checkDiv(self, term, selector1, selector2, xsplit):
        """
        [Internal]

        Method that clicks on checkbox elements on the screen.
        Checkbox with selector 'div.item-inner'

        :param term: Checkbox to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular checkbox:
        >>> self.checkDiv("Exibir Senha")
        """
        webContainer = []
        if self.wait_element(term=selector1, log_error=False):
            # checkbox
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=selector2, container=container, xsplit=xsplit)
            if not webContainer:
                raise Exception("Couldn't find checkbox element.")
            webContainer = webContainer.find_parent()
        return webContainer

    
    def checkIon(self, term, selector1):
        """
        [Internal]

        Method that clicks on checkbox elements on the screen.
        Checkbox with selector 'ion-checkbox.checkbox'

        :param term: Checkbox to be clicked.
        :type term: str

        Usage:

        >>> # Calling the method to click on a regular checkbox:
        >>> self.checkIon("Exibir Senha")
        """
        webContainer = []
        if not webContainer and self.wait_element(term=selector1, log_error=False):
            container = self.currentDOM()
            webContainer = next(iter([x for x in container.select(selector1) if term.upper().strip() in x.parent.text.upper().strip()]))
        return webContainer


    def RadioButton(self, term):
        """
        Clicks on radiobutton elements on the screen.

        :param term: Text to be searched
        :type button: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.RadioButton('HTTPS')
        """
        try:
            if not term:
                raise Exception("Enter text to locate the desired radiobutton.")
            else:
                print(f"Clicking on {term}")
            optional_term=".radio.radio-md"
            if self.wait_element(term=optional_term, log_error=False):
                container = self.currentDOM()
                webContainer = next(iter([ x for x in container.select(optional_term) if term.upper().strip() == x.attrs["ng-reflect-value"].upper().strip() ]))
                if not webContainer:
                    raise Exception("Couldn't find RadioButton element.")
            self.driver.find_element_by_xpath(xpath_soup(webContainer)).click()
        except Exception as e:
            self.log_error(str(e))


    def Settings(self, term):
        """
        Displays the settings screen.

        :param term: Text to be searched
        :type button: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Settings('MEUS ATIVOS FIXOS')
        """
        try:
            if not term:
                raise Exception("Enter text that makes it possible to locate the desired button.")
            else:
                print(f"Clicking on {term}")
            optional_term = self.settSelector()
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term=optional_term[0], container=container)
            if not webContainer: 
                raise Exception("Couldn't find settings element.")
            webContainer = next(iter(container.select(optional_term[1])))
            self.driver.find_element_by_xpath(xpath_soup(webContainer)).click()
        except Exception as e:
            self.log_error(str(e))


    def settSelector(self):
        """
        [Internal]

        Get the possible Settings selectors
        """
        self.wait_element(term='.settings, .settings-button', log_error=False)
        listSelector = [
            ['.header-container > .title', '.header-container > .title', '.icon.icon-md.ion-md-settings'                   ],
            ['div.button-effect'         , '.toolbar-title'            , 'button.bar-button.bar-button-md.bar-button-clear']
        ]
        for selector in listSelector:
            if self.wait_element(term=selector[0], log_error=False):
                return[selector[1], selector[2]]
        return['', '']


    def SetValue(self, term, value):
        """
        Sets value of an input element.
        
        :param term: The field name or label to receive the value
        :type field: str
        :param value: The value to be inputted on the element.
        :type value: str or bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetValue("Pesquisar", "Ativo Origem")
        """
        try:
            if not term:
                raise Exception("Enter text that makes it possible to locate the desired input.")
            else:
                print(f'Filling {term}')
            self.input_value(term, value)
        except Exception as e:
            self.log_error(str(e))
        
    
    def input_value(self, term, value):
        """
        [Internal]

        Sets value of an input element.
        
        :param term: The field name or label to receive the value
        :type field: str
        :param value: The value to be inputted on the element.
        :type value: str or bool

        Usage:

        >>> # Calling the method:
        >>> self.input_value("Pesquisar", "Ativo Origem")
        """
        try:
            optional_term = self.inputSelector(term)
            container = self.currentDOM()
            webContainer = self.webContainer(term=term, optional_term="ion-label.label", container=container)
            if len(webContainer) > 1:
                for element in webContainer:
                    self.inputKeys(element=element, optional_term=optional_term, container=container, value=value)
            else:
                self.inputKeys(element=webContainer, optional_term=optional_term, container=container, value=value)
        except Exception as e:
            self.log_error(str(e))


    def inputKeys(self, element, optional_term, container, value):
        """
        [Internal]

        Sets value of an input element.
        Auxiliary routine of input_value
        """
        if element and hasattr(element.find_parent(),"ion-label.label"):
            container = element.parent
            optional_term[0] = 'input'
        webContainer = next(iter( [x for x in container.select(optional_term[0]) ] ))
        webElement = self.driver.find_element_by_xpath(xpath_soup(webContainer))
        if webElement.is_displayed():
            webElement.clear()
            webElement.send_keys(value, Keys.TAB)


    def inputSelector(self, term):
        """
        [Internal]

        Get the possible input selectors

        :param term: The field name or label to receive the value
        :type field: str
        """
        term = term.split(' ')[0]
        if self.wait_element(term='input.text-input.text-input-md', log_error=False) or self.wait_element(term=f'input[placeholder~={term}]', log_error=False):
            listSelector = [
                ['.searchbar-input[type="text"]', 'input[type="text"]'         , 'ion-searchbar[type="text"]'                ],
                ['.searchbar-input'             , 'input[type="search"]'       , '.searchbar-has-value'                      ],
                ['t-input[class*="ng-valid"]'   , 'input[type="text"]'         , 't-input[class*="ng-valid"]'                ],
                [f'input[placeholder~={term}]'  , f'input[placeholder~={term}]', f'ion-input[ng-reflect-placeholder~={term}]']
            ]
            for selector in listSelector:
                if self.wait_element(term=selector[0], log_error=False):
                    return[selector[1], selector[2]]
        return['', '']


    def webContainer(self, term, optional_term, container, xsplit='', comparation='exactly'):
        """
        [Internal]

        Get a container based on a selector

        :param term: A text to aid in selector identification
        :type term: str
        :param optional_term: A selector used in webscraping.
        :type optional_term: str
        :param container: current HTML DOM parsed as a BeautifulSoup object
        :type container: class bs4.BeautifulSoup
        :param xsplit: Determines how far the text will be considered
        :type xsplit: str
        """
        if comparation == 'contains':
            webList = [x for x in container.select(optional_term) if x.text.strip() and term.upper().strip() in x.text.upper().strip()]
        else:
            webList = [x for x in container.select(optional_term) if x.text.strip() and term.upper().strip() == x.text.upper().strip()]
        if webList:
            if len(webList) == 1:
                webList = next(iter(webList))
        elif xsplit:
            webList = [x for x in container.select(optional_term) if x.text.strip() and term.upper().strip() == re.sub(r"\t|\n|\r|\xa0", "", x.text).split(xsplit)[0].upper().strip() ]
            if webList:
                webList = next(iter(webList))
        return(webList)


    def CheckResult(self, term, value):
        """
        Checks if a field has the value the user expects.

        :param term: The field or label of a field that must be checked.
        :type term: str
        :param value: The value that the field is expected to contain.
        :type value: str

        Usage:

        >>> # Calling method to check a value of a field:
        >>> oHelper.CheckResult("Pesquisar", "MOBILE")
        """
        term_web_value = self.inputSelector(term)[1]
        endtime = time.time() + 10
        webValue = ''
        while(time.time() < endtime and not webValue):
            webValue = self.get_web_value(term='ng-reflect-model', optional_term=term_web_value)
        print(f"Value for Field {term} is: {webValue}")
        self.log_result(term, value, webValue)


    def log_result(self, term, value, webValue):
        """
        [Internal]

        Logs the result of comparison between user value and captured value.

        :param term: The field whose values would be compared
        :type term: str
        :param value: The value the user expects
        :type value: str
        :param webValue: The value that was captured on the screen
        :type webValue: str

        Usage:

        >>> # Calling the method:
        >>> self.log_result("Pesquisar", "MOBILE", "MOBILE")
        """
        txtaux = ""
        message = ""
        if webValue and webValue.upper().strip() != value.upper().strip():
            message = self.create_message([txtaux, term, value, webValue], enum.MessageType.INCORRECT)
        self.compare_field_values(term, value, webValue, message)


    def get_web_value(self, term='', optional_term=''):
        """
        [Internal]

        Gets the current value or text of element.

        :param term: A selector used in webscraping.
        :type term: str
        :param optional_term: The second search term. A selector used in webscraping.
        :type optional_term: str

        :return: The value or text of passed term
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> current_value = self.get_web_value(selenium_field_element)
        """
        try:
            if optional_term:
                self.wait_element(term=optional_term)
                container = self.currentDOM()
                webContainer = next(iter(container.select(optional_term)))
                webElement = self.driver.find_element_by_xpath(xpath_soup(webContainer))
                return webElement.get_attribute(term)
            return None
        except Exception as e:
            self.log_error(str(e))


    def waitElementTimeout(self, timeout=None):
        """
        [Internal]

        Wait show the elements.

        :param timeout: Seconds to wait
        :type timeout: int

        Usage:

        >>> # Calling the method:
        >>> self.waitElementTimeout()
        """
        if not timeout:
            timeout = self.config.time_out
        endtime = time.time() + timeout
        while(time.time() < endtime):
            time.sleep(0.1)


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
        return correctMessage.format(args[0], args[1])


    def assert_result(self, expected):
        """
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

        if self.errors:
            expected = not expected

            for field_msg in self.errors:
                log_message += (" " + field_msg)

            msg = log_message

            self.log.new_line(False, log_message)
        else:
            self.log.new_line(True, "")

        routine_name = self.config.routine if ">" not in self.config.routine else self.config.routine.split(">")[-1].strip()
        routine_name = routine_name if routine_name else "error"
        self.log.save_file(routine_name)
        self.errors = []
        print(msg)
        if expected_assert:
            self.assertTrue(expected, msg)
        else:
            self.assertFalse(expected, msg)



        
