import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.query_api import QueryApi
import plotly.express as px

# =========================
# CONFIGURACIÓN INFLUXDB
# =========================

TOKEN = "DkpL6zznGwMgO5RwAhPXj2ZbZ3w2qsvWVTWotXivS3KKRZe56F5XsywwnK7l3_76FWpj2ZVWOeN1RQVlTydEWQ=="
ORG = "miguelcmo"
URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
BUCKET = "iot_telemetry_data"

# =========================
# CONEXIÓN
# =========================

client = InfluxDBClient(
    url=URL,
    token=TOKEN,
    org=ORG
)

query_api = client.query_api()

# =========================
# INTERFAZ STREAMLIT
# =========================

st.set_page_config(
    page_title="Dashboard IoT",
    layout="wide"
)

st.title("📊 Dashboard IoT")
st.write("Monitoreo de temperatura y humedad")

# =========================
# QUERY FLUX
# =========================

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "environment")
  |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity")
'''

# =========================
# OBTENER DATOS
# =========================

result = query_api.query_data_frame(query)

# =========================
# VALIDAR DATOS
# =========================

if isinstance(result, list):
    df = pd.concat(result)
else:
    df = result

if df.empty:
    st.warning("⚠️ No hay datos disponibles")
else:

    # Limpiar columnas innecesarias
    df = df[["_time", "_field", "_value"]]

    # Convertir fecha
    df["_time"] = pd.to_datetime(df["_time"])

    # =========================
    # MÉTRICAS
    # =========================

    temp_actual = df[df["_field"] == "temperature"]["_value"].iloc[-1]
    hum_actual = df[df["_field"] == "humidity"]["_value"].iloc[-1]

    col1, col2 = st.columns(2)

    with col1:
        st.metric("🌡 Temperatura Actual", f"{temp_actual:.2f} °C")

    with col2:
        st.metric("💧 Humedad Actual", f"{hum_actual:.2f} %")

    # =========================
    # GRÁFICA TEMPERATURA
    # =========================

    temp_df = df[df["_field"] == "temperature"]

    fig_temp = px.line(
        temp_df,
        x="_time",
        y="_value",
        title="Temperatura"
    )

    st.plotly_chart(fig_temp, use_container_width=True)

    # =========================
    # GRÁFICA HUMEDAD
    # =========================

    hum_df = df[df["_field"] == "humidity"]

    fig_hum = px.line(
        hum_df,
        x="_time",
        y="_value",
        title="Humedad"
    )

    st.plotly_chart(fig_hum, use_container_width=True)

# =========================
# CERRAR CLIENTE
# =========================

client.close()
