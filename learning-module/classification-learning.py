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
    "Region",
    "Sub-Category",
    "Quantity",
    "Profit",
    "Discount",
    "Customer Name",
    "Customer ID",
]

feature_frame = feature_frame[selected_columns]

# Feature column names
features = [
    "Quantity",
    "Region",
    "Month",
    "Ship Mode",
    "Sub-Category",
    "Profit",
    "Discount",
    "Customer Frequency",
]
# Result column
result_col = ["Segment"]

customer_name_id_dict = {}

# Since we want to use Customer IDs to determine customer frequency (ie how many total purchases each customer has made),
#   we fill in NaN customer IDs based on if they have had a name previously associated with them

# This code assumes that customer IDs are unique to customer names
for index, row in feature_frame.iterrows():
    # If both customer name and ID aren't NaN, add them as a pairing to the dict
    if isinstance(row["Customer Name"], str):
        if isinstance(row["Customer ID"], str):
            customer_name_id_dict[row["Customer Name"]] = row["Customer ID"]

feature_frame["Customer ID"] = [
    # Replace every customer ID with the ID linked to their name in the dictionary
    customer_name_id_dict[row["Customer Name"]]
    if isinstance(row["Customer Name"], str)
    else row["Customer ID"]
    for index, row in feature_frame.iterrows()
]


X = pd.DataFrame({feature_name: [] for feature_name in features + ["Result"]})

# For rows with NaN order dates, replace them with the ship dates. If the ship date is also NaN, leave it as NaN
X["Month"] = [
    (
        row["Order Date"]
        if isinstance(row["Order Date"], str)
        else row["Ship Date"]
        if isinstance(row["Ship Date"], str)
        else np.nan
    )
    for index, row in feature_frame.iterrows()
]

# Then, grab the month from the full date string
X["Month"] = [
    date_str.split("/")[0] if isinstance(date_str, str) else np.nan
    for date_str in X["Month"]
]

# Grab the features
X["Ship Mode"] = feature_frame["Ship Mode"]
X["Region"] = feature_frame["Region"]
X["Sub-Category"] = feature_frame["Sub-Category"]
X["Customer Frequency"] = feature_frame["Customer ID"]
X["Quantity"] = feature_frame["Quantity"]
X["Profit"] = feature_frame["Profit"]
X["Discount"] = feature_frame["Discount"]

# We are doing binary classification about whether the buyer is a regular consumer or a corporate customer
#  we convert these two labels to 0 and 1, and the other label to nan to be removed
X["Result"] = (
    feature_frame[result_col]
    .replace("Consumer", 0)
    .replace("Corporate", 1)
    .replace("Home Office", np.nan)
)

X = X.dropna()

# For these string-based features, we convert them all into unique int signifiers

X["Ship Mode"] = np.unique(X["Ship Mode"], return_inverse=True)[1]
X["Region"] = np.unique(X["Region"], return_inverse=True)[1]
X["Sub-Category"] = np.unique(X["Sub-Category"], return_inverse=True)[1]

X["Customer Frequency"] = np.unique(X["Customer Frequency"], return_inverse=True)[1]
X["Customer Frequency"] = np.bincount(X["Customer Frequency"])[X["Customer Frequency"]]

# We divide up the feature matrix differently than with the regression model so that
#   we have both the np matrices for the neural networks and the dataframes for the random forest
X_df = X.copy(deep=True)

X_train_df = X_df.sample(frac=0.8, random_state=0)
X_test_df = X_df.drop(X_train_df.index)

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

epoch_num = 30

### LINEAR REGRESSION ###

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

### LOGISTIC REGRESSION ###

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

### RANDOM FOREST ###

X_train_rforest = tfdf.keras.pd_dataframe_to_tf_dataset(X_train_df, label="Result")

rforest_model = tfdf.keras.RandomForestModel()
rforest_history = rforest_model.fit(X_train_rforest)
rforest_model.compile(metrics=[keras.losses.binary_crossentropy, keras.metrics.AUC()])

### MLP ###


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

# Evaluating & printing the models' performances on the test data
linear_regression_model.evaluate(X_test, Y_test)
logistic_regression_model.evaluate(X_test, Y_test)
mlp_model.evaluate(X_test, Y_test)
X_test_rforest = tfdf.keras.pd_dataframe_to_tf_dataset(X_test_df, label="Result")
rforest_auc = rforest_model.evaluate(X_test_rforest)[2]


# Grab and plot models' validation loss histories
linear_val_loss = linear_history.history["val_loss"]
linear_auc = linear_history.history["val_auc"]
logistic_val_loss = logistic_history.history["val_loss"]
logistic_auc = logistic_history.history["val_auc_1"]
rforest_val_loss = rforest_history.history["loss"]
mlp_val_loss = mlp_history.history["val_loss"]
mlp_auc = mlp_history.history["val_auc_3"]


loss_figure = plt.figure(0)
# Not plotted because it's so much higher than the rest
# plt.plot(range(epoch_num), linear_val_loss, label="Linear Regression Loss")
plt.plot(range(epoch_num), logistic_val_loss, label="Logistic Regression Loss")
plt.plot(range(epoch_num), mlp_val_loss, label="MLP Loss")
# Just to have the visual comparison, I plot the RF loss as a line, since it has no loss curve/history
plt.plot(
    range(epoch_num),
    np.ones(np.array(range(epoch_num)).shape) * rforest_val_loss[0],
    label="Random Forest Loss",
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
    label="Random Forest AUC",
)
plt.legend(loc="best")

plt.show()
