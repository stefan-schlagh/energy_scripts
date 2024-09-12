import argparse
from  util.evn.evn_wrapper import EVNAccount

parser = argparse.ArgumentParser()

parser.add_argument('--user')
parser.add_argument('--year', type=int, help="Year to retrieve data for")
parser.add_argument('--end_year', type=int)
parser.add_argument('--month', type=int, help="Month to retrieve data for")
parser.add_argument('--end_month', type=int)
parser.add_argument('--day', type=int, help="Day to retrieve data for")

parser.add_argument('--csv', help="Export to csv")

args = parser.parse_args()

evn = EVNAccount()
user = args.user

#authenticate to the smartmeter API
evn.authenticate(username=user)

def write_tuples(d, fn):
    with open(fn, "a") as f:
        for t in d:
            if(t[0] != None or t[1] != None):
                f.write(f"{t[0]}, {t[1]}\n")

if(args.day):
    day_ = f"{args.year}-{args.month}-{args.day}"

    d = evn.get_consumption_per_day(day_)

    if(args.csv):
        with open(args.csv, "w") as f:
            f.write("Time, cumulative Value\n")

    write_tuples(d, args.csv)

elif(args.month):
    if(args.csv):
        with open(args.csv, "w") as f:
            f.write("Day, cumulative Value\n")

    if(args.end_month):
        for m in range(args.month, args.end_month +1):
            d = evn.get_consumption_for_month(args.year, m)

            if(args.csv):
                write_tuples(d, args.csv)
    else:
        d = evn.get_consumption_for_month(args.year, args.month)
        if(args.csv):
            write_tuples(d, args.csv)

elif(args.year):
    if(args.csv):
        with open(args.csv, "w") as f:
            f.write("Month, cumulative Value\n")

    if(args.end_year):
         for y in range(args.year, args.end_year + 1):
            d = evn.get_consumption_for_year(y)

            if(args.csv):
                write_tuples(d, args.csv)
    else:
        d = evn.get_consumption_for_year(args.year)
        if(args.csv):
            write_tuples(d, args.csv)