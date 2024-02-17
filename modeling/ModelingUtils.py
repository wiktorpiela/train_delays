import numpy as np
import pandas as pd
def make_ml_target(df):
    df['ML_TARGET'] = np.select(
        [
            df['Opóźnienie przyjazdu'] <= 5,
            (df['Opóźnienie przyjazdu'] > 5) & (df['Opóźnienie przyjazdu'] <= 20),
            (df['Opóźnienie przyjazdu'] > 20) & (df['Opóźnienie przyjazdu'] <= 60),
            df['Opóźnienie przyjazdu'] > 60
        ],
        [
            0,
            1,
            2,
            3
        ]
    )

    return df

def make_dummies(df, col_to_dummy):
    dummies = pd.get_dummies(df[col_to_dummy], prefix=col_to_dummy, dtype=float)
    df = pd.concat([df.drop(col_to_dummy, axis=1), dummies], axis=1)
    return df
