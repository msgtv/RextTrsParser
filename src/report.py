from jinja2 import Environment, FileSystemLoader
import pandas as pd


class HTMLReportGenerator:
    def __init__(self, template_path='data', template_name='template.html'):
        self.env = Environment(loader=FileSystemLoader(template_path))
        self.template = self.env.get_template(template_name)

    def generate_report(self, day, stats, hourly_counts_df, woof_sum, ton_sum, reached, woof_betted, output_file='report.html'):
        hourly_counts_table = hourly_counts_df.to_frame().to_html(classes="hourly-counts-table", justify="center")

        html_content = self.template.render(
            day=day,
            stats=stats,
            hourly_counts_table=hourly_counts_table,
            woof_sum=woof_sum,
            ton_sum=ton_sum,
            reached=reached,
            woof_betted=woof_betted
        )

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(html_content)

        print(f"HTML report generated: {output_file}")
