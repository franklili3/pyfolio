#
# Copyright 2016 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import division

import pandas as pd


def map_transaction(txn):
    """
    Maps a single transaction row to a dictionary.

    Parameters
    ----------
    txn : pd.DataFrame
        A single transaction object to convert to a dictionary.

    Returns
    -------
    dict
        Mapped transaction.
    """

    if isinstance(txn['sid'], dict):
        sid = txn['sid']['sid']
        symbol = txn['sid']['symbol']
    else:
        sid = txn['sid']
        symbol = txn['sid']

    return {'sid': sid,
            'symbol': symbol,
            'price': txn['price'],
            'order_id': txn['order_id'],
            'amount': txn['amount'],
            'commission': txn['commission'],
            'dt': txn['dt']}


def make_transaction_frame(transactions):
    """
    Formats a transaction DataFrame.

    Parameters
    ----------
    transactions : pd.DataFrame
        Contains improperly formatted transactional data.

    Returns
    -------
    df : pd.DataFrame
        Daily transaction volume and dollar ammount.
         - See full explanation in tears.create_full_tear_sheet.
    """

    transaction_list = []
    for dt in transactions.index:
        txns = transactions.loc[dt]
        if len(txns) == 0:
            continue

        for txn in txns:
            txn = map_transaction(txn)
            transaction_list.append(txn)
    df = pd.DataFrame(sorted(transaction_list, key=lambda x: x['dt']))
    df['txn_dollars'] = -df['amount'] * df['price']

    df.index = list(map(pd.Timestamp, df.dt.values))
    return df


def get_txn_vol(transactions):
    """
    Extract daily transaction data from set of transaction objects.

    Parameters
    ----------
    transactions : pd.DataFrame
        Time series containing one row per symbol (and potentially
        duplicate datetime indices) and columns for amount and
        price.

    Returns
    -------
    pd.DataFrame
        Daily transaction volume and number of shares.
         - See full explanation in tears.create_full_tear_sheet.
    """

    txn_norm = transactions.copy()
    #print('txn_norm: ', txn_norm.head())
    txn_norm.index = txn_norm.index.normalize()
        # 确保 'amount' 列存在
    if 'amount' not in txn_norm.columns:
        raise ValueError("transactions中缺少'amount'列")
    txn_norm['abs_amount'] = txn_norm['amount'].apply(lambda x: abs(x))
    #amounts = txn_norm['abs_amount']
    #print('amounts: ', amounts)
    # 检查是否为 Series
    #assert isinstance(amounts, pd.Series), "amounts不是一个Series"
    # 检查是否为 DataFrame
    #elif isinstance(amounts, pd.DataFrame):
    #    print("amounts是一个 DataFrame")    
    #print('amounts: ', amounts)
    #prices = txn_norm['price']
    #print('prices: ', prices)
    txn_norm.loc[:, 'values'] = txn_norm.apply(lambda row: row['abs_amount'] * row['price'], axis=1)
    #print('values: ', values)
    #txn_norm.loc[:, 'values'] = txn_norm['abs_amount'] * txn_norm['price']
    #print('values: ', values)
    amounts_values = txn_norm[['abs_amount', 'values']]
    #print('values: ', values)
    amounts_values = txn_norm[['abs_amount', 'values']]
    daily_amounts_values = amounts_values.groupby(amounts_values.index).sum()
    daily_amounts_values = daily_amounts_values.rename(columns={'abs_amount': 'txn_shares', 'values': 'txn_volume'})
    #daily_amounts = amounts.groupby(amounts.index).sum()
    #daily_values = values.groupby(values.index).sum()
    #daily_amounts.name = "txn_shares"
    #daily_values.name = "txn_volume"
    #print('daily_amounts_values: ', daily_amounts_values.head())
    #print('daily_amounts: ', daily_amounts)
    #return pd.concat([daily_values, daily_amounts], axis=1)
    return daily_amounts_values


