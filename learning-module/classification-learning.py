import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import os
import matplotlib.pyplot as plt
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

features = ["Quantity", "Region", "Month", "Ship Mode", "Category", "Profit"]
result_col = ["Segment"]

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

# X["Segment"] = feature_frame["Segment"].fillna("")
# X["Segment"] = np.unique(X["Segment"], return_inverse=True)[1]

X["Region"] = feature_frame["Region"].fillna("")
X["Region"] = np.unique(X["Region"], return_inverse=True)[1]

X["Category"] = feature_frame["Category"].fillna("")
X["Category"] = np.unique(X["Category"], return_inverse=True)[1]

# Bring over quantity and profit after replacing NaNs
X["Quantity"] = feature_frame["Quantity"].fillna(-1)
X["Profit"] = feature_frame["Profit"].fillna(-1)


X["Result"] = (
    feature_frame[result_col]
    .replace("Consumer", 0)
    .replace("Corporate", 1)
    .replace("Home Office", np.nan)
)

X = X.replace("", np.nan)
X["Quantity"] = X["Quantity"].replace(-1, np.nan)
X["Profit"] = X["Profit"].replace(-1, np.nan)

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

num_features = len(features)

epoch_num = 20

# print(keras.layers.Dense(num_features)(normalization_layer(X_train)))


layer_list = [
    normalization_layer,
    keras.layers.Dense(1),
]

linear_regression_model = keras.Sequential(layer_list)

linear_regression_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="binary_crossentropy",
    metrics=[keras.metrics.AUC()],
)

linear_history = linear_regression_model.fit(
    X_train,
    Y_train,
    verbose=False,
    epochs=epoch_num,
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

    layer_list.append(keras.layers.Dense(1, activation="softmax"))
    model = keras.Sequential(layer_list)
    model.build()
    learning_rate = 0.001
    opt = keras.optimizers.Adam(learning_rate=learning_rate)
    model.compile(
        optimizer=opt,
        loss=keras.losses.binary_crossentropy,
        metrics=[keras.metrics.AUC()],
    )
    model.summary()

    return model


mlp_model = build_model()
mlp_history = mlp_model.fit(
    X_train,
    Y_train,
    epochs=epoch_num,
    validation_split=0.1,
    verbose=False,
)
linear_regression_model.evaluate(X_test, Y_test)
mlp_model.evaluate(X_test, Y_test)

linear_val_loss = linear_history.history["val_loss"]
linear_auc = linear_history.history["auc"]
mlp_val_loss = mlp_history.history["val_loss"]
mlp_auc = mlp_history.history["auc"]

plt.plot(range(epoch_num), linear_val_loss, label="Linear Regression Loss")
plt.plot(range(epoch_num), linear_auc, label="Linear Regression AUC")
plt.plot(range(epoch_num), mlp_val_loss, label="MLP Loss")
plt.plot(range(epoch_num), mlp_auc, label="MLP AUC")
plt.legend(loc="best")

plt.show()
