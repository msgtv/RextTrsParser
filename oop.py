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
    settings = TransactionSettings(day_num=3)
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

    WOOF_BETTED = 224000
    reached = (WOOF_BETTED / woof_sum) * ton_sum
    stats = {
        'st1': calced['woofs'][calced['woofs'] < 10000].count(),
        'st2': calced['woofs'][(calced['woofs'] >= 10000) & (calced['woofs'] < 50000)].count(),
        'st3': calced['woofs'][(calced['woofs'] >= 50000) & (calced['woofs'] < 100000)].count(),
        'st4': calced['woofs'][(calced['woofs'] >= 100000) & (calced['woofs'] < 500000)].count(),
        'st5': calced['woofs'][(calced['woofs'] >= 500000) & (calced['woofs'] < 991000)].count(),
        'st6': calced['woofs'][calced['woofs'] >= 991000].count(),
    }

    hourly_counts = transaction_data.get_hourly_counts(calced)

    # Генерация HTML отчета
    report_generator = HTMLReportGenerator()
    report_generator.generate_report(
        day=settings.DAY,
        stats=stats,
        hourly_counts_df=hourly_counts,
        woof_sum=transaction_data.get_formatted_num(woof_sum),
        ton_sum=transaction_data.get_formatted_num(ton_sum),
        reached=reached,
        woof_betted=WOOF_BETTED
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        print(f'Error: {err}')


if __name__ == '__main__':
    asyncio.run(main(1))