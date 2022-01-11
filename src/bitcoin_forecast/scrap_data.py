import re
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .utils import (
    get_feature_header_map,
    get_from_bitinfocharts,
    get_ticker_list,
    get_url_header,
)


def fetch_data(request):
    url = "https://www.investing.com/instruments/HistoricalDataAjax"
    urlheader = get_url_header()

    req = requests.post(url, data=request, headers=urlheader)
    soup = BeautifulSoup(req.content, "html.parser")

    table = soup.find("table", id="curr_table")
    text = table.tbody.find_all("td")[1].text
    return float(re.sub(r"[^\d.]", "", text))


def get_from_investing(payload):

    map_dict = get_feature_header_map()
    ticker_list = get_ticker_list()

    start_date = datetime.now().strftime("%m/%d/%Y")
    end_date = datetime.now().strftime("%m/%d/%Y")
    for ticker in ticker_list:
        # data format: month/date/year
        header_str = f"""{ticker}
        st_date: {start_date}
        end_date: {end_date}
        interval_sec: Daily
        sort_col: date
        sort_ord: DESC
        action: historical_data"""

        req_payload = dict([[item.strip() for item in row.split(": ")] for row in header_str.split("\n")])

        try:
            payload[map_dict[req_payload["header"]]] = fetch_data(req_payload)
        except IndexError:  # when US indices data is not available for today, then take previous business day price
            last_bus_day = datetime.today()
            if date.weekday(last_bus_day) == 5:  # if it's Saturday
                last_bus_day = last_bus_day - timedelta(days=1)  # then make it Friday
            elif date.weekday(last_bus_day) == 6:  # if it's Sunday
                last_bus_day = last_bus_day - timedelta(days=2)  # then make it Friday
            else:  # if data is not for today
                last_bus_day = last_bus_day - timedelta(days=1)

            req_payload["st_date"] = last_bus_day.strftime("%m/%d/%Y")
            payload[map_dict[req_payload["header"]]] = fetch_data(req_payload)

    assert "price_usd" in payload.keys()

    payload["price_bse"] = payload["price_bse"] / payload["price_usd"]
    payload["price_nfty"] = payload["price_nfty"] / payload["price_usd"]
    #     del payload['price_usd']
    return payload


def convert_payload_to_df(payload):
    payload_df = pd.DataFrame([payload])
    payload_df["Date"] = pd.to_datetime(payload_df["Date"])

    payload_df["year"] = payload_df["Date"].dt.year
    payload_df["month"] = payload_df["Date"].dt.month
    payload_df["day"] = payload_df["Date"].dt.day

    payload_df["dayofweek_num"] = payload_df["Date"].dt.dayofweek

    return payload_df


def get_today_data(payload={}):
    payload1 = get_from_bitinfocharts(payload)
    payload2 = get_from_investing(payload)

    payload.update(payload1)
    payload.update(payload2)

    df = convert_payload_to_df(payload)
    return df


if __name__ == "__main__":
    payload_df = get_today_data()
    print(payload_df)
