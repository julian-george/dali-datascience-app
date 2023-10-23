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

# These are the names of the feature columns
features = ["Segment", "Quantity", "Region", "Month", "Ship Mode", "Category"]
# This is what we will be predicting
result_col = ["Profit"]

X = pd.DataFrame({feature_name: [] for feature_name in features + ["Result"]})

# For rows with NaN order dates, replace them with the ship dates. If the ship date is also NaN, leave it as NaN
X["Month"] = [
    (
        row["Order Date"]
        if not (row["Order Date"] == "")
        else row["Ship Date"]
        if not (row["Ship Date"] == "")
        else np.nan
    )
    for index, row in feature_frame.iterrows()
]

# Then, grab the month from the full date string
X["Month"] = [
    date_str.split("/")[0] if isinstance(date_str, str) else np.nan
    for date_str in X["Month"]
]
# Bring the rest of the desired columns over to the input matrix
X["Ship Mode"] = feature_frame["Ship Mode"]
X["Segment"] = feature_frame["Segment"]
X["Region"] = feature_frame["Region"]
X["Category"] = feature_frame["Category"]
X["Quantity"] = feature_frame["Quantity"]
X["Result"] = feature_frame[result_col]

# Drop rows with NaN values
X = X.dropna()

# This converts string features' values into unique integers, each integer representing a different value
X["Ship Mode"] = np.unique(X["Ship Mode"], return_inverse=True)[1]
X["Segment"] = np.unique(X["Segment"], return_inverse=True)[1]
X["Region"] = np.unique(X["Region"], return_inverse=True)[1]
X["Category"] = np.unique(X["Category"], return_inverse=True)[1]


Y = X["Result"]
X = X.drop(columns=["Result"])

# Split the matrix up
X_train = X.sample(frac=0.8, random_state=0)
X_test = X.drop(X_train.index)

Y_train = Y[X_train.index]
Y_test = Y.drop(X_train.index)

# Convert the data frames to numpy arrays to be accepted by the model
X_train = frame_to_nparray(X_train)
Y_train = frame_to_nparray(Y_train, add_dim=True)

X_test = frame_to_nparray(X_test)
Y_test = frame_to_nparray(Y_test, add_dim=True)

# Create a layer to normalize the inputted data
normalization_layer = keras.layers.Normalization()
normalization_layer.adapt(X_train)

# I also experienced with normalizing the labels to get a better idea of the loss
label_normalization_layer = keras.layers.Normalization()
label_normalization_layer.adapt(Y_train)

# Uncomment this to remove the label normalization
# label_normalization_layer = lambda d: d

num_features = len(features)

epoch_num = 20

### LINEAR REGRESSION MODEL ###

layer_list = [
    normalization_layer,
    keras.layers.Dense(1),
]

linear_regression_model = keras.Sequential(layer_list)

linear_regression_model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss="mean_absolute_error"
)

linear_history = linear_regression_model.fit(
    X_train,
    label_normalization_layer(Y_train),
    verbose=False,
    epochs=epoch_num,
    validation_split=0.05,
)


### MLP MODEL ###


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
mlp_history = mlp_model.fit(
    X_train,
    label_normalization_layer(Y_train),
    epochs=epoch_num,
    validation_split=0.1,
    verbose=False,
)

# Evaluate both models with test data
linear_regression_model.evaluate(X_test, label_normalization_layer(Y_test))
mlp_model.evaluate(X_test, label_normalization_layer(Y_test))

# Retrieve and plot validation loss from training process
linear_val_loss = linear_history.history["val_loss"]
mlp_val_loss = mlp_history.history["val_loss"]

plt.plot(range(epoch_num), linear_val_loss, label="Linear Regression Loss")
plt.plot(range(epoch_num), mlp_val_loss, label="MLP Loss")
plt.legend(loc="best")

plt.show()
