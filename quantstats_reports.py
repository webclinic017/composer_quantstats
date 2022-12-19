import datetime
import re
import tempfile

import pandas as pd
import quantstats
import streamlit as st

from compose_symphony_parser.lib import (
    get_backtest_data,
    symphony_backtest,
    symphony_object,
)

st.set_page_config(
    page_title="Strategy tracking and analyzing", page_icon="💰", layout="wide"
)
st.title("Strategy Quantstats report generator")
st.write("This page generates quantstats reports for the selected strategy.")

st.info(
    """This website is not endorsed by or affiliated with [Composer Technologies Inc.](https://www.composer.trade). The data provided might contain errors and I'm not liable for any errors or misuse. Always exercise due diligence before using the data for your investment decisions. None of the informations displayed on this page and on the website as a whole constitute financial advice or any type of advice. """
)
symphony_url = st.text_input("Symphony URL", "", help="Enter your Symphony link here")
benchmark_ticker = st.text_input(
    "Benchmark ticker", "SPY", help="Enter benchmark ticker here"
)
# Fetch Benchmark Data
closes = get_backtest_data.get_backtest_data(set([benchmark_ticker]))
closes.index = pd.to_datetime(closes.index, utc=True).tz_localize(None)
earliest_benchmark_day = closes[benchmark_ticker].index.min().date()
# TODO: improve start and end date accuracy in reports, catch exceptions
backtest_start = st.date_input(
    "Backtest start date",
    value=datetime.date(1993, 1, 29),
    min_value=earliest_benchmark_day,
    max_value=datetime.date.today(),
)

choose_custom_end_date = st.checkbox("Choose a custom end date", value=False)
if choose_custom_end_date:
    backtest_end = st.date_input(
        "Backtest end date", datetime.date.today(), max_value=datetime.date.today()
    )

# Fetch Symphony
@st.experimental_memo
def find_symphony_id(symphony_url):
    m = re.search("\/symphony\/([^\/]+)", symphony_url)
    if m is None:
        return None
    symphony_id = m.groups(1)[0]
    return symphony_id


symphony_id = find_symphony_id(symphony_url)
if symphony_id is not None:
    st.header("Download Quantstats report")
    symphony = symphony_object.get_symphony(symphony_id)
    symphony_name = symphony["fields"]["name"]["stringValue"]
    st.info(symphony_name)

    # Get Composer Backtest Results
    if choose_custom_end_date:
        backtest_result = symphony_backtest.get_composer_backtest_results(
            symphony_id, backtest_start, backtest_end
        )
    else:
        backtest_result = symphony_backtest.get_composer_backtest_results(
            symphony_id, backtest_start
        )
    returns = symphony_backtest.extract_returns_from_composer_backtest_result(
        backtest_result, symphony_id
    )
    # TODO: Display the backtest stats on the page itself
    # Export Quantstats HTML Report
    keepcharacters = (" ", ".", "_", "-")
    filepath = f"{symphony_name}.html"
    filepath = filepath.replace("%", "pct ")
    filepath = "".join(
        c for c in filepath if c.isalnum() or c in keepcharacters
    ).rstrip()

    # create a tempdir in ram and store the output of quantstats.reports.html there
    temp_dir = tempfile.TemporaryDirectory()
    quantstats.reports.html(
        returns,
        closes[benchmark_ticker].pct_change().dropna(),
        title=f"{symphony_name}",
        output=f"{temp_dir.name}/{filepath}",
        download_filename=f"{temp_dir.name}/{filepath}",
    )
    with open(f"{temp_dir.name}/{filepath}") as file:
        st.download_button(
            label="Download HTML report",
            data=file,
            file_name=filepath,
            mime="text/html",
        )
    #    use temp_dir, and when done:
    temp_dir.cleanup()
    st.success(
        "Your report is ready for download. Click the button above to download it."
    )
# TODO: open the report automatically in another tab
# TODO: download the report as a pdf
