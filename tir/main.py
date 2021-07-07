from tir.technologies.webapp_internal import WebappInternal
from tir.technologies.apw_internal import ApwInternal
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.base_database import BaseDatabase
"""
This file must contain the definition of all User Classes.

These classes will contain only calls to the Internal classes.
"""

class Webapp():
    """
    Instantiates the Webapp automated interface testing class.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str
    :param autostart: Sets whether TIR should open browser and execute from the start. - **Default:** True
    :type: bool
    """
    def __init__(self, config_path="", autostart=True):
        self.__webapp = WebappInternal(config_path, autostart)
        self.__database = BaseDatabase(config_path, autostart=False)
        self.config = ConfigLoader()
        self.coverage = self.config.coverage

    def AddParameter(self, parameter, branch, portuguese_value="", english_value="", spanish_value=""):
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
        self.__webapp.AddParameter(parameter, branch, portuguese_value, english_value, spanish_value)

    def AssertFalse(self, expected=False, scritp_message=''):
        """
        Defines that the test case expects a False response to pass

        Usage:

        >>> #Instantiating the class
        >>> inst.oHelper = Webapp()
        >>> #Calling the method
        >>> inst.oHelper.AssertFalse()
        """
        self.__webapp.AssertFalse(expected, scritp_message)

    def AssertTrue(self, expected=True, scritp_message=''):
        """
        Defines that the test case expects a True response to pass

        Usage:

        >>> #Instantiating the class
        >>> inst.oHelper = Webapp()
        >>> #Calling the method
        >>> inst.oHelper.AssertTrue()
        """
        self.__webapp.AssertTrue(expected, scritp_message)

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
        self.__webapp.ChangeEnvironment(date, group, branch, module)

    def ChangeUser(self, user, password, initial_program = "", date='', group='99', branch='01'):
        """
        Change the user.

        :param initial_program: The initial program to load. - **Default:** "" (previous initial_program)
        :type initial_program: str
        :param date: The date to fill on the environment screen. - **Default:** "" (previous date)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "previous date group"
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "previous branch"
        :type branch: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ChangeUser("userTest", "a", "SIGAFAT", "18/08/2018", "T1", "D MG 01 ")
        >>> #------------------------------------------------------------------------
        >>> # Calling the method:
        >>> oHelper.ChangeUser(user="user08", password="8" )
        >>> #------------------------------------------------------------------------
        """
        self.__webapp.ChangeUser(user, password, initial_program, date, group, branch)

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
        :param input_field: False if the desired field is not an input type .
        :type input_field: bool
        :param direction: Desired direction to search for the element, currently accepts right and down.
        :type direction: str

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
        self.__webapp.CheckResult(field, user_value, grid, line, grid_number, name_attr, input_field, direction)

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
        self.__webapp.CheckView(text, element_type)

    def ClickBox(self, fields, contents_list="", select_all=False, grid_number=1, itens=False):
        """
        Clicks on Checkbox elements of a grid.

        :param field: Comma divided string with values that must be checked, combine with content_list.
        :type field: str
        :param content_list: Comma divided string with values that must be checked. - **Default:** "" (empty string)
        :type content_list: str
        :param select_all: Boolean if all options should be selected. - **Default:** False
        :type select_all: bool
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param itens: Bool parameter that click in all itens based in the field and content reference.
        :type itens: bool

        Usage:

        >>> # Calling the method to select a specific checkbox:
        >>> oHelper.ClickBox("Branch", "D MG 01 ")
        >>> #--------------------------------------------------
        >>> # Calling the method to select multiple checkboxes:
        >>> oHelper.ClickBox("Branch", "D MG 01 , D RJ 02")
        >>> #--------------------------------------------------
        >>> # Calling the method to select all checkboxes:
        >>> oHelper.ClickBox("Branch", select_all=True)
        >>> #--------------------------------------------------
        >>> # Calling the method to performe click based in 2 fields and contens:
        >>> test_helper.ClickBox('Numero da SC, Item da SC', 'COM068, 0001')
        >>> #--------------------------------------------------
        >>> # Calling the method to click in all itens with this reference:
        >>> test_helper.ClickBox('Numero da SC', 'COM068', itens=True)
        """
        self.__webapp.ClickBox(fields, contents_list, select_all, grid_number, itens)

    def ClickFolder(self, item, position=1):
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
        self.__webapp.ClickFolder(item, position)

    def ClickGridCell(self, column, row=1, grid_number=1):
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
        self.__webapp.ClickGridCell(column, row, grid_number)

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
        self.__webapp.ClickGridHeader(column, column_name, grid_number)

    def ClickIcon(self, icon_text, position=1):
        """
        Clicks on an Icon button based on its tooltip text.

        :param icon_text: The tooltip text.
        :type icon_text: str
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickIcon("Add")
        >>> oHelper.ClickIcon("Edit")
        """
        self.__webapp.ClickIcon(icon_text, position)

    def ClickCheckBox(self, label_box_name, position=1):
        """
        Clicks on a Label in box on the screen.

        :param label_box_name: The label box name
        :type label_box_name: str
        :param position: index label box on interface
        :type position: int

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickCheckBox("Search",1)
        """
        self.__webapp.ClickCheckBox(label_box_name,position)

    def ClickLabel(self, label_name):
        """
        Clicks on a Label on the screen.

        :param label_name: The label name
        :type label_name: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickLabel("Search")
        """
        self.__webapp.ClickLabel(label_name)

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
        return self.__webapp.GetValue(field, grid, line, grid_number)

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
        self.__webapp.LoadGrid()

    def LogOff(self):
        """
        Logs out of the Protheus Webapp.
        
        .. note::
            Do not use this method in any routine. Use on home screen.

        Usage:

        >>> # Calling the method.
        >>> oHelper.LogOff()
        """
        self.__webapp.LogOff()

    def Finish(self):
        """
        Exit the Protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.Finish()
        """
        self.__webapp.Finish()

    def MessageBoxClick(self, button_text):
        """
        Clicks on desired button inside a Messagebox element.

        :param button_text: Desired button to click.
        :type button_text: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.MessageBoxClick("Ok")
        """
        self.__webapp.MessageBoxClick(button_text)

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
        self.__webapp.Program(program_name)

    def RestoreParameters(self):
        """
        Restores parameters to previous value in CFG screen. Should be used after a **SetParameters** call.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        self.__webapp.RestoreParameters()

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
        self.__webapp.ScrollGrid(column, match_value, grid_number)

    def Screenshot(self, filename):
        """
        Takes a screenshot and saves on the screenshot folder defined in config.

        :param filename: The name of the screenshot file.
        :type: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Screenshot(filename="myscreenshot")
        """
        self.__webapp.take_screenshot(filename)

    def F3(self, field, name_attr=False,send_key=False):
        """
        Do the standard query(F3)
        
        this method:

            1.Search the field
            2.Search icon "lookup"
            3.Click()

        :param term: The term that must be searched.
        :type  term: str
        :param name_attr: True: searchs element by name.
        :type  name_attr: bool
        :param send_key: True: try open standard search field send key F3.
        :type send_key: bool

        Usage:

        >>> # To search using a label name:
        >>> oHelper.F3("Cód")
        >>> #------------------------------------------------------------------------
        >>> # To search using the name of input:
        >>> oHelper.F3(field='A1_EST',name_attr=True)
        >>> #------------------------------------------------------------------------
        >>> # To search using the name of input and do action with a key:
        >>> oHelper.F3(field='A1_EST',name_attr=True,send_key=True)
        """
        self.__webapp.standard_search_field( field, name_attr, send_key )
    
    def SetupTSS(self, initial_program="", environment=""):
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
        self.__webapp.SetupTSS(initial_program, environment)

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
        :param column: The search column to be chosen on the search dropdown. - **Default:** None
        :type column: str

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
        >>> oHelper.SearchBrowse("D MG 001", identifier="Products")
        >>> #------------------------------------------------------------------------
        >>> # To search using an index instead of name for the search key:
        >>> oHelper.SearchBrowse("D MG 001", key=2, index=True)
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen column:
        >>> oHelper.SearchBrowse("D MG 001", column="Nome")
        >>> #------------------------------------------------------------------------
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen columns:
        >>> oHelper.SearchBrowse("D MG 001", column="Nome, Filial*, ColumnX, AnotherColumnY")
        >>> #------------------------------------------------------------------------
        """
        self.__webapp.SearchBrowse(term, key, identifier, index, column)

    def SetBranch(self, branch):
        """
        Chooses the branch on the branch selection screen.

        :param branch: The branch that would be chosen.
        :type branch: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetBranch("D MG 01 ")
        """
        self.__webapp.SetBranch(branch)

    def SetButton(self, button, sub_item="", position=1, check_error=True):
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
        """
        self.__webapp.SetButton(button, sub_item, position, check_error=check_error)

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
        self.__webapp.SetFilePath(value, button)

    def SetFocus(self, field, grid_cell=False, row_number=1, position=1):
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
        """
        self.__webapp.SetFocus(field, grid_cell, row_number, position)

    def SetKey(self, key, grid=False, grid_number=1,additional_key="", wait_show = "", step = 3): 
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
        >>> # Calling the method when you expected new window or text appears on the screen:
        >>> oHelper.SetKey( key = "F12", wait_show="Parametros", step = 3 )
        >>> #--------------------------------------
        >>> # Calling the method with special keys (using parameter additional_key):
        >>> oHelper.SetKey(key="CTRL", additional_key="A")
        """
        self.__webapp.SetKey(key, grid, grid_number,additional_key, wait_show, step)

    def SetLateralMenu(self, menuitens):
        """
        Navigates through the lateral menu using provided menu path.
        e.g. "MenuItem1 > MenuItem2 > MenuItem3"

        :param menu_itens: String with the path to the menu.
        :type menu_itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetLateralMenu("Updates > Registers > Products > Groups")
        """
        self.__webapp.SetLateralMenu(menuitens)

    def SetParameters(self):
        """
        Sets the parameters in CFG screen. The parameters must be passed with calls for **AddParameter** method.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        self.__webapp.SetParameters()

    def SetTabEDAPP(self, table_name):
        """
        Chooses the table on the generic query (EDAPP).

        :param table: The table that would be chosen.
        :type table: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetTabEDAPP("AAB")
        """
        self.__webapp.SetTabEDAPP(table_name)

    def SetValue(self, field, value, grid=False, grid_number=1, ignore_case=True, row=None, name_attr=False, position = 1, check_value=None):
        """
        Sets value of an input element.

        .. note::
            Attention don't use  position parameter with  grid parameter True.

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
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool
        :param check_value: Boolean ignore input check - **Default:** True
        :type name_attr: bool
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Calling method to input value on a field:
        >>> oHelper.SetValue("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field using by label name:
        >>> oHelper.SetValue("Codigo", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field using by an existing label name:
        >>> oHelper.SetValue(field = "Codigo", value = "000002", position = 2)
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
        >>> # Calling method to input value on a field that is a grid (2) *Will not attempt to verify the entered value. Run only once.* :
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2, check_value = False)
        >>> oHelper.LoadGrid()
        """
        self.__webapp.SetValue(field, value, grid, grid_number, ignore_case, row, name_attr, position, check_value)

    def Setup(self, initial_program,  date="", group="99", branch="01", module=""):
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

        Usage:

        >>> # Calling the method:
        >>> oHelper.Setup("SIGAFAT", "18/08/2018", "T1", "D MG 01 ")
        """
        self.__webapp.Setup(initial_program, date, group, branch, module)

    def SetTIRConfig(self, config_name, value):
        """
        Changes a value of a TIR internal config during runtime.

        This could be useful for TestCases that must use a different set of configs
        than the ones defined at **config.json**

        Available configs:

        - Url
        - Environment
        - User
        - Password
        - Language
        - DebugLog
        - TimeOut
        - InitialProgram
        - Routine
        - Date
        - Group
        - Branch
        - Module

        :param config_name: The config to be changed.
        :type config_name: str
        :param value: The value that would be set.
        :type value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetTIRConfig(config_name="date", value="30/10/2018")
        """
        self.__webapp.SetTIRConfig(config_name, value)

    def Start(self):
        """
        Opens the browser maximized and goes to defined URL.

        Usage:

        >>> # Calling the method:
        >>> oHelper.Start()
        """
        self.__webapp.Start()

    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Calling the method
        >>> inst.oHelper.TearDown()
        """
        self.__webapp.TearDown()

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
        self.__webapp.WaitFieldValue(field, expected_value)

    def WaitHide(self, string):
        """
        Search string that was sent and wait hide the elements.

        :param itens: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitHide("Processing")
        """
        self.__webapp.WaitHide(string)

    def WaitProcessing(self, string):
        """
        Uses WaitShow and WaitHide to Wait a Processing screen

        :param string: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitProcessing("Processing")
        """
        self.__webapp.WaitProcessing(string)

    def WaitShow(self, string):
        """
        Search string that was sent and wait show the elements.

        :param itens: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitShow("Processing")
        """
        self.__webapp.WaitShow(string)

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
        self.__webapp.ClickTree(treepath=treepath, right_click=right_click, position=position)

    def GridTree(self, column, treepath,  right_click=False):
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
        self.__webapp.GridTree(column, treepath, right_click)
        
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

        return self.__webapp.GetText(string_left, string_right)
    
    def CheckHelp(self, text="", button="", text_help="", text_problem="", text_solution="", verbosity=False):
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

        return self.__webapp.CheckHelp(text, button, text_help, text_problem, text_solution, verbosity)

    def ClickMenuPopUpItem(self, text, right_click=False, position = 1):
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
        return self.__webapp.ClickMenuPopUpItem(text, right_click, position = position)

    def GetRelease(self):
        """
        Get the current release from Protheus.

        :return: The current release from Protheus.
        :type: str
        
        Usage:

        >>> # Calling the method:
        >>> oHelper.get_release()
        >>> # Conditional with method:
        >>> # Situation: Have a input that only appears in release greater than or equal to 12.1.027
        >>> if self.oHelper.get_release() >= '12.1.027':
        >>>     self.oHelper.SetValue('AK1_CODIGO', 'codigo_CT001')
        """

        return self.__webapp.get_release()
    
    def ClickListBox(self, text):
        """
        Clicks on Item based in a text in a window tlistbox

        :param text: Text in windows to be clicked.
        :type text: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.ClickListBox("text")
        """
        
        return self.__webapp.ClickListBox(text)

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
        self.__webapp.ClickImage(img_name,double_click)

    def ProgramScreen(self, initial_program=""):
        """
        Fills the first screen of Protheus with the first program to run.
        :param initial_program: The initial program to load
        :type initial_program: str
        Usage:
        >>> # Calling the method:
        >>> self.ProgramScreen("SIGAADV")
        """
        self.__webapp.program_screen(initial_program, coverage=self.coverage)
    
    def OpenCSV(self, csv_file='', delimiter=';', column=None, header=None, filter_column=None, filter_value=''):
        """
        Returns a dictionary when the file has a header in another way returns a list
        The folder must be entered in the CSVPath parameter in the config.json.

        .. note::
            This method return data as a string if necessary use some method to convert data like int().

        >>> config.json
        >>> "CSVPath" : "C:\\temp"

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
        :param filter_data: If you want filter a value by column, this parameter need to be a True value
        :type filter_data: bool

        >>> # Call the method:
        >>> file_csv = self.oHelper.OpenCSV(delimiter=";", csv_file="no_header.csv")

        >>> file_csv_no_header_column = self.oHelper.OpenCSV(column=0, delimiter=";", csv_file="no_header_column.csv")

        >>> file_csv_column = self.oHelper.OpenCSV(column='CAMPO', delimiter=";", csv_file="header_column.csv", header=True)

        >>> file_csv_pipe = self.oHelper.OpenCSV(delimiter="|", csv_file="pipe_no_header.csv")

        >>> file_csv_header = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True)

        >>> file_csv_header_column = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True)

        >>> file_csv_header_pipe = self.oHelper.OpenCSV(delimiter="|", csv_file="pipe_header.csv", header=True)

        >>> file_csv_header_filter = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True, filter_column='CAMPO', filter_value='A00_FILIAL')

        >>> file_csv _no_header_filter = self.oHelper.OpenCSV(delimiter=";", csv_file="no_header.csv", filter_column=0, filter_value='A00_FILIAL')
        """
        return self.__webapp.open_csv(csv_file, delimiter, column, header, filter_column, filter_value)

    def StartDB(self):
        """

        :return: connection object
        Usage:

        >>> # Call the method:
        >>> self.oHelper.StartDB()
        """
        return self.__database.connect_database()

    def StopDB(self, connection):
        """

        :param connection: connection object
        :type param: object
        Usage:

        >>> # Call the method:
        >>> self.oHelper.StopDB(connection)
        """
        self.__database.connect_database()

    def QueryExecute(self, query, database_driver="", dbq_oracle_server="", database_server="", database_port=1521, database_name="", database_user="", database_password=""):
        """
        Return a dictionary if the query statement is a SELECT otherwise print a number of row 
        affected in case of INSERT|UPDATE|DELETE statement.

        .. note::  
            Default Database information is in config.json another way is possible put this in the QueryExecute method parameters:
            Parameters:
            "DBDriver": "",
            "DBServer": "",
            "DBName": "",
            "DBUser": "",
            "DBPassword": ""

        .. note::        
            Must be used an ANSI default SQL statement.

        .. note::        
            dbq_oracle_server parameter is necessary only for Oracle connection.
        
        :param query: ANSI SQL estatement query
        :type query: str
        :param database_driver: ODBC Driver database name
        :type database_driver: str
        :param dbq_oracle_server: Only for Oracle: DBQ format:Host:Port/oracle instance
        :type dbq_oracle_server: str
        :param database_server: Database Server Name
        :type database_server: str
        :param database_port: Database port default port=1521
        :type database_port: int
        :param database_name: Database Name
        :type database_name: str
        :param database_user: User Database Name
        :type database_user: str
        :param database_password: Database password
        :type database_password: str

        Usage:

        >>> # Call the method:
        >>> self.oHelper.QueryExecute("SELECT * FROM SA1T10")
        >>> self.oHelper.QueryExecute("SELECT * FROM SA1T10", database_driver="DRIVER_ODBC_NAME", database_server="SERVER_NAME", database_name="DATABASE_NAME", database_user="sa", database_password="123456")
        >>> # Oracle Example:
        >>> self.oHelper.QueryExecute("SELECT * FROM SA1T10", database_driver="Oracle in OraClient19Home1", dbq_oracle_server="Host:Port/oracle instance", database_server="SERVER_NAME", database_name="DATABASE_NAME", database_user="sa", database_password="123456")
        """
        return self.__database.query_execute(query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password)

    def GetConfigValue(self, json_key):
        """

        :param json_key: Json Key in config.json
        :type json_key: str
        :return: Json Key item in config.json
        """
        return self.__webapp.get_config_value(json_key)

    def ReportComparison(self, base_file="", current_file=""):
        """

        Compare two reports files and if exists show the difference between then if exists.

        .. warning::
            Important to use BaseLine_Spool key in config.json to work appropriately. Baseline_Spool is the path of report spool in yout environment

        .. warning::
            Some words are changed to this pattern below:

            'Emissão: 01-01-2015'
            'Emision: 01-01-2015'
            'DT.Ref.: 01-01-2015'
            'Fc.Ref.: 01-01-2015'
            'Hora...: 00:00:00'
            'Hora Término: 00:00:00'
            '/' to '@'

            Only .xml

            'encoding=""'
            '"DateTime">2015-01-01T00:00:00'
            'ss:Width="100"'

        :param base_file: Base file that reflects the expected. If doesn't exist make a copy of auto and then rename to base
        :type base_file: str
        :param current_file: Current file recently impressed, this file is use to generate file_auto automatically.
        :type current_file: str

        Usage:

        >>> # File example:
        >>> # acda080rbase.##r
        >>> # acda080rauto.##r
        >>> # Calling the method:
        >>> self.oHelper.ReportComparison(base_file="acda080rbase.##r", current_file="acda080rauto.##r")
        """

        return self.__webapp.report_comparison(base_file, current_file)

    def GetGrid(self, grid_number=1, grid_element = None):
        """
        Gets a grid BeautifulSoup object from the screen.

        :param grid_number: The number of the grid on the screen.
        :type: int
        :param grid_element: Grid class name in HTML ex: ".tgrid".
        :type: str
        :return: Grid BeautifulSoup object
        :rtype: BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> my_grid = self.get_grid()
        """
        
        return self.__webapp.get_grid_content(grid_number, grid_element)

    def LengthGridLines(self, grid):
        """
        Returns the length of the grid.
        :return:
        """

        return self.__webapp.LengthGridLines(grid)

