from jinja2 import Environment, FileSystemLoader
import pandas as pd


class HTMLReportGenerator:
    def __init__(self, template_path='data', template_name='template.html'):
        self.env = Environment(loader=FileSystemLoader(template_path))
        self.template = self.env.get_template(template_name)

    def generate_report(self, day, hourly_counts_df: pd.DataFrame, woof_sum, ton_sum, woof_price, output_file='report.html'):
        hourly_counts_df.set_index('date', inplace=True, drop=True)
        hourly_counts_df.index.name = None
        hourly_counts_table = hourly_counts_df.to_html(classes="hourly-counts-table", justify="center")

        html_content = self.template.render(
            day=day,
            hourly_counts_table=hourly_counts_table,
            woof_sum=woof_sum,
            ton_sum=ton_sum,
            woof_price=woof_price,
        )

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(html_content)

        print(f"HTML report generated: {output_file}")
