import pandas as pd
from utils.ModelingUtils import make_ml_target, MODEL_FEATURES
from sklearn.model_selection import train_test_split
from sklearn.impute import KNNImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import joblib

data = pd.read_parquet('../data/prepared_data_with_weather.parquet')
data = make_ml_target(data)

y = data['ML_TARGET'].values
X = data[MODEL_FEATURES]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)

numeric_features = X_train.select_dtypes(include=['number']).columns
categorical_features = X_train.select_dtypes(exclude=['number']).columns

numeric_transformer = Pipeline(steps=[
    ('imputer', KNNImputer()),
])

categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ]
)

pipe = Pipeline([
    ('preprocessor', preprocessor),
])

pipe.fit(X_train)

joblib.dump(pipe, 'files/fitted_pipeline.pkl')

X_train_processed = pipe.transform(X_train)
X_test_processed = pipe.transform(X_test)

transformed_numeric_columns = preprocessor.named_transformers_['num'].named_steps['imputer'].get_feature_names_out(input_features=numeric_features)
transformed_categorical_columns = preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(input_features=categorical_features)

# Combine numeric and categorical columns
transformed_columns = list(transformed_numeric_columns) + list(transformed_categorical_columns)

# Create DataFrame with processed data and column names
processed_df_train = pd.DataFrame(X_train_processed, columns=transformed_columns)
processed_df_test = pd.DataFrame(X_test_processed, columns=transformed_columns)

processed_df_train = pd.concat([processed_df_train, pd.Series(y_train).rename('ML_TARGET')], axis=1)
processed_df_test = pd.concat([processed_df_test, pd.Series(y_test).rename('ML_TARGET')], axis=1)

processed_df_train.to_parquet('../data/preprocessed_for_modeling/train_data.parquet')
processed_df_test.to_parquet('../data/preprocessed_for_modeling/test_data.parquet')