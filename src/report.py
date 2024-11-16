from jinja2 import Environment, FileSystemLoader
import pandas as pd


class HTMLReportGenerator:
    def __init__(self, template_path='data', template_name='template.html'):
        self.env = Environment(loader=FileSystemLoader(template_path))
        self.template = self.env.get_template(template_name)

    def generate_report(self, day, trs_stat: pd.DataFrame, big_bet_stat: pd.DataFrame, big_bet_volume, woof_sum, ton_sum, woof_price, output_file='report.html'):
        trs_stat.set_index('date', inplace=True, drop=True)
        trs_stat.index.name = None
        trs_stat_table = trs_stat.to_html(classes="hourly-counts-table", justify="center")

        big_bet_stat = big_bet_stat.values.tolist()

        html_content = self.template.render(
            day=day,
            trs_stat_table=trs_stat_table,
            big_bet_stat=big_bet_stat,
            big_bet_volume=big_bet_volume,
            woof_sum=woof_sum,
            ton_sum=ton_sum,
            woof_price=woof_price,
        )

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(html_content)

        print(f"HTML report generated: {output_file}")
