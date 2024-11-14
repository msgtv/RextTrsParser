from src.transaction import TransactionData


class BetCalculator:
    def __init__(self, settings, woof_ton_data):
        self.settings = settings
        self.woof_ton_data = woof_ton_data

    def calculate_bet_stats(self, df):
        def calc_woof(row):
            ton_count = row['value']
            woof_count = TransactionData.get_woof_count(self.woof_ton_data.data, ton_count)
            row['woofs'] = woof_count
            return row

        return df.apply(calc_woof, axis=1)