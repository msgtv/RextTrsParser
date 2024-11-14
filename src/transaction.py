import locale
import re
from datetime import datetime

import pandas as pd
from pytoniq import LiteClient


class TransactionData:
    pattern = re.compile(r'\d+(\.\d+)?\s+TON\s+Ref#\w+={6}', flags=re.IGNORECASE)

    def __init__(self, filename, address, start_date, end_date):
        self.filename = filename
        self.address = address
        self.start_date = start_date
        self.end_date = end_date

    async def get_transactions(self, t: str = 'f'):
        if t == 'f':
            df = pd.read_csv(self.filename)
            df['date'] = pd.to_datetime(df['date'])
        else:
            df = await self.fetch_transactions()
            df = self.prepare_transactions(df)

            df.to_csv(self.filename, index=False)

        return df


    @staticmethod
    def get_formatted_num(num):
        return locale.format_string('%.2f', num, grouping=True)

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

    async def fetch_transactions(self):
        from_lt = None
        from_hash = None
        transactions = []
        async with LiteClient.from_mainnet_config(ls_i=0, trust_level=2) as client:
            while True:
                tx_list = await client.get_transactions(self.address, 1000, from_lt=from_lt, from_hash=from_hash)
                for tx in tx_list:
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
            date = datetime.fromtimestamp(tr.in_msg.info.created_at).strftime("%Y-%m-%d %H:%M:%S")
            data.append({
                'date': date,
                'from': from_address,
                'value': tr.in_msg.info.value_coins / 1e9,
                'comment': comment,
            })
        return pd.DataFrame(data)

    @staticmethod
    def get_first_transactions(df):
        return df.sort_values('date').drop_duplicates(subset=['from'], keep='first')

    @staticmethod
    def get_hourly_counts(df):
        df['date'] = pd.to_datetime(df['date']).dt.floor('h')
        return df['date'].value_counts().sort_index()
