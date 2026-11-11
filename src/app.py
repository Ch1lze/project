import re

import pandas as pd
import streamlit as st


PAGE_SIZE = 100


def reset_table_page():
    st.session_state.pop("table_page", None)


def reset_filters():
    st.session_state.pop("filter_region", None)
    st.session_state.pop("filter_year", None)
    reset_table_page()


def reset_upload():
    st.session_state.pop("uploaded_table", None)
    st.session_state.pop("filter_values", None)
    reset_filters()


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


def get_column(data, headers, names):
    for name in names:
        if name in headers:
            return data[headers[name]]
    return None


def get_filter_values(data):
    headers = {
        re.sub(r"[_\s]+", " ", str(column).strip().casefold()): column
        for column in data.columns
    }
    regions = get_column(data, headers, ("регион", "region", "region name", "субъект рф"))
    if regions is not None:
        regions = regions.astype("string").str.strip().replace("", pd.NA)

    years = get_column(data, headers, ("год", "год дтп", "year", "accident year"))
    if years is not None:
        years = pd.to_numeric(years, errors="coerce")
        years = years.where(years.between(1000, 9999) & (years % 1 == 0)).astype("Int64")

    dates = get_column(data, headers, ("дата дтп", "дата", "дата и время дтп", "datetime", "date", "accident date"))
    if dates is not None and (years is None or years.isna().any()):
        # Keep the calendar year in the source even when a timestamp has a time zone.
        dates = dates.astype("string").str.strip().str.split(r"[T\s]", n=1).str[0]
        date_years = pd.to_datetime(dates, format="mixed", dayfirst=True, errors="coerce").dt.year.astype("Int64")
        years = date_years if years is None else years.fillna(date_years)
    return regions, years


def apply_filters(data):
    if "filter_values" not in st.session_state:
        st.session_state.filter_values = get_filter_values(data)
    regions, years = st.session_state.filter_values
    region_options = sorted(regions.dropna().unique()) if regions is not None else []
    year_options = sorted(years.dropna().unique()) if years is not None else []
    if not region_options and not year_options:
        return data

    with st.sidebar:
        st.header("Фильтры")
        st.button("Сбросить фильтры", key="reset_filters", on_click=reset_filters)
        region = None
        if region_options:
            region = st.selectbox(
                "Регион", [None, *region_options],
                format_func=lambda value: "Все регионы" if value is None else value,
                key="filter_region", on_change=reset_table_page,
            )
        year = None
        if year_options:
            year = st.selectbox(
                "Год", [None, *year_options],
                format_func=lambda value: "Все годы" if value is None else str(value),
                key="filter_year", on_change=reset_table_page,
            )

    if region is not None and year is not None:
        return data.loc[regions.eq(region) & years.eq(year)]
    if region is not None:
        return data.loc[regions.eq(region)]
    if year is not None:
        return data.loc[years.eq(year)]
    return data


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
            filtered = apply_filters(data)
            if filtered.empty:
                st.info("По выбранным фильтрам ничего не найдено.")
            else:
                show_table(filtered)
