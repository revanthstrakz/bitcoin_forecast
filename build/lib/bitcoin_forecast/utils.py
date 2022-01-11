import re
from functools import reduce

import pandas as pd
import requests
from bs4 import BeautifulSoup

WINDOW_SIZE = 100


def get_ticker_list():
    ticker_list = """curr_id: 17940
    smlID: 2036382
    header: Nifty 50 Historical Data

    curr_id: 39929
    smlID: 2055486
    header: BSE Sensex 30 Historical Data

    curr_id: 169
    smlID: 2030170
    header: Dow Jones Industrial Average Historical Data

    curr_id: 166
    smlID: 2030167
    header: S&amp;P 500 Historical Data

    curr_id: 14958
    smlID: 2035302
    header: NASDAQ Composite Historical Data

    curr_id: 160
    smlID: 106815
    header: USD/INR Historical Data""".split(
        "\n\n"
    )

    return ticker_list


def get_from_bitinfocharts(payload):
    url = "https://bitinfocharts.com/bitcoin/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.find("td", id="tdid2").span.text
    payload["price_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid3").text
    payload["transactions_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("a", href="../comparison/bitcoin-size.html").parent.parent.find_all("td")[-1].text
    payload["size_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid5").span.text
    payload["sentinusd_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid15").abbr.text
    payload["difficulty_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid7").span.text
    payload["transactionvalue_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid25").a.text
    payload["tweets_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid20").text
    payload["activeaddresses_btc"] = float(re.sub(r"[^\d.]", "", text))

    text = soup.find("td", id="tdid2").small.text
    payload["Date"] = re.findall(r"([0-9]{4}-[0-9]{2}-[0-9]{2})", text)[0]
    return payload


def get_url_header():
    url_header = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    return url_header


def get_feature_header_map():
    map_dict = {
        "Nifty 50 Historical Data": "price_nfty",
        "BSE Sensex 30 Historical Data": "price_bse",
        "Dow Jones Industrial Average Historical Data": "price_dj",
        "S&amp;P 500 Historical Data": "price_snp",
        "NASDAQ Composite Historical Data": "price_nasq",
        "USD/INR Historical Data": "price_usd",
    }
    return map_dict


def parse_record(record):
    date = re.findall("([0-9]{4}/[0-9]{2}/[0-9]{2})", record)[0]
    value = re.findall(r"\,(.*?)\]", record)[0]
    return [date, value]


def get_meta_data():
    url = "https://bitinfocharts.com/comparison/bitcoin-price.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    soup = soup.find("div", {"id": "buttonsHDiv"}).find("select")

    # drop_down_list = []
    data = []
    _url = "https://bitinfocharts.com/comparison/{feature}.html"

    # get all available elements in dropdown list
    for tag in soup.find_all("option"):
        value = tag["value"]
        desc = tag.text
        full_url = _url.format(feature=value)
        if "top100cap" not in value:
            data.append([value, desc, full_url])

    meta_df = pd.DataFrame(data, columns=["short_id", "description", "url"])
    return meta_df


def get_bitinfocharts_data(meta_df):
    # fetch data
    df = pd.DataFrame(columns=["Date"])
    df["Date"] = pd.to_datetime(df["Date"])
    for _, row in meta_df.iterrows():
        response = requests.get(row["url"])
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.findAll("script")[4]
        script_text = script_tag.text

        pattern = re.compile(r'\[new Date\("\d{4}/\d{2}/\d{2}"\),\d*\w*\]')
        records = pattern.findall(script_text)

        transactions = []
        current_iteration = 0
        for record in records[::-1]:
            transactions.append(parse_record(record))
            current_iteration += 1
            if current_iteration == WINDOW_SIZE:
                break

        curr_df = pd.DataFrame(transactions, columns=["Date", row["short_id"].replace("-", "_")])
        curr_df["Date"] = pd.to_datetime(curr_df["Date"])
        df = df.merge(curr_df, on="Date", how="outer")
    return df


def extract_investing_data(start_date, end_date):
    url = "https://www.investing.com/instruments/HistoricalDataAjax"

    urlheader = get_url_header()
    ticker_list = get_ticker_list()
    dfs = []
    for ticker in ticker_list:
        # data format: month/date/year
        header_str = f"""{ticker}
        st_date: {start_date}
        end_date: {end_date}
        interval_sec: Daily
        sort_col: date
        sort_ord: DESC
        action: historical_data"""

        payload = dict([[val.strip() for val in row.split(": ")] for row in header_str.split("\n")])

        req = requests.post(url, data=payload, headers=urlheader)
        soup = BeautifulSoup(req.content, "html.parser")

        table = soup.find("table", id="curr_table")
        split_rows = table.find_all("tr")

        fields = []
        for row in split_rows[0:1]:
            columns = list(row.stripped_strings)
            columns = [column.replace(",", "") for column in columns]
            if len(columns) == 7 or (payload["header"] == "USD/INR Historical Data" and len(columns) == 6):
                fields = columns
                break

        rows = []
        for row in split_rows[1:]:
            row_val = list(row.stripped_strings)
            row_val = [column.replace(",", "") for column in row_val]
            if len(row_val) == 7 or (payload["header"] == "USD/INR Historical Data" and len(columns) == 6):
                rows.append(row_val)

        df = pd.DataFrame(rows, columns=fields)[["Date", "Price"]]
        df["Date"] = pd.to_datetime(df["Date"])
        df["Price"] = df["Price"].astype("float32")
        header_dict = get_feature_header_map()

        df.rename(columns={"Price": header_dict[payload["header"]]}, inplace=True)
        # print(df.head())
        dfs.append(df)

        # clear memory after writing to file
        fields.clear()
        rows.clear()
    final_df = reduce(lambda left, right: pd.merge(left, right, on="Date", how="outer"), dfs)
    final_df["price_nfty"] = final_df["price_nfty"] / final_df["price_usd"]
    final_df["price_bse"] = final_df["price_bse"] / final_df["price_usd"]

    return final_df
