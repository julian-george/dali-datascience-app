import numpy as np
import tensorflow as tf
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

CSV_FILE_PATH = os.environ["CSV_URL"]

feature_frame = pd.read_csv(CSV_FILE_PATH, index_col=[0], low_memory=False)

print(feature_frame)
