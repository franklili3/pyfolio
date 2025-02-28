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
from math import copysign
import warnings
from collections import deque, OrderedDict

import pandas as pd
import numpy as np

from .utils import print_table, format_asset

PNL_STATS = OrderedDict(
    [('总净利润', lambda x: x.sum()),
     ('总盈利', lambda x: x[x > 0].sum()),
     ('总亏损', lambda x: x[x < 0].sum()),
     ('利润因子', lambda x: x[x > 0].sum() / x[x < 0].abs().sum()
      if x[x < 0].abs().sum() != 0 else np.nan),
     ('所有交易平均净利润', 'mean'),
     ('盈利交易平均净利润', lambda x: x[x > 0].mean()),
     ('亏损交易平均净利润', lambda x: x[x < 0].mean()),
     ('盈亏比率', lambda x: x[x > 0].mean() /
      x[x < 0].abs().mean() if x[x < 0].abs().mean() != 0 else np.nan),
     ('最大盈利', 'max'),
     ('最大亏损', 'min'),
     ])

SUMMARY_STATS = OrderedDict(
    [('总交易数', 'count'),
     ('盈利百分比', lambda x: len(x[x > 0]) / float(len(x))),
     ('盈利交易数', lambda x: len(x[x > 0])),
     ('亏损交易数', lambda x: len(x[x < 0])),
     ('平局交易数', lambda x: len(x[x == 0])),
     ])

RETURN_STATS = OrderedDict(
    [('所有交易的平均收益', lambda x: x.mean()),
     ('盈利交易的平均收益', lambda x: x[x > 0].mean()),
     ('亏损交易的平均收益', lambda x: x[x < 0].mean()),
     ('所有交易的中位数收益', lambda x: x.median()),
     ('盈利交易的中位数收益', lambda x: x[x > 0].median()),
     ('亏损交易的中位数收益', lambda x: x[x < 0].median()),
     ('最大盈利交易', 'max'),
     ('最大亏损交易', 'min'),
     ])

DURATION_STATS = OrderedDict(
    [('平均持续时间-天', lambda x: x.mean().days),
     ('中位数持续时间-天', lambda x: x.median().days),
     ('最长持续时间-天', lambda x: x.max().days),
     ('最短持续时间-天', lambda x: x.min().days)
     #  FIXME: Instead of x.max() - x.min() this should be
     #  rts.close_dt.max() - rts.open_dt.min() which is not
     #  available here. As it would require a new approach here
     #  that passes in multiple fields we disable these measures
     #  for now.
     #  ('平均每日回合交易数', lambda x: float(len(x)) /
     #   (x.max() - x.min()).days),
     #  ('平均每月回合交易数', lambda x: float(len(x)) /
     #   (((x.max() - x.min()).days) / APPROX_BDAYS_PER_MONTH)),
     ])


def agg_all_long_short(round_trips, col, stats_dict):
    stats_all = (round_trips
                 .assign(ones=1)
                 .groupby('ones')[col]
                 .agg([
                     (key, func) for key, func in stats_dict.items()
                 ])
                 .T
                 .rename(columns={1: '所有交易'}))
    # print('stats_all: ', stats_all.head())
    stats_long_short = (round_trips
                        .groupby('long')[col]
                        .agg([
                            (key, func) for key, func in stats_dict.items()
                        ])
                        .T
                        .rename(columns={False: '做空交易',
                                         True: '做多交易'}))

    return stats_all.join(stats_long_short)


