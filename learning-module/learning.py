import numpy as np
import tensorflow as tf
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# I realize that the URL is exposed in the other module - this is just what I would normally do
CSV_FILE_PATH = os.environ["CSV_URL"]

feature_frame = pd.read_csv(CSV_FILE_PATH, index_col=[0], low_memory=False)

print(feature_frame.shape)

selected_columns = [
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Segment",
    "Region",
    "Category",
    "Quantity",
    "Profit",
]

feature_frame = feature_frame[selected_columns]

features = ["Month", "Ship Mode", "Segment", "Region", "Category", "Quantity"]
result_col = ["Profit"]

X = pd.DataFrame({feature_name: [] for feature_name in features + ["Result"]})

print(X)

# For rows with NaN order dates, replace them with the ship dates. If the ship date is also NaN, leave it as NaN
X["Month"] = [
    (
        row["Order Date"]
        if not (row["Order Date"] == "")
        else row["Ship Date"]
        if not (row["Ship Date"] == "")
        else ""
    )
    for index, row in feature_frame.iterrows()
]

# Then, grab the month from the full date string
X["Month"] = [
    date_str.split("/")[0] if isinstance(date_str, str) else ""
    for date_str in X["Month"]
]

# For these string-based features, we replace NaNs with empty strings,
#   then convert them all into unique int signifiers

X["Ship Mode"] = feature_frame["Ship Mode"].fillna("")
X["Ship Mode"] = np.unique(X["Ship Mode"], return_inverse=True)[1]

X["Segment"] = feature_frame["Segment"].fillna("")
X["Segment"] = np.unique(X["Segment"], return_inverse=True)[1]

X["Region"] = feature_frame["Region"].fillna("")
X["Region"] = np.unique(X["Region"], return_inverse=True)[1]

X["Category"] = feature_frame["Category"].fillna("")
X["Category"] = np.unique(X["Category"], return_inverse=True)[1]

# Bring over quantity after replacing NaNs
X["Quantity"] = feature_frame["Category"].fillna(-1)

X["Result"] = feature_frame[result_col]

X = X.replace("", np.nan)
X["Quantity"] = X["Quantity"].replace(-1, np.nan)

X = X.dropna()

# Now that the NaNs have been dropped, we drop the result column and set the Y
# We drop the NaNs late in the process so that it's easier to go back include NaN inputs if needed in the future
Y = X["Result"]
X = X.drop(columns=["Result"])

print(X.shape, Y.shape)
