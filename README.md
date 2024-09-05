# statistics/power_hourly.py

this script creates an average of the power statistics for each hour of the day. It writes those results to a csv file.

it reads the data from an influxdb instance and is made to work with a [solectrus](https://solectrus.de/) installation.

TODO - add more options

# ui/powerdata_explorer.py

displays the data generated in power_hourly.py. Allows to select month and year