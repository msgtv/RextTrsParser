import pandas as pd

from src.transaction import TransactionData


class BetCalculator:
    def __init__(self, settings, woof_ton_data):
        self.settings = settings
        self.woof_ton_data = woof_ton_data

    def calculate_bet_trs(self, df):
        def calc_woof(row):
            if row['action'] == TransactionData.action_bet:
                ton_count = row['value']
                woof_count = TransactionData.get_woof_count(self.woof_ton_data.data, ton_count)
                row['woofs'] = woof_count
            else:
                row['woofs'] = 0
            return row

        return df.apply(calc_woof, axis=1)

    def get_big_bet_stat(self, df, bet_volume):
        df = df[df['woofs'] >= bet_volume]
        df = df['date'].dt.floor('min').value_counts().to_frame().reset_index()
        df.sort_values(by=['date'], inplace=True)
        df.reset_index(inplace=True, drop=True)

        # # Генерация полного временного диапазона
        # full_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='T')
        #
        # # Установка полного временного диапазона в DataFrame
        # df = df.set_index('date').reindex(full_range).fillna(0).reset_index(names='date')

        df['date'] = df['date'].dt.strftime("%d.%m %H:%M")

        return df
