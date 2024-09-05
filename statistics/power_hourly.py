from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import argparse

from util.timestamps import get_month_timestamps

load_dotenv()

bucket = os.getenv('INFLUX_BUCKET')

# Create the InfluxDB client
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=os.getenv('INFLUX_TOKEN_WRITE'), org=os.getenv('INFLUX_ORG'))

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('--year', type=int, help="Year to retrieve data for")
    parser.add_argument('--month', type=int, help="Month to retrieve data for")
    parser.add_argument('--start_month', type=int, help="Month to start retrieving data from")
    parser.add_argument('--end_month', type=int, help="Month to stop retrieving data at")

    args = parser.parse_args()

    year = args.year

    if(args.month):
        r = range(args.month, args.month+1)
    else:
        r = range(args.start_month, args.end_month)
    for month in r:
        df = get_averages_monthly(year, month)
        df.to_csv(f"~/Documents/GitHub/energy_scripts/data/power_averages_{year}_{month}.csv", encoding='utf-8')

def get_averages_monthly(year, month):
    start_time, end_time = get_month_timestamps(year, month)
    return get_averages(start_time, end_time)

def get_averages(start_time, end_time):

    exec_start_time = datetime.now()

    # Time range for the query (last month)

    #end_time = datetime.now()
    #start_time = end_time - timedelta(days=30)
    #start_time = end_time - timedelta(days=1)

    print(f"start: {start_time}, end: {end_time}")

    # Query to get the data
    query = f'''
    from(bucket:"{bucket}")
    |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
    |> filter(fn: (r) => r["_measurement"] == "SENEC")
    |> filter(fn: (r) => r["_field"] == "grid_power_plus" or r["_field"] == "grid_power_minus" or r["_field"] == "house_power" or r["_field"] == "inverter_power")
    '''

    # Execute the query
    result = client.query_api().query(query=query)

    #local_timezone = 'US/Eastern'
    #local_result = convert_influxdb_to_local_timezone(result, local_timezone)

    # Process the results
    data = []
    for table in result:
        for record in table.records:
            data.append({
                #'time': datetime_from_utc_to_local(record.get_time()),
                'time': record.get_time(),
                'field': record.get_field(),
                'value': record.get_value()
            })

    # Convert to DataFrame
    df = pd.DataFrame(data)

    df_bytes = df.memory_usage(index=True, deep=True).sum()
    #print(f"df size: {df_bytes/1000:2f} kB")
    #print(df)

    # Convert time to datetime and set as index
    #df['time'] = pd.to_datetime(df['time'])

    # convert timezone, this solution seems to be a bit slower than the following one
    #df['time'] = pd.to_datetime(df['time'], utc=True).map(lambda x: x.tz_convert('Europe/Vienna'))

    # this solution is a bit faster
    import pytz
    local_timezone = pytz.timezone('Europe/Vienna')
    df['time'] = df['time'].dt.tz_convert(local_timezone)


    df.set_index('time', inplace=True)

    # Pivot the data to have fields as columns
    df_pivoted = df.pivot(columns='field', values='value')

    #Resample to hourly data and calculate mean
    df_hourly = df_pivoted.resample('H').mean()

    #print(df_hourly)

    # Group by hour of day and calculate mean
    df_hour_of_day = df_hourly.groupby(df_hourly.index.hour).mean()

    # Rename the index for clarity
    df_hour_of_day.index.name = 'Hour'

    # Function to format hour range
    def format_hour_range(hour):
        start = f"{hour:02d}:00"
        end = f"{(hour + 1) % 24:02d}:00"
        return f"{start} - {end}"

    # Apply the formatting to the index
    df_hour_of_day.index = df_hour_of_day.index.map(format_hour_range)

    # round values
    df_hour_of_day = df_hour_of_day.round()

    print("Average power usage for each hour interval over the last month:")
    print(df_hour_of_day)

    # Calculate total energy for each category
    total_consumed = df_hourly['house_power'].sum()
    total_fed_in = df_hourly['grid_power_minus'].sum()
    total_drawn = df_hourly['grid_power_plus'].sum()
    total_generated = df_hourly['inverter_power'].sum()

    print(f"\nTotal energy consumed by the household: {total_consumed/1000:.2f} kWh")
    print(f"Total energy fed back to the grid: {total_fed_in/1000:.2f} kWh")
    print(f"Total energy drawn from the grid: {total_drawn/1000:.2f} kWh")
    print(f"Total energy generated: {total_generated/1000:.2f} kWh")

    exec_end_time = datetime.now()

    exec_time = exec_end_time - exec_start_time
    print(f"execution time {exec_time}")

    return df_hour_of_day

if __name__ == "__main__":
    main()