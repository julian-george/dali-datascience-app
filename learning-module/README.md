## DALI Machine Learning Challenge

### Julian George, 24W

## Objective

The objective of my machine learning module will be to predict the profit of a sale based on several pre-determined characteristics. This is a useful, real-life application, because

## Acknowledgements

My linear regression implementation borrows heavily from [here](https://www.tensorflow.org/tutorials/keras/regression)

## Usage

Feel free to set this up in a virtual environment - I didn't use one in development. To set it up, I do the following:

1. `pip3 install -r requirements.txt`
2. Run `python3 classification-learning.py` to run the classification model or `python3 regression-learning.py` to run the regression model

## Discussion and Results

I started out with the regression model, trying to predict the profit of a sale based on its date, the type of consumer ("Segment"), the region of the buyer, the month it was bought, the type of shipping, and the quantity. I implemented a linear regression (and later a logistic regression) model for a baseline, and then built an MLP model. After completing my implementation, I initially had a tough time wrapping my head around the loss, since it initially was the average difference between the actual profit and the predicted profit, leading to high loss amounts (think ~20-50). I implemented loss normalization, that turned that loss into a decimal percent.
