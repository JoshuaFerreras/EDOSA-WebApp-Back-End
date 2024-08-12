import requests
import ast
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.interpolate import interp1d
import numba
import pickle
import sktime
import joblib
import pandas as pd
from datetime import datetime


def prediction(data):
    AHI_table = {
        "Severity": None,
        "AHI": None,
        "TimeIn": data["TimeIn"],
        "TimeOut": data["TimeOut"],
        "UserID": data["UserID"],
        "Normal": 0,
        "Apnea": 0,
        "Hypopnea": 0,
    }

    for i in data.keys():
        if i not in ["UserID", "TimeIn", "TimeOut"]:
            data[i] = ast.literal_eval(data[i])

    def get_df_from_signals_dict(signals_list):
        all_df = []
        for i in range(len(signals_list)):
            signals = signals_list[i]
            pd_dict = {}
            signals_keys = list(signals.keys())
            epochs = int(len(signals[list(signals.keys())[0]]) / 24 / 30)
            for i in range(len(signals_keys)):
                pd_list = []
                curr_col = signals_keys[i]
                samples = int(len(signals[curr_col]) / epochs)
                for i in range(0, epochs):
                    pd_list.append(
                        pd.Series(
                            signals[curr_col][samples * i : samples * i + samples]
                        )
                    )
                pd_dict[curr_col] = pd_list

            pd_dict = pd.DataFrame(pd_dict)
            all_df.append(pd_dict)

        final_df = pd.concat(all_df, ignore_index=True)
        return final_df

    excluded_columns = ["UserID", "TimeOut", "TimeIn"]
    new_dict = {
        key: value for key, value in data.items() if key not in excluded_columns
    }
    df_inputs = get_df_from_signals_dict([new_dict])

    def cubic_spline_interpolation(data):
        # Define the original 300 data point signal
        l = len(data)
        x = np.linspace(0, 30, l)
        y = data.values

        # Normalize the data
        scaler = StandardScaler()
        y_norm = scaler.fit_transform(y.reshape(-1, 1)).flatten()

        # Define the new time points for upsampling
        x_new = np.linspace(0, 30, 1020)

        # Upsample using cubic spline interpolation
        f_cubic = interp1d(x, y_norm, kind="cubic")
        y_cubic = f_cubic(x_new)

        # Denormalize the data
        y_rescaled = scaler.inverse_transform(y_cubic.reshape(-1, 1)).flatten()
        y_rescaled_series = pd.Series(y_rescaled)
        return y_rescaled_series

    df_temp1 = df_inputs.copy()
    new_df = pd.DataFrame(index=df_temp1.index, columns=df_temp1.columns)

    # iterate over each cell in the dataframe
    for i in range(df_temp1.shape[0]):
        for j in range(df_temp1.shape[1]):
            cell_value = df_temp1.iloc[i, j]
            if isinstance(cell_value, pd.Series) and len(cell_value) != 1020:
                new_series = cubic_spline_interpolation(cell_value)
                new_df.iloc[i, j] = new_series
            else:
                new_df.iloc[i, j] = cell_value

    df_temp1 = new_df
    df_series = df_temp1.applymap(lambda x: pd.Series(x.tolist()))
    df_series.drop("HR", axis=1, inplace=True)
    df_series.rename(
        columns={
            "Airflow": "Flow1",
            "ECG": "EKG",
            "Snore": "Snore",
            "SpO2": "SpO2",
            "Therm": "Flow2",
        },
        inplace=True,
    )

    desired_order = ["EKG", "Snore", "Flow1", "Flow2", "SpO2"]
    df_series = df_series.reindex(columns=desired_order)

    with open(
        r"C:\Users\DeadSpheres\Downloads\EDOSA-Project\flask-vue-edosa\resultsbackend\MiniRV2_FitOnTrainingSetOnly_1020.pickle",
        "rb",
    ) as f:
        miniR = pickle.load(f)
    sensor_readings = df_series.copy()
    sensor_readings_transformed = miniR.transform(sensor_readings)

    model = joblib.load(
        r"C:\Users\DeadSpheres\Downloads\EDOSA-Project\flask-vue-edosa\resultsbackend\MiniR_pipeline2_1020_SVC_Recall_76_76_avg_75.joblib"
    )

    df_predict = model.predict(sensor_readings_transformed)

    def create_integer_counts_dict(arr, AHI_table):
        for num in arr:
            if num == 0:
                AHI_table["Normal"] += 1
            elif num == 1:
                AHI_table["Apnea"] += 1
            elif num == 2:
                AHI_table["Hypopnea"] += 1
        from datetime import datetime

        # Convert the datetime strings into datetime objects
        datetime_str1 = AHI_table["TimeIn"]
        datetime_str2 = AHI_table["TimeOut"]
        datetime_format = "%Y-%m-%d %H:%M:%S"  # Format of the datetime strings

        datetime_obj1 = datetime.strptime(datetime_str1, datetime_format)
        datetime_obj2 = datetime.strptime(datetime_str2, datetime_format)

        # Calculate the time difference in hours
        time_difference = (datetime_obj2 - datetime_obj1).total_seconds() / 3600

        # Calculate the AHI
        AHI = (AHI_table["Apnea"] + AHI_table["Hypopnea"]) / time_difference

        # Add the AHI to the dictionary
        AHI_table["AHI"] = AHI

        # Add the severity to the dictionary

        if AHI < 5:
            AHI_table["Severity"] = "Normal"
        elif AHI >= 5 and AHI < 15:
            AHI_table["Severity"] = "Mild"
        elif AHI >= 15 and AHI < 30:
            AHI_table["Severity"] = "Moderate"
        elif AHI >= 30:
            AHI_table["Severity"] = "Severe"

        return AHI_table

    AHI_table = create_integer_counts_dict(df_predict, AHI_table)
    return AHI_table
