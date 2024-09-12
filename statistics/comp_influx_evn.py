from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import argparse
from calendar import monthrange
import pytz

from util.timestamps import get_month_timestamps
from  util.evn.evn_wrapper import EVNAccount

def to_utc(date):
    # Localize the datetime (tell Python this datetime is in your local timezone)
    local_datetime = local_tz.localize(date)

    # Convert to UTC
    return local_datetime.astimezone(pytz.UTC)

load_dotenv()

bucket = os.getenv('INFLUX_BUCKET')

# Create the InfluxDB client
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=os.getenv('INFLUX_TOKEN_WRITE'), org=os.getenv('INFLUX_ORG'))

local_tz = pytz.timezone('Europe/Vienna') 

parser = argparse.ArgumentParser()

parser.add_argument('--user')
parser.add_argument('--year', type=int, help="Year to retrieve data for")
parser.add_argument('--month', type=int, help="Month to retrieve data for")
parser.add_argument('--start_month', type=int, help="Month to start retrieving data from", default=1)
parser.add_argument('--end_month', type=int, help="Month to stop retrieving data at")
parser.add_argument('--end_day', type=int, help="Day to stop retrieving data at")
parser.add_argument('--append', action="store_true")

args = parser.parse_args()

evn = EVNAccount()
user = args.user

#authenticate to the smartmeter API
evn.authenticate(account_index=2, username=user)

year = args.year

if not args.append:
    # write header
    with open("comp_influx_evn.csv","w") as f:
        f.write("date, taken from grid - influx, taken from grid - evn, difference factor, fed into grid - influx, fed into grid - evn, difference factor\n")

if(args.month):
    r = range(args.month, args.month+1)
else:
    r = range(args.start_month, args.end_month)
for month in r:
    num_days_in_month = monthrange(year, month)[1]

    # date, taken from grid - influx, taken from grid - evn, difference, fed into grid - influx, fed into grid - evn, difference
    data_len = args.end_day if args.end_day else num_days_in_month
    data = [{} for _ in range(data_len)]

    evn.switch_account(account_index=2)

    def fetch_data(day, field):
        date = f"{year}-{month}-{day}"
        start_datetime = to_utc(datetime(year, month, day, 0, 0, 0))
        end_datetime = (start_datetime + timedelta(days=1))

        index = day-1
        print(f"{date} {field}")
        data[index]["date"] = date

        query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')})
          |> filter(fn: (r) => r._measurement == "SENEC" and r._field == "{field}")
          |> integral(unit: 1h)
        '''

        result = client.query_api().query(query=query)
        try:
            data[index][f"{field}_influx"] = round(result[0].records[0].get_value() / 1000, 2)
        except Exception as e:
            print(f"Error at fetching from influxdb: {e} result: {result}")
            data[index][f"{field}_influx"] = "ERROR"

        try:
            data[index][f"{field}_evn"] = evn.get_cumulative_consumption_per_day(date)
        except Exception as e:
            print(f"Error at fetching from evn: {e}")
            data[index][f"{field}_evn"] = "ERROR"

        try:
            data[index][f"{field}_factor"] = round(data[index][f"{field}_influx"]  / data[index][f"{field}_evn"] ,2)
        except Exception as e:
            print(f"Error at calculating factor: {e}")
            data[index][f"{field}_factor"] = "ERROR"

    if(args.end_day):
        r = range(1, args.end_day + 1)
    else:
        r = range(1,num_days_in_month + 1)

    # taken from grid
    for day in r:
        fetch_data(day, "grid_power_plus")
    
    evn.switch_account(account_index=3)

    # grid feed in
    for day in r:
        fetch_data(day, "grid_power_minus")

    with open("comp_influx_evn.csv","a") as f:
        for d in data:
            f.write(f'{d["date"]},{d["grid_power_plus_influx"]},{d["grid_power_plus_evn"]},{d["grid_power_plus_factor"]},{d["grid_power_minus_influx"]},{d["grid_power_minus_evn"]},{d["grid_power_minus_factor"]}\n')