def adjust_returns_for_slippage(returns, positions, transactions,
                                slippage_bps):
    """
    Apply a slippage penalty for every dollar traded.

    Parameters
    ----------
    returns : pd.Series
        Daily returns of the strategy, noncumulative.
         - See full explanation in create_full_tear_sheet.
    positions : pd.DataFrame
        Daily net position values.
         - See full explanation in create_full_tear_sheet.
    transactions : pd.DataFrame
        Prices and amounts of executed trades. One row per trade.
         - See full explanation in create_full_tear_sheet.
    slippage_bps: int/float
        Basis points of slippage to apply.

    Returns
    -------
    pd.Series
        Time series of daily returns, adjusted for slippage.
    """

    slippage = 0.0001 * slippage_bps
    portfolio_value = positions.sum(axis=1)
    pnl = portfolio_value * returns
    traded_txn = get_txn_vol(transactions)
    #print('traded_txn: ', traded_txn.head())
    traded_value = traded_txn.txn_volume
    # 确保索引对齐
    slippage_dollars_df = traded_value.reindex(pnl.index, fill_value=0) * slippage
    # 确保 slippage_dollars 是 Series
    if isinstance(slippage_dollars_df, pd.DataFrame):
        slippage_dollars = slippage_dollars_df.squeeze()  # 将 DataFrame 转换为 Series
    else:
        slippage_dollars = slippage_dollars_df
    #slippage_dollars = slippage_dollars_df['txn_volume']
    #print('slippage_dollars: ', slippage_dollars.head())
    assert isinstance(slippage_dollars, pd.Series), 'slippage_dollars must be a pd.Series'
    # 调试输出
    #print('pnl: ', pnl.head())
    #slippage_dollars = traded_value * slippage
    #adjusted_pnl = pnl.add(-slippage_dollars, fill_value=0)
    adjusted_pnl = pnl - slippage_dollars
    adjusted_returns = returns * adjusted_pnl / pnl

    return adjusted_returns


def get_turnover(positions, transactions, denominator='AGB'):
    """
     - Value of purchases and sales divided
    by either the actual gross book or the portfolio value
    for the time step.

    Parameters
    ----------
    positions : pd.DataFrame
        Contains daily position values including cash.
        - See full explanation in tears.create_full_tear_sheet
    transactions : pd.DataFrame
        Prices and amounts of executed trades. One row per trade.
        - See full explanation in tears.create_full_tear_sheet
    denominator : str, optional
        Either 'AGB' or 'portfolio_value', default AGB.
        - AGB (Actual gross book) is the gross market
        value (GMV) of the specific algo being analyzed.
        Swapping out an entire portfolio of stocks for
        another will yield 200% turnover, not 100%, since
        transactions are being made for both sides.
        - We use average of the previous and the current end-of-period
        AGB to avoid singularities when trading only into or
        out of an entire book in one trading period.
        - portfolio_value is the total value of the algo's
        positions end-of-period, including cash.

    Returns
    -------
    turnover_rate : pd.Series
        timeseries of portfolio turnover rates.
    """

    txn_vol = get_txn_vol(transactions)
    #print(txn_vol.head())  # Check the structure of the DataFrame
    traded_value = txn_vol.txn_volume

    if denominator == 'AGB':
        # Actual gross book is the same thing as the algo's GMV
        # We want our denom to be avg(AGB previous, AGB current)
        AGB = positions.drop('cash', axis=1).abs().sum(axis=1)
        denom = AGB.rolling(2).mean()

        # Since the first value of pd.rolling returns NaN, we
        # set our "day 0" AGB to 0.
        denom.iloc[0] = AGB.iloc[0] / 2
    elif denominator == 'portfolio_value':
        denom = positions.sum(axis=1)
    else:
        raise ValueError(
            "Unexpected value for denominator '{}'. The "
            "denominator parameter must be either 'AGB'"
            " or 'portfolio_value'.".format(denominator)
        )

    denom.index = denom.index.normalize()
    turnover = traded_value.div(denom, axis='index')
    turnover = turnover.fillna(0)
    return turnover
