# billing_controller.py
from flask import Blueprint, jsonify
import pandas as pd

billing = Blueprint('billing', __name__)

@billing.route("/api/billing_data")
def get_billing_data():
    df = pd.read_csv("data/billing_actual.csv")  # Must point to your real file
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    return jsonify({
        "labels": df["date"].dt.strftime("%Y-%m-%d").tolist(),
        "data": df["amount"].tolist()
    })
