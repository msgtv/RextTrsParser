import asyncio
import re
import locale

from src.bet_calc import BetCalculator
from src.report import HTMLReportGenerator
from src.settings import TransactionSettings
from src.transaction import TransactionData
from src.woofton import WoofTonData

# Установить локаль для форматирования чисел
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

TARGET_ADDRESS = "UQBBzGtr3y5pb1Vc2HhhbHFObxbWq2X4El3RSUJ3jO3wPyUa"


# async def main(day_num=1, dtype='f'):
#     settings = TransactionSettings(day_num=day_num)
#     woof_data = WoofTonData(settings.FILENAME_WOOF_TON)
#     transaction_data = TransactionData(
#         filename=settings.FILENAME,
#         address=TARGET_ADDRESS,
#         start_date=settings.START_DATE,
#         end_date=settings.END_DATE,
#     )
#
#     trs = await transaction_data.get_transactions(dtype)
#
#     trs.to_csv(settings.FILENAME, index=False)
#
#     first_trs = transaction_data.get_first_transactions(trs)
#     # first_trs.to_csv(settings.FILENAME_FIRST_TRS, index=False)
#
#     calculator = BetCalculator(settings, woof_data)
#     calced = calculator.calculate_bet_stats(first_trs)
#     # calced.to_csv(settings.FILENAME_CALCED, index=False)
#
#     woof_sum = round(float(calced['woofs'].sum()), 2)
#     ton_sum = round(float(trs['value'].sum()), 2)
#
#     print(f"День {settings.DAY}")
#     print(f'Банк $WOOF - {transaction_data.get_formatted_num(woof_sum)}')
#     print(f'Банк $TON - {transaction_data.get_formatted_num(ton_sum)}')
#     print('Статистика ставок по часам:')
#     print(transaction_data.get_hourly_counts(calced))


async def main(day_num=1, dtype='f'):
    settings = TransactionSettings(day_num=day_num)
    woof_data = WoofTonData(settings.FILENAME_WOOF_TON)
    transaction_data = TransactionData(
        filename=settings.FILENAME,
        address=TARGET_ADDRESS,
        start_date=settings.START_DATE,
        end_date=settings.END_DATE,
    )

    trs = await transaction_data.get_transactions(dtype)

    # prepared_data.to_csv(settings.FILENAME, index=False)

    first_trs = transaction_data.get_first_transactions(trs)
    # first_trs.to_csv(settings.FILENAME_FIRST_TRS, index=False)

    calculator = BetCalculator(settings, woof_data)
    calced = calculator.calculate_bet_stats(first_trs)
    # calced.to_csv(settings.FILENAME_CALCED, index=False)

    # Расчёт данных для HTML отчёта
    woof_sum = round(float(calced['woofs'].sum()), 2)
    ton_sum = round(float(trs['value'].sum()), 2)
    woof_price = round(ton_sum / woof_sum, 7)

    hourly_stat = transaction_data.get_stat_by_hour(calced)

    # Генерация HTML отчета
    report_generator = HTMLReportGenerator()
    report_generator.generate_report(
        day=settings.DAY,
        hourly_counts_df=hourly_stat,
        woof_sum=transaction_data.get_formatted_num(woof_sum),
        ton_sum=transaction_data.get_formatted_num(ton_sum),
        woof_price=woof_price,
        output_file=f'day_{settings.DAY}_report.html',
    )


if __name__ == '__main__':
    try:
        asyncio.run(main(4, 't'))
    except Exception as err:
        print(f'Error: {err}')
