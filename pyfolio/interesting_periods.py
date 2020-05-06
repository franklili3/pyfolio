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

"""Generates a list of historical event dates that may have had
significant impact on markets.  See extract_interesting_date_ranges."""

import pandas as pd

from collections import OrderedDict

PERIODS = OrderedDict()
# Dotcom bubble
PERIODS['Dotcom'] = (pd.Timestamp('20000310'), pd.Timestamp('20000910'))

# 9/11
PERIODS['9/11'] = (pd.Timestamp('20010911'), pd.Timestamp('20011011'))

# 01/08/03  US Housing Bubble 2003
PERIODS['US Housing'] = (
    pd.Timestamp('20030108'), pd.Timestamp('20030208'))

# Market regimes
PERIODS['Low Volatility Bull Market'] = (pd.Timestamp('20050101'),
                                         pd.Timestamp('20070801'))

# August 2007, March and September of 2008, Q1 & Q2 2009,
PERIODS['Fall2007'] = (pd.Timestamp('20071001'), pd.Timestamp('20081031'))
PERIODS['Mar2008'] = (pd.Timestamp('20080301'), pd.Timestamp('20080401'))

# Lehmann Brothers
PERIODS['June2008'] = (pd.Timestamp('20080601'), pd.Timestamp('20080630'))

PERIODS['Fall2009'] = (pd.Timestamp('20090801'), pd.Timestamp('20090831'))

PERIODS['Fall2010'] = (
    pd.Timestamp('20100401'), pd.Timestamp('20100630'))

PERIODS['Fall2011'] = (pd.Timestamp('20110901'),
                                            pd.Timestamp('20111230'))

PERIODS['Fall2012'] = (
    pd.Timestamp('20120601'), pd.Timestamp('20121130'))


# Market down-turn in August/Sept 2015
PERIODS['Fall2015'] = (pd.Timestamp('20150601'), pd.Timestamp('20150930'))

PERIODS['Fall2016'] = (pd.Timestamp('20160101'), pd.Timestamp('20160129'))

PERIODS['Fall2018'] = (pd.Timestamp('20180201'), pd.Timestamp('20181228'))

PERIODS['New Normal'] = (pd.Timestamp('20190101'),
                         pd.Timestamp('today'))
