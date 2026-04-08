import streamlit as st
import pandas as pd
import plotly.express as px
import io
from charset_normalizer import from_bytes

# --- Настройка страницы ---
st.set_page_config(
    page_title="Анализ данных",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📊 Анализ CSV-файлов")

# --- Инициализация состояния сессии ---
if 'df' not in st.session_state:
    st.session_state.df = None
if 'loaded' not in st.session_state:
    st.session_state.loaded = False
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = []
if 'column_types' not in st.session_state:
    st.session_state.column_types = {}


# --- Кешированная функция загрузки данных ---
@st.cache_data(show_spinner="🔍 Определяю кодировку и загружаю данные...")
def load_data(file):
    raw_data = file.getbuffer().tobytes()
    if not raw_data.strip():
        return None, "Файл пуст или содержит только пробельные символы."
    try:
        encoding = from_bytes(raw_data).best().encoding
        df = pd.read_csv(file, encoding=encoding, sep=None, engine='python')
        return df, None
    except Exception as e:
        return None, f"Ошибка чтения файла: {str(e)}"


# --- Боковая панель: Загрузка файла ---
with st.sidebar:
    st.header("🔽 Загрузка файла")
    uploaded_file = st.file_uploader("📁 Выберите CSV-файл", type="csv")

    with st.spinner(text="⏳ Обработка файла..."):
        if uploaded_file is not None:
            df, error_message = load_data(uploaded_file)
            if error_message:
                st.error(error_message)
                st.session_state.loaded = False
            elif df is None or df.empty:
                st.warning("Файл не содержит данных для анализа.")
                st.session_state.loaded = False
            else:
                # Определяем типы данных для каждого столбца
                column_types = {}
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        column_types[col] = 'numeric'
                    elif pd.api.types.is_datetime64_any_dtype(df[col]):
                        column_types[col] = 'datetime'
                    else:
                        column_types[col] = 'categorical'

                st.session_state.df = df
                st.session_state.column_types = column_types

                # Сброс выбранных колонок при загрузке нового файла
                st.session_state.selected_columns = []
                #считаем кол-во загруженных строк и столбцов
                st.success(f"✅ **Успешно загружено:** {len(df)} строк, {len(df.columns)} столбцов")
                st.session_state.loaded = True

# --- Основной блок анализа ---
if st.session_state.loaded and st.session_state.df is not None:
    df = st.session_state.df
    column_types = st.session_state.column_types
    #Создаем три вкладки
    tab1, tab2, tab3 = st.tabs(["📋 Таблица", "📝 Статистический анализ", "📈 Графики"])

    # Вкладка 1: Таблица с данными
    with tab1:
        st.success("✅ Файл успешно загружен!")
        st.subheader("📥 Данные:")
        all_columns = df.columns.tolist()

        # Логика сброса выбора колонок при смене файла
        if not st.session_state.selected_columns or not all(
                col in all_columns for col in st.session_state.selected_columns):
            st.session_state.selected_columns = all_columns.copy()
        #выбор колонок
        selected_columns = st.multiselect(
            "Выберите колонки для отображения:",
            options=all_columns,
            default=st.session_state.selected_columns,
            key="column_filter"
        )

        if selected_columns:
            st.session_state.selected_columns = selected_columns
        #чек бокс для показа всей таблицы
        if selected_columns:
            show_full_table = st.checkbox("🔼 Развернуть таблицу полностью", value=False)

            if show_full_table:
                st.subheader("📋 Все данные (отфильтрованные):")
                st.dataframe(df[selected_columns])
            else:
                st.subheader("📋 Первые 10 строк (отфильтрованные):")
                st.dataframe(df[selected_columns].head(10))
        else:
            st.warning("❗ Выберите хотя бы один столбец для отображения.")
        #добавим информацию с типом колонок
        with st.expander("ℹ️ Информация"):
            st.write("**Типы данных:**")
            info_df = df.dtypes.reset_index().rename(columns={"index": "Столбец", 0: "Тип"})
            st.dataframe(info_df)

    # Вкладка 2: Статистика
    with tab2:
        st.header("📊 Статистические показатели")
        #числовые столбцы
        num_cols = [col for col, typ in column_types.items() if typ == 'numeric']

        if num_cols:
            selected_stat_col = st.selectbox(
                "Выберите числовой столбец для анализа",
                num_cols,
                help="Для выбранного столбца будут рассчитаны основные статистические метрики."
            )
            #основные статистические подсчеты
            if selected_stat_col:
                data = df[selected_stat_col]

                col1, col2, col3, col4, col5 = st.columns(5)

                col1.metric("Среднее", f"{data.mean():.2f}")
                col2.metric("Медиана", f"{data.median():.2f}")
                col3.metric("Ст. отклонение", f"{data.std(ddof=1):.2f}")
                col4.metric("Минимум", f"{data.min():.2f}")
                col5.metric("Максимум", f"{data.max():.2f}")
                #добавить информацию о наличие пропущенных значений при их наличии
                missing_count = data.isna().sum()
                if missing_count > 0:
                    st.warning(f"⚠️ В столбце обнаружены пропущенные значения: **{missing_count}** из {len(data)}.")
        #если числовых столбцлв в загруженных данных нет
        else:
            st.info("ℹ️ В загруженном файле отсутствуют числовые столбцы для проведения анализа.")

    # Вкладка 3: Графики
    with tab3:
        st.header("📈 Построение графиков")
        #Выбор графиков
        chart_type = st.radio(
            "Тип графика",
            ["Линейный", "Точечный (диаграмма рассеяния)", "Гистограмма"],
            horizontal=True,
        )
        #типы колонок
        numeric_cols = [col for col, typ in column_types.items() if typ == 'numeric']
        datetime_cols = [col for col, typ in column_types.items() if typ == 'datetime']
        categorical_cols = [col for col, typ in column_types.items() if typ == 'categorical']

        # --- БЛОК 1: Линейный и Точечный графики ---
        if chart_type in ["Линейный", "Точечный (диаграмма рассеяния)"]:
            if len(numeric_cols) < 2:
                st.error("❌ Для построения этого графика требуется как минимум два числовых столбца.")
                st.info(f"В текущем файле найдено всего {len(numeric_cols)} числовых колонки.")
            else:
                col1, col2, col3 = st.columns(3)

                with col1:
                    x_axis_options = numeric_cols + datetime_cols
                    x_axis = st.selectbox("Ось X", x_axis_options, index=0)

                with col2:
                    y_options = [col for col in numeric_cols if col != x_axis]
                    y_axis = st.selectbox("Ось Y", y_options, index=0)

                with col3:
                    color_by_options = ["Нет"] + categorical_cols
                    color_by = st.selectbox("Цвет (опционально)", color_by_options, index=0)

                if x_axis and y_axis and len(df) > 0:
                    fig_data = df[[x_axis, y_axis]].dropna()

                    if color_by != "Нет":
                        fig_data[color_by] = df[color_by]

                    labels_dict = {x_axis: x_axis, y_axis: y_axis}

                    if chart_type == "Линейный":
                        if column_types.get(x_axis) == 'datetime':
                            fig_data = fig_data.sort_values(x_axis)

                        fig = px.line(
                            fig_data,
                            x=x_axis,
                            y=y_axis,
                            color=color_by if color_by != "Нет" else None,
                            title=f"{y_axis} от {x_axis}",
                            labels=labels_dict,
                        )
                        if column_types.get(x_axis) == 'datetime':
                            fig.update_layout(xaxis=dict(tickformat="%d %b %Y", nticks=15))
                    else:  # Scatter
                        fig = px.scatter(
                            fig_data,
                            x=x_axis,
                            y=y_axis,
                            color=color_by if color_by != "Нет" else None,
                            title=f"Диаграмма рассеяния: {y_axis} от {x_axis}",
                            labels=labels_dict,
                        )
                        #преобразование дат в формат дд.mm.yy
                        if column_types.get(x_axis) == 'datetime':
                            fig.update_layout(xaxis=dict(tickformat="%d %m %Y", nticks=15))

                    st.plotly_chart(fig, width='content')

                    # кнопка для скачивания
                    buffer = io.StringIO()
                    buffer.write(fig.to_html())
                    buffer.seek(0)

                    st.download_button(
                        label="💾 Скачать график (HTML)",
                        data=buffer.getvalue(),
                        file_name=f"plot_{x_axis}_vs_{y_axis}.html",
                        mime="text/html"
                    )
        # --- БЛОК 2: Гистограмма ---
        elif chart_type == "Гистограмма":
            if not numeric_cols:
                st.error("❌ Для построения гистограммы требуется хотя бы один числовой столбец.")
                st.info("В текущем файле нет числовых данных для анализа распределения.")
            else:
                col = st.selectbox("Столбец для анализа", numeric_cols)
                bins = st.slider("Количество интервалов (bins)", min_value=5, max_value=50, value=20)

                fig = px.histogram(
                    df,
                    x=col,
                    nbins=bins,
                    title=f"Распределение: {col}",
                    labels={col: col, 'count': 'Частота'}
                )

                st.plotly_chart(fig, width='content')

                #  кнопка для скачивания ...
                buffer = io.StringIO()
                buffer.write(fig.to_html())
                buffer.seek(0)

                st.download_button(
                    label="💾 Скачать гистограмму (HTML)",
                    data=buffer.getvalue(),
                    file_name=f"histogram_{col}.html",
                    mime="text/html"
                )
else:
    st.info("👈 Пожалуйста, загрузите CSV-файл для начала работы.")