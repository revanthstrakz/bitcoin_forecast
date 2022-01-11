# Take the lastest 100 records and retrain for every 20 days
# Update the DB table with 100 records, to make sure DB size as less
# Perform incremental re-train using custom linear regression model
# Create a cron job which will run return function for every 20 days

import sqlite3

import joblib
import pandas as pd
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from bitcoin_forecast.scrap_ground_truth import get_final_ground_truth_data

# from datetime import datetime


scheduler = BackgroundScheduler(timezone=pytz.timezone("gmt"))


def extract_latest_100_records():
    data = pd.read_csv("data/processed/latest_200_25-06-2021_to_10-01-2022.csv")
    model_cols = joblib.load("artifacts/model/model_cols.joblib")
    model_cols = list(model_cols.values)
    model_cols.append("Date")

    data.sort_values(by=["Date"], ascending=False, inplace=True)
    data = data[model_cols]
    data = data[:100]

    return data


def store_data(data):
    # Create your connection.
    with sqlite3.connect("bitcoin_db") as cnx:
        data.to_sql(name="bitcoin_data", con=cnx, if_exists="replace")


def fetch_data_db(db_name):
    with sqlite3.connect(db_name) as cnx:
        data = pd.read_sql("bitcoin_data", parse_dates=["Date"], con=cnx)
    return data


def incremental_retrain():
    model = joblib.load("rls_model.joblib")
    model_cols = joblib.load("model_cols.joblib")
    data = get_final_ground_truth_data()
    X = data[model_cols]
    y = data["tomorrow_price_btc"]
    model.update_many(X, y)
    # time_stamp = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    # model = joblib.dump(model, f"artifacts/model/rls_model/rls_model_{time_stamp}.joblib")
    model = joblib.dump(model, "rls_model.joblib")


def run_scheduler():
    scheduler.add_job(incremental_retrain, trigger="interval", days=20)

    scheduler.start()


if __name__ == "__main__":
    # TODO: Need to scrap from online instead of using csv
    # data = extract_latest_100_records()
    # store_data(data)
    # db_name = "bitcoin_db"
    # data = fetch_data_db(db_name)
    print("updating model..")
    incremental_retrain()
    print("updated the model!!")
