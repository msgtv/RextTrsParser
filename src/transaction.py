import locale
import os.path
import re
from datetime import datetime

import pandas as pd
from pytoniq import LiteClient


class TransactionData:
    action_bet = 'bet'
    action_exchange = 'exchange'
    action_freeze = 'freeze'

    pattern = re.compile(r'\d+(\.\d+)?\s+TON\s+Ref#\w+={6}', flags=re.IGNORECASE)

    def __init__(self, filename, address, start_date, end_date):
        self.filename = filename
        self.address = address
        self.start_date = start_date
        self.end_date = end_date

    async def get_transactions(self, t: str = 'f'):
        if os.path.isfile(self.filename):
            df = pd.read_csv(self.filename)
            df['date'] = pd.to_datetime(df['date'])
        else:
            df = pd.DataFrame()

        if t == 'f' and not df.empty:
            return df

        else:
            last_lt = not df.empty and df.sort_values(by='date', ascending=False).loc[0, 'lt'] or None
            new_trs = await self.fetch_transactions(last_lt)
            new_df = self.prepare_transactions(new_trs)

            df = pd.concat([df, new_df])
            df.reset_index(inplace=True, drop=True)

            df.to_csv(self.filename, index=False)

        # if t == 'f':
        #     df = pd.read_csv(self.filename)
        #     df['date'] = pd.to_datetime(df['date'])
        # else:
        #     df = await self.fetch_transactions()
        #     df = self.prepare_transactions(df)
        #
        #     df.to_csv(self.filename, index=False)

        return df


    @staticmethod
    def get_formatted_num(num, num_count=2):
        return locale.format_string(f'%.{num_count}f', num, grouping=True)

    @staticmethod
    def get_woof_count(data_dict, ton_count, left=None, right=None):
        if ton_count == 5:
            return 1
        if ton_count <= 0.1:
            return 1000000

        woof_count = data_dict.get(ton_count)
        if woof_count is None:
            if left is None:
                left = TransactionData.get_woof_count(data_dict, round(ton_count - 0.01, 2), left=left, right=right)
            if right is None:
                right = TransactionData.get_woof_count(data_dict, round(ton_count + 0.01, 2), left=left, right=right)
            woof_count = (left + right) / 2

        return woof_count

    async def fetch_transactions(self, last_lt):
        from_lt = None
        from_hash = None
        transactions = []
        async with LiteClient.from_mainnet_config(ls_i=0, trust_level=2, timeout=10) as client:
            while True:
                tx_list = await client.get_transactions(self.address, 1000, from_lt=from_lt, from_hash=from_hash)
                for tx in tx_list:
                    if tx.lt == last_lt:
                        return transactions
                    if not hasattr(tx.in_msg.info, 'created_at'):
                        continue
                    dt = datetime.fromtimestamp(tx.in_msg.info.created_at)
                    if dt > self.end_date:
                        continue
                    elif dt > self.start_date:
                        transactions.append(tx)
                    else:
                        return transactions
                from_lt = tx.prev_trans_lt
                from_hash = tx.prev_trans_hash

    def prepare_transactions(self, trs):
        data = []
        for tr in trs:
            comment = tr.in_msg.body.data.decode('utf-8', errors='ignore')
            comment = ''.join(filter(str.isprintable, comment))
            if self.pattern.match(comment) is None:
                continue
            from_address = tr.in_msg.info.src.to_str(is_user_friendly=True)
            date = pd.Timestamp.fromtimestamp(tr.in_msg.info.created_at)
            data.append({
                'date': date,
                'from': from_address,
                'value': tr.in_msg.info.value_coins / 1e9,
                'comment': comment,
                'lt': tr.lt,
            })
        return pd.DataFrame(data)

    def mark_transactions(self, df):
        df['action'] = ''

        # метка ставок #1
        first_trs_indexes = df.sort_values('date').drop_duplicates(subset=['from'], keep='first').index
        mask_first_trs = df.index.isin(first_trs_indexes)
        df.loc[mask_first_trs, 'action'] = self.action_bet

        # метка платного обмена
        mask_empty_action = df['action'] == ''
        mask_exchanges = df['value'] == 1
        df.loc[mask_empty_action & mask_exchanges, 'action'] = self.action_exchange

        # метка заморозки
        mask_freeze_first = df['value'] == 5
        mask_empty_action = df['action'] == ''
        freeze_trs = df[mask_freeze_first].drop_duplicates(subset=['from'], keep='first').index
        mask_freeze_second = df.index.isin(freeze_trs)
        df.loc[mask_empty_action & mask_freeze_second, 'action'] = self.action_freeze

        # метка ставок с пустым 'action' и не равным 5 TON
        # mask_second_non_five_ton = df['value'] != 5
        # df.loc[mask_empty_action & mask_second_non_five_ton, 'action'] = self.action_bet

        df = df[df['action'] != '']

        return df

    @staticmethod
    def get_hourly_counts(df):
        df['date'] = pd.to_datetime(df['date']).dt.floor('h')
        return df['date'].value_counts().sort_index()

    def get_stat(self, df):
        # Группируем по часу и считаем количество транзакций
        df['date'] = pd.to_datetime(df['date'])
        df['hour'] = df['date'].dt.floor('h')

        data = []
        total_stat = {'date': 'ВСЕГО'}

        total_stat.update(self.get_stat_by_bet_volume(df))
        total_stat.update(self.get_total_stat(df))
        data.append(total_stat)

        for one_date, one_df in df.groupby('hour'):
            one_data = {
                'date': one_date.strftime('%d.%m %H:%M'),
            }

            one_data.update(self.get_total_stat(one_df))

            volume_stat = self.get_stat_by_bet_volume(one_df)
            one_data.update(volume_stat)

            data.append(one_data)

        data.append(total_stat)

        return pd.DataFrame(data)

    def get_total_stat(self, df):
        return {
            'С': len(df[df['action'] == self.action_bet]),
            'О': len(df[df['action'] == self.action_exchange]),
            'З': len(df[df['action'] == self.action_freeze]),
            'В': len(df[df['action'] != '']),
        }

    @staticmethod
    def get_stat_by_bet_volume(df):
        woofs = df[df['woofs'] > 0]['woofs']
        data = {
            '1': woofs[woofs < 4].count(),
            'до 10к': woofs[woofs < 10000].count(),
            '10к - 50к': woofs[woofs >= 10000][woofs < 50000].count(),
            '50к - 100к': woofs[woofs >= 50000][woofs < 100000].count(),
            '100к - 500к': woofs[woofs >= 100000][woofs < 500000].count(),
            '500к - 991к': woofs[woofs >= 500000][woofs < 991000].count(),
            'от 991к': woofs[woofs >= 991000].count()
        }

        return data