def _groupby_consecutive(txn, max_delta=pd.Timedelta('8h')):
    """Merge transactions of the same direction separated by less than
    max_delta time duration.

    Parameters
    ----------
    transactions : pd.DataFrame
        Prices and amounts of executed round_trips. One row per trade.
        - See full explanation in tears.create_full_tear_sheet

    max_delta : pandas.Timedelta (optional)
        Merge transactions in the same direction separated by less
        than max_delta time duration.


    Returns
    -------
    transactions : pd.DataFrame

    """
    def vwap(transaction):
        if transaction.amount.sum() == 0:
            warnings.warn('Zero transacted shares, setting vwap to nan.')
            return np.nan
        return (transaction.amount * transaction.price).sum() / \
            transaction.amount.sum()

    out = []
    # print('txn: ', txn.head())
    for _, t in txn.groupby('symbol'):
        t = t.sort_index()
        t.index.name = 'dt'
        t = t.reset_index()

        t['order_sign'] = t.amount > 0
        t['block_dir'] = (t.order_sign.shift(
            1) != t.order_sign).astype(int).cumsum()
        t['block_time'] = ((t.dt.sub(t.dt.shift(1))) >
                           max_delta).astype(int).cumsum()
        grouped_price = (t.groupby(['block_dir',
                                   'block_time'])
                          .apply(vwap))
        grouped_price.name = 'price'
        grouped_rest = t.groupby(['block_dir', 'block_time']).agg({
            'amount': 'sum',
            'symbol': 'first',
            'dt': 'first'})

        grouped = grouped_rest.join(grouped_price)

        out.append(grouped)
    # print('out: ', out)

    out1 = pd.concat(out)
    # print('out1: ', out1)
    out2 = out1.set_index('dt')
    return out2


def extract_round_trips(transactions,
                        portfolio_value=None):
    """Group transactions into "round trips". First, transactions are
    grouped by day and directionality. Then, long and short
    transactions are matched to create round-trip round_trips for which
    PnL, duration and returns are computed. Crossings where a position
    changes from long to short and vice-versa are handled correctly.

    Under the hood, we reconstruct the individual shares in a
    portfolio over time and match round_trips in a FIFO-order.

    For example, the following transactions would constitute one round trip:
    index                  amount   price    symbol
    2004-01-09 12:18:01    10       50      'AAPL'
    2004-01-09 15:12:53    10       100      'AAPL'
    2004-01-13 14:41:23    -10      100      'AAPL'
    2004-01-13 15:23:34    -10      200       'AAPL'

    First, the first two and last two round_trips will be merged into a two
    single transactions (computing the price via vwap). Then, during
    the portfolio reconstruction, the two resulting transactions will
    be merged and result in 1 round-trip trade with a PnL of
    (150 * 20) - (75 * 20) = 1500.

    Note, that round trips do not have to close out positions
    completely. For example, we could have removed the last
    transaction in the example above and still generated a round-trip
    over 10 shares with 10 shares left in the portfolio to be matched
    with a later transaction.

    Parameters
    ----------
    transactions : pd.DataFrame
        Prices and amounts of executed round_trips. One row per trade.
        - See full explanation in tears.create_full_tear_sheet

    portfolio_value : pd.Series (optional)
        Portfolio value (all net assets including cash) over time.
        Note that portfolio_value needs to beginning of day, so either
        use .shift() or positions.sum(axis='columns') / (1+returns).

    Returns
    -------
    round_trips : pd.DataFrame
        DataFrame with one row per round trip.  The returns column
        contains returns in respect to the portfolio value while
        rt_returns are the returns in regards to the invested capital
        into that partiulcar round-trip.
    """
    print('transactions: ', transactions.head())

    transactions_consecutive = _groupby_consecutive(transactions)
    roundtrips = []
    print('transactions_consecutive: ', transactions_consecutive.head())
    transactions_symbol = transactions_consecutive.groupby('symbol')
    print('transactions_symbol: ', transactions_symbol.head())

    for sym, trans_sym in transactions_symbol:
        trans_sym = trans_sym.sort_index()
        price_stack = deque()
        dt_stack = deque()
        trans_sym['signed_price'] = trans_sym.price * \
            np.sign(trans_sym.amount)
        trans_sym['abs_amount'] = trans_sym.amount.abs().astype(int)
        print('trans_sym: ', trans_sym.head())

        for dt, t in trans_sym.iterrows():
            if t.price < 0:
                warnings.warn('Negative price detected, ignoring for'
                              'round-trip.')
                continue

            indiv_prices = [t.signed_price] * t.abs_amount

            if (len(price_stack) == 0) or \
               (copysign(1, price_stack[-1]) == copysign(1, t.amount)):
                price_stack.extend(indiv_prices)
                dt_stack.extend([dt] * len(indiv_prices))
            else:
                # Close round-trip
                pnl = 0
                invested = 0
                cur_open_dts = []

                for price in indiv_prices:
                    if len(price_stack) != 0 and \
                       (copysign(1, price_stack[-1]) != copysign(1, price)):
                        # Retrieve first dt, stock-price pair from
                        # stack
                        prev_price = price_stack.popleft()
                        prev_dt = dt_stack.popleft()

                        pnl += -(price + prev_price)
                        cur_open_dts.append(prev_dt)
                        invested += abs(prev_price)

                    else:
                        # Push additional stock-prices onto stack
                        price_stack.append(price)
                        dt_stack.append(dt)
                print('pnl: ', pnl)
                print('open_dt: ', cur_open_dts[0])
                print('close_dt: ', dt)
                print('long: ', price < 0)
                print('rt_returns: ', pnl / invested)
                print('symbol: ', sym)

                roundtrips.append({'pnl': pnl,
                                   'open_dt': cur_open_dts[0],
                                   'close_dt': dt,
                                   'long': price < 0,
                                   'rt_returns': pnl / invested,
                                   'symbol': sym,
                                   })

    roundtrips = pd.DataFrame(roundtrips)
    print('roundtrips: ', roundtrips.head())
    roundtrips['duration'] = roundtrips['close_dt'].sub(roundtrips['open_dt'])

    if portfolio_value is not None:
        # Need to normalize so that we can join
        pv = pd.DataFrame(portfolio_value,
                          columns=['portfolio_value'])\
            .assign(date=portfolio_value.index)

        roundtrips['date'] = roundtrips.close_dt.apply(lambda x:
                                                       x.replace(hour=0,
                                                                 minute=0,
                                                                 second=0))

        tmp = (roundtrips.set_index('date')
                         .join(pv.set_index('date'), lsuffix='_')
                         .reset_index())

        roundtrips['returns'] = tmp.pnl / tmp.portfolio_value
        roundtrips = roundtrips.drop('date', axis='columns')

    return roundtrips


