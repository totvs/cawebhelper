from tir.technologies.core.base import Base
from tir.technologies.webapp_internal import WebappInternal
import pandas as pd
import pyodbc
import re
from tir.technologies.core.logging_config import logger


class BaseDatabase(Base):

    def __init__(self):
        super().__init__(autostart=False)
        self.webapp_internal = WebappInternal(autostart=False)
        self.restart_counter = self.webapp_internal.restart_counter

    def odbc_connect(self, database_driver="", dbq_oracle_server="", database_server="", database_port=1521, database_name="", database_user="", database_password=""):
        """
        :return:
        """
        connection = None
        
        database_driver = self.config.database_driver if not database_driver else database_driver
        database_server = self.config.database_server if not database_server else database_server
        database_port = self.config.database_port if not database_port else database_port
        database_name = self.config.database_name if not database_name else database_name
        database_user = self.config.database_user if not database_user else database_user
        database_password = self.config.database_password if not database_password else database_password
        dbq_oracle_server = self.config.dbq_oracle_server if not dbq_oracle_server else dbq_oracle_server

        self.check_pyodbc_drivers(database_driver)

        try:
            if dbq_oracle_server:
                connection = pyodbc.connect(f'DRIVER={database_driver};dbq={dbq_oracle_server};database={database_name};uid={database_user};pwd={database_password}')
            else:
                connection = pyodbc.connect(f'DRIVER={database_driver};server={database_server};port={database_port};database={database_name};uid={database_user};pwd={database_password}')
        except Exception as error:
            self.webapp_internal.restart_counter = 3
            self.webapp_internal.log_error(str(error))

        return connection

    def test_odbc_connection(self, connection):
        """
        :param connection:
        :return: cursor attribute if connection ok else return False
        """
        try:
            return connection.cursor()
        except:
            return False

    def connect_database(self, query="", database_driver="", dbq_oracle_server="", database_server="", database_port=1521, database_name="", database_user="", database_password=""):

        connection = self.odbc_connect(database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password)

        if self.test_odbc_connection(connection):
            logger().info('DataBase connection started')
        else:
            logger().info('DataBase connection is stopped')

        return connection

    def disconnect_database(self, connection):

        if not connection:
            connection = self.odbc_connect()

        cursor = self.test_odbc_connection(connection)
        if cursor:
            cursor.close()
            connection.close()
            if not self.test_odbc_connection(connection):
                logger().info('DataBase connection stopped')
        else:
            logger().info('DataBase connection already stopped')

    def check_pyodbc_drivers(self, driver_database):
        if not next(iter(list(filter(lambda x: x == driver_database, pyodbc.drivers()))), None):
            error_message = f"Driver: '{driver_database}' isn't a valid driver name!"
            self.webapp_internal.restart_counter = 3
            self.webapp_internal.log_error(error_message)

    def query_execute(self, query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password):
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
        connection = self.connect_database(query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password)
        
        if re.findall(r'^(SELECT)', query.upper()):
            df = pd.read_sql(sql=query, con=connection)
            return (df.to_dict())
        elif re.findall(r'^(UPDATE|DELETE|INSERT)', query.upper()):
            self.cursor_execute(query, connection)
        else:
            self.webapp_internal.log_error(f"Not a valid query in {query}")

    def cursor_execute(self, query, connection):
        cursor = connection.cursor()
        try:
            rowcount = cursor.execute(query).rowcount
        except Exception as error:
            self.webapp_internal.log_error(str(error))
        logger().info(f'{rowcount} row(s) affected')
        connection.commit()
