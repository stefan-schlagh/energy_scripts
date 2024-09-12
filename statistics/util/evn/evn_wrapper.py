import requests
import pickle
import os
import json
from util.evn.custom_print import print_status_message as print

# base code taken from here @A.E.I.O.U. https://www.lteforum.at/mobilfunk/evn-smartmeter-api-wrapper-influx-importer-grafana-dashboard.21319/

class EVNAccount:
    def __init__(self, accountID=None, Smartmeter=None, Electricity=None, Gas=None, Communicative=None, Optin=None, Active=None, metering_point_id=None,session=None):
        self._accountID = accountID
        self._Smartmeter = Smartmeter
        self._Electricity = Electricity
        self._Gas = Gas
        self._Communicative = Communicative
        self._Optin = Optin
        self._Active = Active
        self._metering_point_id = metering_point_id
        self._session=session

    # Sessions
    def get_Session(self):
        return self._session
    def set_accountID(self, session):
        self._session = session

    # accountID
    def get_accountID(self):
        return self._accountID
    def set_accountID(self, accountID):
        self._accountID = accountID

    # Smartmeter
    def get_Smartmeter(self):
        return self._Smartmeter
    def set_Smartmeter(self, Smartmeter):
        self._Smartmeter = Smartmeter

    # Electricity
    def get_Electricity(self):
        return self._Electricity
    def set_Electricity(self, Electricity):
        self._Electricity = Electricity

    # Gas
    def get_Gas(self):
        return self._Gas
    def set_Gas(self, Gas):
        self._Gas = Gas

    # Communicative
    def get_Communicative(self):
        return self._Communicative
    def set_Communicative(self, Communicative):
        self._Communicative = Communicative

    # Optin
    def get_Optin(self):
        return self._Optin
    def set_Optin(self, Optin):
        self._Optin = Optin

    # Active
    def get_Active(self):
        return self._Active
    def set_Active(self, Active):
        self._Active = Active

    # metering_point_id
    def get_metering_point_id(self):
        return self._metering_point_id
    def set_metering_point_id(self, metering_point_id):
        self._metering_point_id = metering_point_id

    # Retrieve User Data
    def retrieve_user_data(self, session, account_index=None):

        userDetails = session.get('https://smartmeter.netz-noe.at/orchestration/User/GetBasicInfo')

        accountingDetails = session.get('https://smartmeter.netz-noe.at/orchestration/User/GetAccountIdByBussinespartnerId?context=2')
        self._all_accountingDetails = [EVNAccountDetails(x) for x in accountingDetails.json()]
        
        if account_index == None:
            account_index = self.select_account_index()

        self._accountingDetails = self._all_accountingDetails[account_index]
        self._accountingDetails.get_metering_point_id(session)
        
        self._session=session
    
    def switch_account(self, account_index):
        if account_index == None:
            account_index = self.select_account_index()

        self._accountingDetails = self._all_accountingDetails[account_index]
        self._accountingDetails.get_metering_point_id(self._session)
    
    def select_account_index(self):
        print("accounts available for this user:")

        for i in range(len(self._all_accountingDetails)):
            print(f"[{i+1}]: \t {self._all_accountingDetails[i]}")
        
        return input_account_detail(len(self._all_accountingDetails))

    #authenticate
    def authenticate(self, username, account_index=None, password=None, session_file='evn_session.pkl'):
        session = None

        # Check if a cached session exists
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session = pickle.load(f)
                # Check if the cached session is still valid
                print("Check if stored Session is valid...", 'info')
                response = session.get('https://smartmeter.netz-noe.at/orchestration/User/GetBasicInfo')
                if response.status_code != 200:
                    session = None
                    print("Stored session is not valid", 'error')
                    print("Reauthenticating...", 'info')
                else:
                    print("Stored session is  valid", 'success')
        
        # If a valid session doesn't exist, authenticate the user
        if session is None:

            if not password:
                from getpass import getpass
                password = getpass()

            session = requests.Session()
            auth_url = 'https://smartmeter.netz-noe.at/orchestration/Authentication/Login'
            auth_data = {'user': username, 'pwd': password}
            response = session.post(auth_url, json=auth_data)
            if response.status_code != 200:
                print("Username or Password not correct", 'error')
                raise Exception('Failed to authenticate user')
            else:
                print("Successfull Authenticated", 'success')
            # Save the session to disk
            with open(session_file, 'wb') as f:
                pickle.dump(session, f)
        
        #retrieve user data after successul authentication
        self.retrieve_user_data(session, account_index)
        return self

    
    
    def get_consumption_per_day(self, day):
        """
        Get the consumption per day for the given metering point ID and day.
        Values are usually quarter-hourly

        Args:
            day (str): The day to get the consumption data for, in the format 'YYYY-MM-DD'.

        Returns:
            A list of tuples containing the peak demand times and corresponding metered values.
        """
        try:
            response = self._session.get(
                "https://smartmeter.netz-noe.at/orchestration/ConsumptionRecord/Day",
                params={"meterId": self._accountingDetails._metering_point_id, "day": day},
            )
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error status code
            data = response.json()[0]
            consumption_per_day = list(zip(data["peakDemandTimes"], data["meteredValues"]))
            return consumption_per_day
        except (requests.exceptions.RequestException, ValueError) as error:
            print(f"An error occurred: {error}")
            return []

    def get_cumulative_consumption_per_day(self, day):
        data = self.get_consumption_per_day(day)
        return round(sum([x[1] for x in data if x[1] != None]),2)
    
    def get_consumption_for_month(self, year, month):
        """
        Get the consumption for the given metering point ID and month.

        Args:
            year (int): The year to get the consumption data for.
            month (int): The month to get the consumption data for.

        Returns:
            A list of tuples containing the peak demand times and corresponding metered values.
        """
        try:
            response = self._session.get(
                "https://smartmeter.netz-noe.at/orchestration/ConsumptionRecord/Month",
                params={"meterId": self._accountingDetails._metering_point_id, "year": year, "month": month},
            )
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error status code
            data = response.json()[0]
            consumption_for_month = list(zip(data["peakDemandTimes"], data["meteredValues"]))
            return consumption_for_month
        except (requests.exceptions.RequestException, ValueError) as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_consumption_for_year(self, year):
        """
        Get the consumption for the given metering point ID and year.

        Args:
            year (int): The year to get the consumption data for.

        Returns:
            A list of tuples containing the peak demand times and corresponding metered values.
        """
        try:
            response = self._session.get(
                "https://smartmeter.netz-noe.at/orchestration/ConsumptionRecord/Year",
                params={"meterId": self._accountingDetails._metering_point_id, "year": year},
            )
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error status code
            data = response.json()[0]
            consumption_for_year = list(zip(data["peakDemandTimes"], data["values"]))
            return consumption_for_year
        except (requests.exceptions.RequestException, ValueError) as error:
            print(f"An error occurred: {error}")
            return []

