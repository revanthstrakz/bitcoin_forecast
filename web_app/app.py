# import sqlite3
from functools import lru_cache

import joblib
from bitcoin_forecast.scrap_data import get_today_data
from flask import Flask, render_template

from retrain_scheduler import run_scheduler

app = Flask(__name__)
model = joblib.load("artifacts/model/rls_model.joblib")
model_cols = joblib.load("artifacts/model/model_cols.joblib")

# start scheduler to re-train model for every 20 days
run_scheduler()


@app.route("/")
def home():
    return render_template("index.html")


@lru_cache
def get_and_store_data():
    data = get_today_data()
    # Create your connection.
    # with sqlite3.connect("bitcoin_db") as cnx:
    #     data.to_sql(name="bitcoin_data", con=cnx, if_exists="append")
    return data


@app.route("/predict", methods=["POST"])
def predict():
    """
    For rendering results on HTML GUI
    """
    today_df = get_and_store_data()
    # get_data.cache_clear() # TODO: clear cache every day
    price = model.predict(today_df[model_cols])[0]
    usd = today_df["price_usd"].values[0]
    return render_template("index.html", prediction_text=f"Bitcoin price $ {price:.2f} USD ({price * usd:.2f} INR) on 11-Jan-2022")


if __name__ == "__main__":

    app.run(debug=True)
