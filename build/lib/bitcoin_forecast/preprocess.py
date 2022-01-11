import numpy as np


def preprocess(df):
    # https://stackoverflow.com/a/41589383/8353711
    # For the below six features only one value, is missing.
    # For this we can use forward fill, which expects for current
    # day same value repeats as per the previous day.
    # Four features: transactions_btc, size_btc, sentbyaddress_btc,
    #                difficulty_btc, sentinusd_btc, transactionvalue_btc

    cols = ["transactions_btc", "size_btc", "sentbyaddress_btc", "difficulty_btc", "sentinusd_btc", "transactionvalue_btc"]
    df[cols] = df[cols].fillna(method="ffill")

    # For global indices the saturday and sunday values will be missing.
    # Ideally, we can consider the previous day prices.
    # We can perform forward fill and then backward fill to make sure missing values
    # are filled

    cols = ["price_snp", "price_dj", "price_nasq", "price_nfty", "price_bse"]
    df[cols] = df[cols].fillna(method="ffill").fillna(method="bfill")

    # to maintain the same distribution of tweets
    # we will get probability of each value
    # fill the nulls by randomly picking the values with probabilities
    _vals, _prob = [], []
    for idx, val in df["tweets_btc"].value_counts(normalize=True).items():
        _vals.append(idx)
        _prob.append(val)

    df["tweets_btc"].loc[df["tweets_btc"].isna()] = np.random.choice(_vals, p=_prob, size=df["tweets_btc"].isna().sum())

    # to maintain the same distribution of tweets
    # we will get probability of each value
    # fill the nulls by randomly picking the values with probabilities
    _vals, _prob = [], []
    for idx, val in df["activeaddresses_btc"].value_counts(normalize=True).items():
        _vals.append(idx)
        _prob.append(val)

    df["activeaddresses_btc"].loc[df["activeaddresses_btc"].isna()] = np.random.choice(
        _vals, p=_prob, size=df["activeaddresses_btc"].isna().sum()
    )

    df = feature_engineering(df)

    return df


def feature_engineering(data):
    data["year"] = data["Date"].dt.year
    data["month"] = data["Date"].dt.month
    data["day"] = data["Date"].dt.day

    data["dayofweek_num"] = data["Date"].dt.dayofweek

    data = data.sort_values(by=["Date"], ascending=False).reset_index(drop=True)

    # we want to use yesterday's data for today's predictions
    data["tomorrow_price_btc"] = data["price_btc"].shift(1)

    # drop the rows which containes Nan values that created due to feature engineering
    data.dropna(inplace=True)
    return data
