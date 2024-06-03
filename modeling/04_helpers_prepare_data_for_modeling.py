import pandas as pd
import numpy as np
from utils.ModelingUtils import *
from utils.PreprocessingUtils import get_route_names, fix_polish_chars
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.impute import KNNImputer
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, roc_curve, auc, make_scorer, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import RFECV
import joblib

pd.set_option('display.max_columns', None)

data = pd.read_parquet('../data/final_data_to_modeling1105.parquet')
data = make_ml_target_regression(data)[MODEL_FEATURES]

data = data.where(pd.notnull(data), np.nan)

exclude_cols = ['temp', 'feelslike', 'humidity', 'dew', 'precip', 'precipprob', 'snow', 'preciptype', 'windgust', 'visibility', 'solarradiation', 'solarenergy', 'uvindex',]

for col in data.columns:
    if pd.api.types.is_numeric_dtype(data[col]) and col not in exclude_cols and data[col].isnull().any():
        data[col] = data[col].fillna(-1)


y = data['ML_TARGET'].values
X = data.drop('ML_TARGET', axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)

numeric_features = X_train.select_dtypes(include=['number']).columns
categorical_features = X_train.select_dtypes(exclude=['number']).columns

numeric_transformer = Pipeline(steps=[
    ('imputer', KNNImputer()),
    ('scaler', StandardScaler()),
    ])

categorical_transformer = Pipeline(steps=[
    ('transform_preciptype', CustomTransformer(column='preciptype', function=transform_preciptype)),
    ('transform_conditions', CustomTransformer(column='conditions', function=transform_conditions)),
    ('onehot', OneHotEncoder(handle_unknown='ignore', drop='first'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

pipe = Pipeline([
    ('preprocessor', preprocessor),
])

pipe.fit(X_train)

joblib.dump(pipe, f'files/pipeline_data_preprocessing.pickle')

X_train_processed = pipe.transform(X_train)
X_test_processed = pipe.transform(X_test)

# Get column names after transformation
transformed_numeric_columns = preprocessor.named_transformers_['num'].named_steps['imputer'].get_feature_names_out(input_features=numeric_features)
transformed_categorical_columns = preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(input_features=categorical_features)

transformed_columns = list(transformed_numeric_columns) + list(transformed_categorical_columns)

#Create DataFrame with processed data and column names
processed_df_train = pd.DataFrame(X_train_processed, columns=transformed_columns)
processed_df_test = pd.DataFrame(X_test_processed, columns=transformed_columns)

processed_df_train = pd.concat([processed_df_train, pd.Series(y_train).rename('ML_TARGET')], axis=1)
processed_df_test = pd.concat([processed_df_test, pd.Series(y_test).rename('ML_TARGET')], axis=1)

processed_df_train.to_parquet(f'../data/preprocessed_for_modeling/train_data_1205.parquet')
processed_df_test.to_parquet(f'../data/preprocessed_for_modeling/test_data_1205.parquet')