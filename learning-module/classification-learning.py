import numpy as np
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import os
import matplotlib.pyplot as plt
import tensorflow_decision_forests as tfdf
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
    "State",
    "Sub-Category",
    "Quantity",
    "Profit",
    "Discount",
]

feature_frame = feature_frame[selected_columns]

features = [
    "Quantity",
    "State",
    "Month",
    "Ship Mode",
    "Sub-Category",
    "Profit",
    "Discount",
]
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

X["State"] = feature_frame["State"].fillna("")
X["State"] = np.unique(X["State"], return_inverse=True)[1]

X["Sub-Category"] = feature_frame["Sub-Category"].fillna("")
X["Sub-Category"] = np.unique(X["Sub-Category"], return_inverse=True)[1]

# Bring over quantity and profit after replacing NaNs
X["Quantity"] = feature_frame["Quantity"].fillna(-1)
X["Profit"] = feature_frame["Profit"].fillna(-1)
X["Discount"] = feature_frame["Discount"].fillna(-1)


X["Result"] = (
    feature_frame[result_col]
    .replace("Consumer", 0)
    .replace("Corporate", 1)
    .replace("Home Office", np.nan)
)

X = X.replace("", np.nan)
X["Quantity"] = X["Quantity"].replace(-1, np.nan)
X["Profit"] = X["Profit"].replace(-1, np.nan)
X["Discount"] = X["Discount"].replace(-1, np.nan)

X = X.dropna()


X_df = X.copy(deep=True)

X_train_df = X_df.sample(frac=0.8, random_state=0)
X_test_df = X_df.drop(X_train_df.index)

# Now that the NaNs have been dropped, we drop the result column and set the Y
# We drop the NaNs late in the process so that it's easier to go back include NaN inputs if needed in the future
Y = X["Result"]
X = X.drop(columns=["Result"])

print(X.shape, Y.shape)

Y_train = X_train_df["Result"]
Y_test = X_test_df["Result"]

X_train = X_train_df.drop(columns=["Result"])
X_test = X_test_df.drop(columns=["Result"])


X_train = frame_to_nparray(X_train)
Y_train = frame_to_nparray(Y_train, add_dim=True)

X_test = frame_to_nparray(X_test)
Y_test = frame_to_nparray(Y_test, add_dim=True)

normalization_layer = keras.layers.Normalization()
normalization_layer.adapt(X_train)

num_features = len(features)

epoch_num = 20

# print(keras.layers.Dense(num_features)(normalization_layer(X_train)))


linear_layer_list = [
    normalization_layer,
    keras.layers.Dense(1),
]

linear_regression_model = keras.Sequential(linear_layer_list)

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

logistic_layer_list = [
    normalization_layer,
    keras.layers.Dense(1, activation="sigmoid"),
]

logistic_regression_model = keras.Sequential(logistic_layer_list)

logistic_regression_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="binary_crossentropy",
    metrics=[keras.metrics.AUC()],
)

logistic_history = logistic_regression_model.fit(
    X_train,
    Y_train,
    verbose=False,
    epochs=epoch_num,
    validation_split=0.05,
)

X_train_rforest = tfdf.keras.pd_dataframe_to_tf_dataset(X_train_df, label="Result")


rforest_model = tfdf.keras.RandomForestModel()
rforest_history = rforest_model.fit(X_train_rforest)
rforest_model.compile(metrics=[keras.losses.binary_crossentropy, keras.metrics.AUC()])


def build_model(hp=None, normalize=True):
    layer_num = 8

    activation_function = "relu"

    layer_list = []

    if normalize:
        layer_list.append(normalization_layer)
    else:
        layer_list.append(keras.layers.InputLayer(num_features))

    for l_i in range(layer_num):
        layer_list.append(keras.layers.Dense(num_features, activation_function))

    layer_list.append(keras.layers.Dense(1, activation="sigmoid"))
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
logistic_regression_model.evaluate(X_test, Y_test)
mlp_model.evaluate(X_test, Y_test)
X_test_rforest = tfdf.keras.pd_dataframe_to_tf_dataset(X_test_df, label="Result")
rforest_auc = rforest_model.evaluate(X_test_rforest)[2]

linear_val_loss = linear_history.history["val_loss"]
linear_auc = linear_history.history["auc"]
logistic_val_loss = logistic_history.history["val_loss"]
logistic_auc = logistic_history.history["auc_1"]
rforest_val_loss = rforest_history.history["loss"]
mlp_val_loss = mlp_history.history["val_loss"]
mlp_auc = mlp_history.history["auc_3"]


loss_figure = plt.figure(0)
# plt.plot(range(epoch_num), linear_val_loss, label="Linear Regression Loss")
plt.plot(range(epoch_num), logistic_val_loss, label="Logistic Regression Loss")
plt.plot(range(epoch_num), mlp_val_loss, label="MLP Loss")
# Just to have the visual comparison, I plot the RF loss as a line, since it has no loss curve/history
plt.plot(
    range(epoch_num),
    np.ones(np.array(range(epoch_num)).shape) * rforest_val_loss[0],
    label="Random Forest Loss (static)",
)
plt.legend(loc="best")

auc_figure = plt.figure(1)
plt.plot(range(epoch_num), linear_auc, label="Linear Regression AUC")
plt.plot(range(epoch_num), logistic_auc, label="Logistic Regression AUC")
plt.plot(range(epoch_num), mlp_auc, label="MLP AUC")
# Same deal here with the random forest AUC visual
plt.plot(
    range(epoch_num),
    np.ones(np.array(range(epoch_num)).shape) * rforest_auc,
    label="Random Forest AUC (static)",
)
plt.legend(loc="best")

plt.show()
