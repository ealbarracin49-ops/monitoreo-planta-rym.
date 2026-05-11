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

st.set_page_config(page_title="RYM Manufacturing Dashboard", layout="wide")
st.title("🏭 RYM Manufacturing: Control de Planta")

# SIDEBAR
st.sidebar.header("⏱️ Configuración de Tiempo")
start_time = st.sidebar.text_input("Inicio", value="-1h")
stop_time = st.sidebar.text_input("Fin", value="now()")

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client.query_api()
query = f'from(bucket: "{BUCKET}") |> range(start: {start_time}, stop: {stop_time})'

try:
    tables = query_api.query_data_frame(query)
    df = pd.concat(tables) if isinstance(tables, list) else tables

    if df.empty:
        st.warning("No hay datos disponibles en este rango de tiempo.")
    else:
        # Limpieza
        if "_time" in df.columns:
            df["_time"] = pd.to_datetime(df["_time"])

        # MÉTRICAS
        st.subheader("📊 Resumen de Variables")
        col1, col2 = st.columns(2)
        temp_df = df[df["_field"] == "temperature"]
        hum_df = df[df["_field"] == "humidity"]
        
        if not temp_df.empty:
            col1.metric("🌡️ Temp Promedio", f"{round(temp_df['_value'].mean(), 2)} °C")
        if not hum_df.empty:
            col2.metric("💧 Humedad Promedio", f"{round(hum_df['_value'].mean(), 2)} %")

        # GRÁFICAS AMBIENTALES
        st.subheader("🌡️ Control Ambiental")
        st.plotly_chart(px.line(temp_df, x="_time", y="_value", title="Historial Temperatura"), use_container_width=True)
        st.plotly_chart(px.line(hum_df, x="_time", y="_value", title="Historial Humedad"), use_container_width=True)

        # GRÁFICAS DE ACELERÓMETRO (VIBRACIÓN)
        st.subheader("📈 Monitoreo de Vibración (Ejes X, Y, Z)")
        for axis in ["accel_x", "accel_y", "accel_z"]:
            axis_df = df[df["_field"] == axis]
            if not axis_df.empty:
                st.plotly_chart(px.line(axis_df, x="_time", y="_value", title=f"Vibración {axis.upper()}"), use_container_width=True)

        # NUEVA GRÁFICA DE CORRELACIÓN (PEDIDO DEL PROFE)
        st.subheader("🔍 Análisis de Causa-Raíz: Vibración vs Temperatura")
        st.subheader("correlacion: Vibración en x vs Temperatura")
        df_pivot = df[df["_field"].isin(["temperature", "accel_x"])].pivot(
            index="_time", columns="_field", values="_value"
        ).dropna()

        if not df_pivot.empty:
            fig_scatter = px.scatter(df_pivot, x="temperature", y="accel_x", trendline="ols", 
                                   title="Relación Calor-Vibración", labels={"temperature": "Temp (°C)", "accel_x": "Vibración X"})
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.info("💡 Esta gráfica ayuda a predecir fallos mecánicos por exceso de calor.")


        st.subheader("correlacion : Vibración en y vs Temperatura")
        df_pivot = df[df["_field"].isin(["temperature", "accel_y"])].pivot(
            index="_time", columns="_field", values="_value"
        ).dropna()

        if not df_pivot.empty:
            fig_scatter = px.scatter(df_pivot, x="temperature", y="accel_y", trendline="ols", 
                                   title="Relación Calor-Vibración", labels={"temperature": "Temp (°C)", "accel_y": "Vibración y"})
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.info("💡 Esta gráfica ayuda a predecir fallos mecánicos por exceso de calor.")

        # TELEMETRÍA GENERAL
        st.subheader("📋 Log de Datos Completo")
        st.plotly_chart(px.line(df, x="_time", y="_value", color="_field", title="Todas las variables combinadas"), use_container_width=True)
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error de conexión: {e}")
