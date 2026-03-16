import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Настройка страницы
st.set_page_config(
    page_title="Кредитный Калькулятор",
    layout='wide',
)

# Инициализация глобального состояния
if "df" not in st.session_state:
    st.session_state.df = None

if "summary" not in st.session_state:
    st.session_state.summary = None

# Интерфейс Streamlit
st.title("💳 Кредитный Калькулятор")

# Информация необходимая для расчета
st.write("---")
st.info("""
Для расчёта кредита укажите следующие данные:
- **Сумму кредита**,
- **Годовую процентную ставку** (от 0.1% до 25%),
- **Количество месяцев кредита** (от 1 до 360 месяцев),
- выберите **тип платежа** («Аннуитетный» или «Дифференцированный»).
""")

# Боковая панель с параметрами кредита
st.sidebar.title("Введите параметры кредита:")
principal = st.sidebar.number_input("Сумма кредита в рублях:", min_value=0.0, step=10000.0)
rate = st.sidebar.number_input("Годовая процентная ставка (%):", min_value=0.0, max_value=25.0, value=12.0, step=0.1)
months = st.sidebar.number_input("Срок кредита (месяцы):", min_value=0, max_value=360, step=1)
payment_type = st.sidebar.radio("Тип платежа:", ["Аннуитетный", "Дифференцированный"], horizontal=True)
start_date = st.sidebar.date_input("Начальная дата платежа:", value=date.today())
calculate = st.sidebar.button("Рассчитать")

if calculate:
    # Проверка корректности ввода
    if principal <= 0:
        st.warning("Введите корректную сумму кредита (больше 0)")
        st.stop()
    elif rate < 0.1 or rate > 25:
        st.warning("Процентная ставка должна быть в диапазоне от 0.1% до 25%")
        st.stop()
    elif months < 1 or months > 360:
        st.warning("Срок кредита должен быть от 1 до 360 месяцев")
        st.stop()
    else:
        st.sidebar.success("Расчет произведен", icon=":material/thumb_up:")
        st.session_state["press_button"] = True

    # Результат расчета
    st.write("**Итоги расчета:**")
    with st.spinner("Идет расчет..."):
        # Создание пустого DataFrame для графика платежей
        df = pd.DataFrame(columns=[
            "Дата платежа",
            "Остаток долга на начало",
            "Ежемесячный платеж",
            "Основная задолженность",
            "Проценты",
            "Остаток долга"
        ])

        # Аннуитетный платеж
        if payment_type == "Аннуитетный":
            r = rate / 100 / 12
            annuity = principal * (r * (1 + r) ** months) / ((1 + r) ** months - 1)
            remaining_balance = principal
            previous_remaining_balance = principal  # отслеживаем прошлый остаток
            for i in range(int(months)):
                next_month = start_date + relativedelta(months=(i + 1))  # Следующий месяц
                interest = remaining_balance * r
                main_payment = annuity - interest
                remaining_balance -= main_payment

                # Заполняем новую колонку "Остаток долга на начало"
                df.loc[i] = [
                    next_month.strftime("%d.%m.%Y"),
                    round(previous_remaining_balance, 2),
                    round(annuity, 2),
                    round(main_payment, 2),
                    round(interest, 2),
                    round(remaining_balance, 2)
                ]
                previous_remaining_balance = remaining_balance  # запомнили текущий остаток для следующей итерации

        # Дифференцированный платеж
        else:
            initial_payment = principal / months
            remaining_balance = principal
            previous_remaining_balance = principal  # отслеживаем прошлый остаток
            for i in range(int(months)):
                next_month = start_date + relativedelta(months=(i + 1))  # Следующий месяц
                interest = remaining_balance * (rate / 100 / 12)
                main_payment = initial_payment
                total_payment = main_payment + interest
                remaining_balance -= main_payment

                # Заполняем новую колонку "Остаток долга на начало"
                df.loc[i] = [
                    next_month.strftime("%d.%m.%Y"),
                    round(previous_remaining_balance, 2),
                    round(total_payment, 2),
                    round(main_payment, 2),
                    round(interest, 2),
                    round(remaining_balance, 2)
                ]
                previous_remaining_balance = remaining_balance  # запомнили текущий остаток для следующей итерации

        # Сохраняем результат в session state
        st.session_state.df = df
        st.session_state.summary = {
            "Общая сумма выплат": df['Ежемесячный платеж'].sum(),
            "Всего процентов": df['Проценты'].sum()
        }

        # Вывод итогов расчетов
        if payment_type == "Аннуитетный":
            st.write(f"- Размер ежемесячного платежа: ₽{round(df['Ежемесячный платеж'][0], 2)}")
        else:
            st.write(f"- Минимальный ежемесячный платеж: ₽{round(min(df['Ежемесячный платеж']), 2)}")
            st.write(f"- Максимальный ежемесячный платеж: ₽{round(max(df['Ежемесячный платеж']), 2)}")

        st.write(f"- Общая сумма выплат: ₽{round(st.session_state.summary['Общая сумма выплат'], 2)}")
        st.write(f"- Всего процентов: ₽{round(st.session_state.summary['Всего процентов'], 2)}")

        # Выводим график платежей
        with st.expander("Показать график платежей"):
            st.dataframe(df,width='stretch')