def add_closing_transactions(positions, transactions):
    """
    Appends transactions that close out all positions at the end of
    the timespan covered by positions data. Utilizes pricing information
    in the positions DataFrame to determine closing price.

    Parameters
    ----------
    positions : pd.DataFrame
        The positions that the strategy takes over time.
    transactions : pd.DataFrame
        Prices and amounts of executed round_trips. One row per trade.
        - See full explanation in tears.create_full_tear_sheet

    Returns
    -------
    closed_txns : pd.DataFrame
        Transactions with closing transactions appended.
    """
    print('transactions_add_closing_transactions: ', transactions.head())

    closed_txns = transactions[['symbol', 'amount', 'price']]
    print('closed_txns: ', closed_txns.head())

    pos_at_end = positions.drop('cash', axis=1).iloc[-1]
    print('pos_at_end: ', pos_at_end.head())

    open_pos = pos_at_end.replace(0, np.nan).dropna()
    print('open_pos: ', open_pos.head())
    # Add closing round_trips one second after the close to be sure
    # they don't conflict with other round_trips executed at that time.
    end_dt = open_pos.name + pd.Timedelta(seconds=1)
    print('end_dt type: ', type(end_dt))
    end_dt = pd.Timestamp(end_dt)
    for sym_array, ending_val in open_pos.items():
        print('sym_array: ', sym_array)
        sym = sym_array[0]
        print('ending_val: ', ending_val)
        # 在提取交易符号之前，打印 transactions 的信息
        print('transactions 数据框的头部: ', transactions.head())
        print('transactions symbol列 的头部: ', transactions['symbol'].head())
        print('transactions 数据框的符号: ', transactions['symbol'].iloc[0,0])
        print('transactions 数据框的 symbol 列的数据类型: ', transactions['symbol'].dtypes)
        print('sym 的数据类型: ', type(sym))
        transactions['symbol'] = transactions['symbol'].apply(lambda x: x.str.strip())  # 去除空格
        transactions['symbol'] = transactions['symbol'].apply(lambda x: x.str.upper())  # 转换为大写
        sym = str(sym).strip().upper()  # 去除空格并转换为大写
        print('筛选条件 sym: ', sym)
        # 在提取 txn_sym 之前，检查是否有与 sym 匹配的记录
        txn_sym = transactions[transactions['symbol'] == sym]
        if txn_sym.empty:
            print(f'没有找到与符号 {sym} 匹配的交易记录。')
        else:
            print('找到的交易记录: ', txn_sym)
        # txn_sym = transactions[transactions['symbol'] == sym]
        # print('txn_sym: ', txn_sym)
        ending_amount = txn_sym.amount.sum()
        print('ending_amount: ', ending_amount)

        ending_price = ending_val / ending_amount
        print('ending_price: ', ending_price)
        #closing_txn = OrderedDict([
        #    ('amount', -ending_amount),
        #    ('price', ending_price),
        #    ('symbol', sym),
        #])
        closing_txn = pd.DataFrame({
            'amount': [-ending_amount],
            'price': [ending_price],
            'symbol': [sym]
        }, index=[end_dt])
        print('closing_txn: ', closing_txn)
        # closing_txn = pd.DataFrame(closing_txn, index=[end_dt])
        closed_txns1 = pd.concat([closed_txns, closing_txn])
    print('closed_txns1: ', closed_txns1.tail())

    #closed_txns = closed_txns[closed_txns.amount != 0]
    # Check if closed_txns is empty before filtering
    if not closed_txns.empty:
        # Ensure amount is numeric and filter
        closed_txns1['amount'] = pd.to_numeric(closed_txns1['amount'], errors='coerce')
        closed_txns2 = closed_txns1[closed_txns1['amount'] != 0]
    print('closed_txns1: ', closed_txns1.head())

    return closed_txns1