class Apw():

    def __init__(self, config_path=""):

        self.__Apw = ApwInternal()

    def CheckBrowse(self, valores):

        self.__Apw.CheckBrowse(valores)


    def CheckLink(self, Link):

        self.__Apw.CheckLink(Link)


    def ClickLink(self, Link):

        self.__Apw.ClickLink(Link)

    def ClickMenu(self, caminho):

        self.__Apw.ClickMenu(caminho)


    def CloseAlert(self):

        self.__Apw.CloseAlert()

    def CloseWindow(self):

        self.__Apw.CloseWindow()

    def EndCase(self):

        self.__Apw.EndCase()

    def SetButton(self, button, type=''):

        self.__Apw.SetButton(button, type)

    def SetGrid(self, btnFunc="Incluir"):

        self.__Apw.SetGrid(btnFunc)

    def SelectBrowse(self, valores, opcao='', duplo=True):

        self.__Apw.SelectBrowse(valores, opcao, duplo)

    def Setup(self, lblUser="Usuário", lblPassword="Senha", btnAccess="Acessar Portal"):

        self.__Apw.Setup(lblUser, lblPassword, btnAccess)

    def SwitchModal(self, opcao, frame=''):

        self.__Apw.SwitchModal(opcao, frame)

    def SwitchWindow(self, exit=False):

        self.__Apw.SwitchWindow(exit)

    def SearchValue(self, busca, valor, grid=False, btnOk='ok', btnFind='buscar', searchparam='Pesquisar'):

        self.__Apw.SearchValue(busca, valor, grid, btnOk, btnFind, searchparam)

    def SetValue(self, campo, valor, grid=False, linha=0, chknewline=False, disabled=False):

        self.__Apw.SetValue(campo, valor, grid, linha, chknewline, disabled)

    def WaitModal(self, text, opcao="title"):
        self.__Apw.WaitModal(text, opcao)
