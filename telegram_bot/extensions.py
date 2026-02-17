import requests
from datetime import datetime
import json

class APIException(Exception):
    pass

class Converter:
    @staticmethod
    def get_price(base: str, quote: str, amount: float):
        if base == quote:
            raise APIException(f'Невозможно перевести одинаковые валюты ({base}).')
        
        # Список доступных валют
        available_currencies = ['EUR', 'USD', 'RUB']
        if base not in available_currencies or quote not in available_currencies:
            raise APIException(f'Нет такой валюты: {base}/{quote}. Доступные валюты: {" ".join(available_currencies)}.')
        
        # Получаем сегодняшнюю дату
        today_date = datetime.now().strftime('%d/%m/%Y')
        
        # Делаем запрос к API ЦБ РФ
        response = requests.get(f'https://www.cbr-xml-daily.ru/daily_json.js')
        
        # Распарсиваем ответ прямо в JSON
        data = response.json()
        
        # Берем актуальные курсы валют
        euro_rate = data['Valute']['EUR']['Value']
        dollar_rate = data['Valute']['USD']['Value']
        
        # Расчет итоговой суммы
        if base == 'EUR':
            total_sum = euro_rate * amount
        elif base == 'USD':
            total_sum = dollar_rate * amount
        elif base == 'RUB':
            if quote == 'EUR':
                total_sum = amount / euro_rate
            elif quote == 'USD':
                total_sum = amount / dollar_rate
        
        return total_sum