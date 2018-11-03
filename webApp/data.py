import pandas as pd
import numpy as np


def load_data():

    data = pd.read_csv("data/nama_10_gdp_1_Data.csv", na_values=':', usecols=["TIME", "GEO", "NA_ITEM", "Value"])

    data["Value"].replace(to_replace="None", value=np.NaN, inplace=True)  # replace 'None'
    data["Value"] = data["Value"].str.replace(" ", "")  # replace ' '
    pd.to_numeric(data["Value"], errors='coerce')  # convert Value to number

    data.dropna(inplace=True)  # drop NaN

    data = data.groupby(["TIME", "GEO", "NA_ITEM"], as_index=False).max()  # group repeated rows

    data["Country"] = np.where(data["GEO"].str.contains("Euro", case=False, na=False), 'Euro', 'Countries')  # create Country flag

    data.sort_values(  # sort values
        by=["TIME", "Country", "GEO", "NA_ITEM"],
        ascending=[True, False, True, True],
        inplace=True
    )

    return data
