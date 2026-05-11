import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient

TOKEN = "DkpL6zznGwMgO5RwAhPXj2ZbZ3w2qsvWVTWotXivS3KKRZe56F5XsywwnK7l3_76FWpj2ZVWOeN1RQVlTydEWQ=="
ORG = "miguelcmo"
URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
BUCKET = "iot_telemetry_data"

client = InfluxDBClient(
    url=URL,
    token=TOKEN,
    org=ORG
)

query_api = client.query_api()

st.title("Debug InfluxDB")

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30d)
'''

try:
    df = query_api.query_data_frame(query)

    if isinstance(df, list):
        df = pd.concat(df)

    st.write("Datos encontrados:")
    st.dataframe(df)

    st.write("Measurements:")
    st.write(df["_measurement"].unique())

    st.write("Fields:")
    st.write(df["_field"].unique())

except Exception as e:
    st.error(str(e))

client.close()
