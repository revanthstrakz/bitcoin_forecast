from datetime import datetime, timedelta

import pandas as pd

from bitcoin_forecast.preprocess import preprocess
from bitcoin_forecast.utils import (
    WINDOW_SIZE,
    extract_investing_data,
    get_bitinfocharts_data,
    get_meta_data,
)


def get_final_ground_truth_data():
    meta_df = get_meta_data()
    bitcoin_df = get_bitinfocharts_data(meta_df)

    end_date = datetime.today().strftime("%m/%d/%Y")
    start_date = (datetime.today() - timedelta(WINDOW_SIZE)).strftime("%m/%d/%Y")

    indices_df = extract_investing_data(start_date, end_date)
    final_df = pd.merge(bitcoin_df, indices_df, on="Date", how="outer")
    final_df = preprocess(final_df)

    return final_df


if __name__ == "__main__":
    # extract bitinfocharts
    data = get_final_ground_truth_data()
