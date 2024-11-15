import os
from datetime import datetime, timedelta


class TransactionSettings:
    base_start_date = datetime.strptime("2024-11-12 16:15:00", "%Y-%m-%d %H:%M:%S")
    base_end_date = datetime.strptime("2024-11-13 16:00:00", "%Y-%m-%d %H:%M:%S")

    def __init__(self, day_num):
        self.DAY = day_num
        self.START_DATE, self.END_DATE = self.set_date_range()
        self.DATA_PATH = f'data/day{self.DAY}'
        self.create_data_path()
        self.FILENAME = os.path.join(self.DATA_PATH, "transactions.csv")
        self.FILENAME_FIRST_TRS = os.path.join(self.DATA_PATH, "first_transactions.csv")
        self.FILENAME_CALCED = os.path.join(self.DATA_PATH, "calced.csv")
        self.FILENAME_WOOF_TON = 'data.json'

    def set_date_range(self):
        if self.DAY <= 1:
            return self.base_start_date, self.base_end_date
        return (
            self.base_start_date + timedelta(days=self.DAY - 1),
            self.base_end_date + timedelta(days=self.DAY - 1)
        )

    def create_data_path(self):
        if not os.path.isdir(self.DATA_PATH):
            os.makedirs(self.DATA_PATH)