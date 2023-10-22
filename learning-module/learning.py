import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import os
import seaborn as sns
from dotenv import load_dotenv

from util import frame_to_nparray

load_dotenv()

# I realize that the URL is exposed in the other module - this is just what I would normally do
CSV_FILE_PATH = os.environ["CSV_URL"]

feature_frame = pd.read_csv(CSV_FILE_PATH, index_col=[0], low_memory=False)

print("Feature frame loaded, shape:", feature_frame.shape)

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

features = ["Segment", "Quantity", "Region", "Month", "Ship Mode", "Category"]
result_col = ["Profit"]

X = pd.DataFrame({feature_name: [] for feature_name in features + ["Result"]})

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
X["Quantity"] = feature_frame["Quantity"].fillna(-1)

X["Result"] = feature_frame[result_col]

X = X.replace("", np.nan)
X["Quantity"] = X["Quantity"].replace(-1, np.nan)

X = X.dropna()

# Now that the NaNs have been dropped, we drop the result column and set the Y
# We drop the NaNs late in the process so that it's easier to go back include NaN inputs if needed in the future
Y = X["Result"]
X = X.drop(columns=["Result"])

print(X.shape, Y.shape)

X_train = X.sample(frac=0.8, random_state=0)
X_test = X.drop(X_train.index)

Y_train = Y[X_train.index]
Y_test = Y.drop(X_train.index)

X_train = frame_to_nparray(X_train)
Y_train = frame_to_nparray(Y_train, add_dim=True)

X_test = frame_to_nparray(X_test)
Y_test = frame_to_nparray(Y_test, add_dim=True)

normalization_layer = keras.layers.Normalization()
normalization_layer.adapt(X_train)

label_normalization_layer = keras.layers.Normalization()
label_normalization_layer.adapt(Y_train)

num_features = len(features)


# print(keras.layers.Dense(num_features)(normalization_layer(X_train)))


layer_list = [
    normalization_layer,
    keras.layers.Dense(1),
]

linear_regression_model = keras.Sequential(layer_list)

linear_regression_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss="mean_absolute_error"
)

history = linear_regression_model.fit(
    X_train,
    label_normalization_layer(Y_train),
    verbose=False,
    epochs=10,
    validation_split=0.05,
)


def build_model(hp=None, normalize=True):
    layer_num = 6

    activation_function = "relu"

    layer_list = []

    if normalize:
        layer_list.append(normalization_layer)
    else:
        layer_list.append(keras.layers.InputLayer(num_features))

    for l_i in range(layer_num):
        layer_list.append(keras.layers.Dense(num_features, activation_function))

    layer_list.append(keras.layers.Dense(1))
    model = keras.Sequential(layer_list)
    model.build()
    learning_rate = 0.001
    opt = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=opt,
        loss=keras.losses.mean_absolute_error,
    )
    model.summary()

    return model


mlp_model = build_model()
mlp_model.fit(
    X_train,
    label_normalization_layer(Y_train),
    epochs=10,
    validation_split=0.1,
    verbose=False,
)
linear_regression_model.evaluate(X_test, label_normalization_layer(Y_test))
for i in range(1):
    print(
        linear_regression_model.predict(X_test[i]), label_normalization_layer(Y_test[i])
    )
mlp_model.evaluate(X_test, label_normalization_layer(Y_test))
for i in range(1):
    print(mlp_model.predict(X_test[i]), label_normalization_layer(Y_test[i]))
