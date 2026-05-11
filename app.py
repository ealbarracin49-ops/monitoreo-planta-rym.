import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
import plotly.express as px

# =========================
# CONFIGURACIÓN INFLUXDB
# =========================

URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "EJwrNIOrygCc52EJm-H0NVuHwUapDRTUdEiJ4rCwz3H_cwi_APdfpViMMc9bmzfzcfg9dub8uibJw0fpekAIVQ=="
ORG = "miguelcmo"
BUCKET = "iot_telemetry_data"

# =========================
# CONFIGURACIÓN STREAMLIT
# =========================

st.set_page_config(
    page_title="IoT Dashboard",
    layout="wide"
)

st.title("📡 IoT Telemetry Dashboard")

# =========================
# SIDEBAR - RANGO DE TIEMPO
# =========================

st.sidebar.header("⏱️ Configuración de Tiempo")

start_time = st.sidebar.text_input(
    "Start",
    value="-1h"
)

stop_time = st.sidebar.text_input(
    "Stop",
    value="now()"
)

# =========================
# CONEXIÓN INFLUXDB
# =========================

client = InfluxDBClient(
    url=URL,
    token=TOKEN,
    org=ORG
)

query_api = client.query_api()

# =========================
# QUERY FLUX
# =========================

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: {start_time}, stop: {stop_time})
'''

# =========================
# CONSULTAR DATOS
# =========================

try:

    tables = query_api.query_data_frame(query)

    if isinstance(tables, list):
        df = pd.concat(tables)
    else:
        df = tables

    # =========================
    # VALIDAR DATOS
    # =========================

    if df.empty:
        st.warning("No hay datos disponibles.")

    else:

        # =========================
        # LIMPIEZA
        # =========================

        columns_to_remove = [
            "result",
            "table",
            "_start",
            "_stop"
        ]

        for col in columns_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])

        # Convertir tiempo
        if "_time" in df.columns:
            df["_time"] = pd.to_datetime(df["_time"])

        # =========================
        # MÉTRICAS SUPERIORES
        # =========================

        st.subheader("📊 Métricas Estadísticas")

        # Función auxiliar
        def get_field_stats(field_name):

            field_df = df[df["_field"] == field_name]

            if not field_df.empty:

                avg = round(field_df["_value"].mean(), 2)
                minimum = round(field_df["_value"].min(), 2)
                maximum = round(field_df["_value"].max(), 2)

                return avg, minimum, maximum

            return None, None, None

        # Variables
        temp_avg, temp_min, temp_max = get_field_stats("temperature")
        hum_avg, hum_min, hum_max = get_field_stats("humidity")

        col1, col2 = st.columns(2)

        with col1:
            if temp_avg is not None:
                st.metric(
                    "🌡️ Temp Promedio",
                    f"{temp_avg} °C",
                    delta=f"Max {temp_max} | Min {temp_min}"
                )

        with col2:
            if hum_avg is not None:
                st.metric(
                    "💧 Humedad Promedio",
                    f"{hum_avg} %",
                    delta=f"Max {hum_max} | Min {hum_min}"
                )

        # =========================
        # DATAFRAME
        # =========================

        st.subheader("📋 Datos Recientes")

        st.dataframe(df, use_container_width=True)

        # =========================
        # GRÁFICA TEMPERATURA
        # =========================

        temp_df = df[df["_field"] == "temperature"]

        if not temp_df.empty:

            st.subheader("🌡️ Temperatura")

            fig_temp = px.line(
                temp_df,
                x="_time",
                y="_value",
                title="Temperatura vs Tiempo"
            )

            st.plotly_chart(fig_temp, use_container_width=True)

        # =========================
        # GRÁFICA HUMEDAD
        # =========================

        hum_df = df[df["_field"] == "humidity"]

        if not hum_df.empty:

            st.subheader("💧 Humedad")

            fig_hum = px.line(
                hum_df,
                x="_time",
                y="_value",
                title="Humedad vs Tiempo"
            )

            st.plotly_chart(fig_hum, use_container_width=True)

        # =========================
        # ACELERÓMETRO
        # =========================

        accel_x = df[df["_field"] == "accel_x"]
        accel_y = df[df["_field"] == "accel_y"]
        accel_z = df[df["_field"] == "accel_z"]

        st.subheader("📈 Acelerómetro")

        if not accel_x.empty:

            fig_x = px.line(
                accel_x,
                x="_time",
                y="_value",
                title="Accel X"
            )

            st.plotly_chart(fig_x, use_container_width=True)

        if not accel_y.empty:

            fig_y = px.line(
                accel_y,
                x="_time",
                y="_value",
                title="Accel Y"
            )

            st.plotly_chart(fig_y, use_container_width=True)

        if not accel_z.empty:

            fig_z = px.line(
                accel_z,
                x="_time",
                y="_value",
                title="Accel Z"
            )

            st.plotly_chart(fig_z, use_container_width=True)

        # =========================
        # GRÁFICA GENERAL
        # =========================

        st.subheader("📊 Telemetría General")

        fig_all = px.line(
            df,
            x="_time",
            y="_value",
            color="_field",
            title="Todas las Variables"
        )

        st.plotly_chart(fig_all, use_container_width=True)

except Exception as e:
    st.error(f"Error conectando a InfluxDB: {e}")