class EVNAccountDetails():
    def __init__(self, data):
        self._accountID = data['accountId']
        self._facilityDescription = data['facilityDescription']
        self._Smartmeter = data['hasSmartMeter']
        self._Electricity = data['hasElectricity']
        self._Gas = data['hasGas']
        self._Communicative = data['hasCommunicative']
        self._Optin = data['hasOptIn']
        self._Active = data['hasActive']
        self._address = data['address']
        self._metering_point_id = None

    def __str__(self) -> str:
        return f"{self._facilityDescription} {self.__addr_to_str__()}"

    def __addr_to_str__(self) -> str:
        a = self._address
        return f"{a['plz']} {a['ort']} {a['strasse']} {a['hausnummer']}"

    def get_metering_point_id(self, session):
        meterDetails = session.get(
            f'https://smartmeter.netz-noe.at/orchestration/User/GetMeteringPointByAccountId?accountId={self._accountID}&context=2')
        
        self._metering_point_id = meterDetails.json()[0]['meteringPointId']

def input_account_detail(num_options):
    options = [str(x) for x in range(1, num_options + 1)]
    while True:
        user_input = input(f"Enter a number in the range (1 - {num_options}): ")
        if user_input in options:
            break
        else:
            print(f"Invalid input. Please enter a number in the range (1 - {num_options})")
    return int(user_input) - 1