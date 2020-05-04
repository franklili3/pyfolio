# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 10:16:26 2019

@author: user
"""

import tushare as ts
#ts.set_token('ce9da8752a8227870a5125db27894418d3d6ef81d2bf0af6a20b1957')
f = ts.get_hist_data('hs300') #一次性获取全部日k线数据
#start = '2011/09/01'
#end = '2020/05/03'
#web.DataReader('000001.ss', 'yahoo')#stooq
#s = f[end: start]
#b = s.sort_index()
#b.to_csv('D:\\myprojects\\pyfolio\\000001_2011_09.csv')
