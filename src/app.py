import pandas as pd
import streamlit as st


PAGE_SIZE = 100


def reset_table_page():
    st.session_state.pop("table_page", None)


def reset_upload():
    st.session_state.pop("uploaded_table", None)
    reset_table_page()


def read_uploaded_file(uploaded_file):
    if uploaded_file.size == 0:
        raise pd.errors.EmptyDataError("Пустой файл")
    if not uploaded_file.name.lower().endswith(".csv"):
        return pd.read_excel(uploaded_file)
    try:
        return pd.read_csv(uploaded_file, sep=None, engine="python")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="cp1251")


def show_table(data):
    st.subheader("Таблица данных")
    page_count = (len(data) + PAGE_SIZE - 1) // PAGE_SIZE
    page = 1
    if page_count > 1:
        page = st.number_input(
            f"Страница (из {page_count})",
            min_value=1,
            max_value=page_count,
            step=1,
            key="table_page",
        )
    start = (page - 1) * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(data))
    st.caption(f"Строки {start + 1}–{end} из {len(data)}")
    st.dataframe(data.iloc[start:end], use_container_width=True)


st.set_page_config(page_title="Анализ ДТП", page_icon="🚗", layout="wide")
st.title("Система анализа дорожно-транспортных происшествий")
st.write("Загрузите файл с данными о ДТП в формате CSV или Excel.")

uploaded_file = st.file_uploader(
    "Выберите файл", type=["csv", "xlsx", "xls"], on_change=reset_upload
)

if uploaded_file is not None:
    try:
        if "uploaded_table" not in st.session_state:
            st.session_state.uploaded_table = read_uploaded_file(uploaded_file)
    except pd.errors.EmptyDataError:
        st.warning("Файл прочитан, но в нём нет данных.")
    except Exception as error:
        st.error("Не удалось прочитать файл. Проверьте формат и содержимое файла.")
        st.caption(f"Подробности ошибки: {error}")
    else:
        data = st.session_state.uploaded_table
        if data.empty:
            st.warning("Файл прочитан, но в нём нет данных.")
        else:
            st.success("Файл успешно загружен!")
            st.write(f"Количество строк: {len(data)}")
            st.write(f"Количество столбцов: {len(data.columns)}")
            show_table(data)
