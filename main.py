import asyncio
import json
import os
import re
import locale

import pandas as pd
from time import sleep

from datetime import datetime, timedelta
from pytoniq import LiteClient, MessageAny

# Установить параметры
TARGET_ADDRESS = "UQBBzGtr3y5pb1Vc2HhhbHFObxbWq2X4El3RSUJ3jO3wPyUa"

PATTERN = re.compile(r'\d+(\.\d+)?\s+TON\s+Ref#\w+={6}', flags=re.IGNORECASE)

UTC_OFFSET = 5  # Часовой пояс

START_DATE = datetime.strptime("2024-11-14 16:00:00", "%Y-%m-%d %H:%M:%S")
END_DATE = datetime.strptime("2024-11-15 16:00:00", "%Y-%m-%d %H:%M:%S")

DAY = 3
DATA_PATH = f'data/day{DAY}'

if not os.path.isdir(DATA_PATH):
    os.makedirs(DATA_PATH)

FILENAME = os.path.join(DATA_PATH, "transactions.csv")
FILENAME_FIRST_TRS = os.path.join(DATA_PATH, "first_transactions.csv")
FILENAME_CALCED = os.path.join(DATA_PATH, "calced.csv")
FILENAME_WOOF_TON = 'data.json'

# START_TIME = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0) - timedelta(hours=UTC_OFFSET)
# END_TIME = START_TIME + timedelta(days=1)

# Инициализация pytoniq
# blockchain = pytoniq()


def get_formatted_num(num):
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')  # Установите нужную локаль
    num = locale.format_string('%.2f', num, grouping=True)
    return num



def get_woof_count(data_dict, ton_count, left=None, right=None):
    if ton_count == 5:
        return 1
    if ton_count <= 0.1:
        return 1000000

    woof_count = data_dict.get(ton_count)
    if woof_count is None:
        if left is None:
            left = get_woof_count(data_dict, round(ton_count - 0.01, 2), left=left, right=right)
        if right is None:
            right = get_woof_count(data_dict, round(ton_count + 0.01, 2), left=left, right=right)

        woof_count = (left + right) / 2

    return woof_count


def get_tx_datetime(tx):
    date = datetime.fromtimestamp(tx.in_msg.info.created_at)

    return date


class EndOfParsing(Exception):
    ...


# Функция для фильтрации транзакций
async def get_transactions_in_time_range(address):
    from_lt = None
    from_hash = None
    trs = []
    async with LiteClient.from_mainnet_config(ls_i=0, trust_level=2) as client:
        while True:
            try:
                transactions = await client.get_transactions(address, 1000, from_lt=from_lt, from_hash=from_hash)

                for tx in transactions:
                    try:
                        dt = get_tx_datetime(tx)
                    except Exception as e:
                        continue

                    if dt > END_DATE:
                        continue
                    elif dt > START_DATE:
                        trs.append(tx)
                    else:
                        raise EndOfParsing()
                else:
                    from_lt = tx.prev_trans_lt
                    from_hash = tx.prev_trans_hash
            except EndOfParsing:
                return trs


def prepare_transactions(trs):
    data = []

    for tr in trs:
        comment = tr.in_msg.body.data.decode('utf-8', errors='ignore')
        comment = ''.join(filter(str.isprintable, comment))

        res = PATTERN.match(comment)
        if res is None:
            continue

        from_address = tr.in_msg.info.src.to_str(is_user_friendly=True)
        to_address = tr.in_msg.info.dest.to_str(is_user_friendly=True)
        date = datetime.fromtimestamp(tr.in_msg.info.created_at)
        date_str = datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

        coins = tr.in_msg.info.value_coins / 1000000000

        data.append({
            'date': date_str,
            'from': from_address,
            'value': coins,
            'comment': comment,
        })

    df = pd.DataFrame(data)

    return df


async def get_transactions(address, from_: str = 'f'):
    if from_ == 'f':
        df = pd.read_csv(FILENAME)
        df['date'] = pd.to_datetime(df['date'])
        return df
    else:
        trs = await get_transactions_in_time_range(address)

        trs = prepare_transactions(trs)

        trs.to_csv(FILENAME, index=False)

        return trs


def get_first_trs(trs):
    return trs.sort_values('date').drop_duplicates(subset=['from'], keep='first')


def get_ton_woof_data():
    with open(FILENAME_WOOF_TON, 'r') as f:
        data = json.load(f)

    woof_tons = {}

    for row in data:
        w, t = row
        w = int(w)
        t = float(t)

        woof_tons.setdefault(t, []).append(w)

    data = {}
    for t, woofs in woof_tons.items():
        data[t] = sum(woofs)/len(woofs)

    return data


def calc_woof_betted(first_trs):
    tw_dict = get_ton_woof_data()

    def calc_woof(row):
        ton_count = row['value']
        woof_count = get_woof_count(tw_dict, ton_count)

        row['woofs'] = woof_count

        return row

    calced = first_trs.apply(calc_woof, axis=1)

    return calced


async def main():
    WOOF_BETTED = 224000

    trs = await get_transactions(
        TARGET_ADDRESS,
        from_='t'
    )

    first_trs = get_first_trs(trs)

    first_trs.to_csv(FILENAME_FIRST_TRS, index=False)

    calced = calc_woof_betted(first_trs)

    calced.to_csv(FILENAME_CALCED, index=False)

    woofs = calced['woofs']
    woof_sum = round(float(woofs.sum()), 2)

    ton_sum = round(float(trs['value'].sum()), 2)

    reached = (WOOF_BETTED / woof_sum) * ton_sum

    total_trs = len(trs)
    people_count = len(calced)
    other_trs_sum = total_trs - people_count

    # TODO: статистика ставок:
    #  < 10 000
    st1 = woofs[woofs < 10000].count()
    st2 = woofs[woofs >= 10000][woofs < 50000].count()
    st3 = woofs[woofs >= 50000][woofs < 100000].count()
    st4 = woofs[woofs >= 100000][woofs < 500000].count()
    st5 = woofs[woofs >= 500000][woofs < 991000].count()
    st6 = woofs[woofs >= 991000].count()

    print(f'День {DAY}')

    s = f"""Статистика ставок:
    до 10к: {st1}
    от 10к до 50к: {st2}
    от 50к до 100к: {st3}
    от 100к до 500к: {st4}
    от 500к до 991к: {st5}
    от 991к: {st6}
    
    Транзакций: {total_trs}
    Ставок: {people_count}
    Обмены и замарозки: {other_trs_sum}\n\n"""

    print(s)
    print(f'Банк $WOOF - {get_formatted_num(woof_sum)}')
    print(f'Банк $TON - {get_formatted_num(ton_sum)}')

    print('{reached:.2f} $TON за ставку {woof} $WOOF'.format(reached=reached, woof=WOOF_BETTED))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        print(f'Error: {err}')




"""
import pandas as pd

# Загрузите ваши данные в DataFrame (например, из CSV)
df = pd.read_csv('transactions.csv')

# Преобразуем столбец 'date' в формат datetime
df['date'] = pd.to_datetime(df['date'])

# Сортируем по дате, оставляем первую запись для каждого уникального отправителя
df_first_transactions = df.sort_values('date').drop_duplicates(subset=['from'], keep='first')

# Выводим результат
print(df_first_transactions)
"""
