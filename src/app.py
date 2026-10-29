
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Анализ ДТП",
    page_icon="🚗",
    layout="wide"
)

st.title("Система анализа дорожно-транспортных происшествий")
st.write("Загрузите файл с данными о ДТП в формате CSV или Excel.")

uploaded_file = st.file_uploader(
    "Выберите файл",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine="python")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(
                    uploaded_file,
                    sep=None,
                    engine="python",
                    encoding="cp1251"
                )
        else:
            df = pd.read_excel(uploaded_file)

        if df.empty:
            st.warning("Файл прочитан, но в нём нет данных.")
        else:
            st.success("Файл успешно загружен!")
            st.write(f"Количество строк: {len(df)}")
            st.write(f"Количество столбцов: {len(df.columns)}")

            st.subheader("Предварительный просмотр данных")
            st.dataframe(df.head(100), use_container_width=True)

    except Exception as error:
        st.error(
            "Не удалось прочитать файл. "
            "Проверьте формат и содержимое файла."
        )
        st.caption(f"Подробности ошибки: {error}")