def apply_sector_mappings_to_round_trips(round_trips, sector_mappings):
    """
    Translates round trip symbols to sectors.

    Parameters
    ----------
    round_trips : pd.DataFrame
        DataFrame with one row per round trip trade.
        - See full explanation in round_trips.extract_round_trips
    sector_mappings : dict or pd.Series, optional
        Security identifier to sector mapping.
        Security ids as keys, sectors as values.

    Returns
    -------
    sector_round_trips : pd.DataFrame
        Round trips with symbol names replaced by sector names.
    """

    sector_round_trips = round_trips.copy()
    sector_round_trips.symbol = sector_round_trips.symbol.apply(
        lambda x: sector_mappings.get(x, 'No Sector Mapping'))
    sector_round_trips = sector_round_trips.dropna(axis=0)

    return sector_round_trips


def gen_round_trip_stats(round_trips):
    """Generate various round-trip statistics.

    Parameters
    ----------
    round_trips : pd.DataFrame
        DataFrame with one row per round trip trade.
        - See full explanation in round_trips.extract_round_trips

    Returns
    -------
    stats : dict
       A dictionary where each value is a pandas DataFrame containing
       various round-trip statistics.

    See also
    --------
    round_trips.print_round_trip_stats
    """

    stats = {}
    stats['pnl'] = agg_all_long_short(round_trips, 'pnl', PNL_STATS)
    stats['summary'] = agg_all_long_short(round_trips, 'pnl',
                                          SUMMARY_STATS)
    stats['duration'] = agg_all_long_short(round_trips, 'duration',
                                           DURATION_STATS)
    stats['returns'] = agg_all_long_short(round_trips, 'returns',
                                          RETURN_STATS)

    stats['symbols'] = \
        round_trips.groupby('symbol')['returns'].agg([
                    (key, func) for key, func in RETURN_STATS.items()
                    ]).T

    return stats


def print_round_trip_stats(round_trips, hide_pos=False):
    """Print various round-trip statistics. Tries to pretty-print tables
    with HTML output if run inside IPython NB.

    Parameters
    ----------
    round_trips : pd.DataFrame
        DataFrame with one row per round trip trade.
        - See full explanation in round_trips.extract_round_trips

    See also
    --------
    round_trips.gen_round_trip_stats
    """

    stats = gen_round_trip_stats(round_trips)

    print_table(stats['summary'], float_format='{:.2f}'.format,
                name='总览指标')
    print_table(stats['pnl'], float_format='{:.2f}'.format, name='盈亏指标')
    print_table(stats['duration'], float_format='{:.2f}'.format,
                name='持有期指标')
    print_table(stats['returns'] * 100, float_format='{:.2f}%'.format,
                name='收益指标')

    if not hide_pos:
        stats['symbols'].columns = stats['symbols'].columns.map(format_asset)
        print_table(stats['symbols'] * 100,
                    float_format='{:.2f}%'.format, name='交易品种指标')
