![pyfolio](https://media.quantopian.com/logos/open_source/pyfolio-logo-03.png "pyfolio")

# pyfolio

[![Join the chat at https://gitter.im/quantopian/pyfolio](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/quantopian/pyfolio?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![build status](https://travis-ci.org/quantopian/pyfolio.png?branch=master)](https://travis-ci.org/quantopian/pyfolio)

pyfolio 是一个由
[Quantopian Inc](https://www.quantopian.com)开发的投资组合的业绩和风险分析的Python库。 它可以与开源回测库
[Zipline](https://www.zipline.io/)一起工作。
Quantopian 也为专业人士提供一个 [完全管理的服务](https://factset.quantopian.com)，它包含 Zipline, Alphalens, Pyfolio, FactSet数据等。 

pyfolio的核心是一份报告，它由各种单独的图像组成，这些图像提供了交易算法的业绩和风险分析。这是一个简单策略分析报告的例子：

![简单报告 0](https://github.com/quantopian/pyfolio/raw/master/docs/simple_tear_0.png "由 Zipline 算法创建的报告案例")
![简单报告 1](https://github.com/quantopian/pyfolio/raw/master/docs/simple_tear_1.png "由 Zipline 算法创建的报告案例")

也可以参考 [slides of a talk about
pyfolio](https://nbviewer.jupyter.org/format/slides/github/quantopian/pyfolio/blob/master/pyfolio/examples/pyfolio_talk_slides.ipynb#/).

## 中文版
此库为Quantopian的pyfolio库的中文版，原库地址为：https://github.com/quantopian/pyfolio
报告中的中文为本人翻译，其他部分为原库内容。

![业绩统计数据](https://github.com/franklili3/pyfolio/raw/master/docs/业绩统计数据.png "由 franklili3 创建的钱翻一番算法报告案例")

![最差回撤期间](https://github.com/franklili3/pyfolio/raw/master/docs/最差回撤期间.png "由 franklili3 创建的钱翻一番算法报告案例")

![累计收益率](https://github.com/franklili3/pyfolio/raw/master/docs/累计收益率.png "由 franklili3 创建的钱翻一番算法报告案例")

![累计收益率对数](https://github.com/franklili3/pyfolio/raw/master/docs/累计收益率对数.png "由 franklili3 创建的钱翻一番算法报告案例")

![日收益率](https://github.com/franklili3/pyfolio/raw/master/docs/日收益率.png "由 franklili3 创建的钱翻一番算法报告案例")

![波动率](https://github.com/franklili3/pyfolio/raw/master/docs/波动率.png "由 franklili3 创建的钱翻一番算法报告案例")

![夏普比率](https://github.com/franklili3/pyfolio/raw/master/docs/夏普比率.png "由 franklili3 创建的钱翻一番算法报告案例")

![最大5个回撤期间](https://github.com/franklili3/pyfolio/raw/master/docs/最大5个回撤期间.png "由 franklili3 创建的钱翻一番算法报告案例")

![月收益率](https://github.com/franklili3/pyfolio/raw/master/docs/月收益率.png "由 franklili3 创建的钱翻一番算法报告案例")

![日周月收益率四分位](https://github.com/franklili3/pyfolio/raw/master/docs/日周月收益率四分位.png "由 franklili3 创建的钱翻一番算法报告案例")

## 安装

要安装 pyfolio, 请运行:

```bash
pip install pyfolio
```

#### 开发

想开发，可以使用一个 [虚拟环境](https://docs.python-guide.org/en/latest/dev/virtualenvs/) 避免与你其他项目的依赖冲突。要设置一个虚拟环境，请运行:
```bash
mkvirtualenv pyfolio
```

下一步, 克隆此库，并且运行 
```python setup.py develop
```
，然后直接编辑库文件。

下一步，更新版本，请运行
```pip install versioneer
versioneer install
git add .
git commit -m "Update version"
python setup.py -V
```

#### 在 OSX 上的 Matplotlib 

如果你在 OSX 上，并且使用一个非框架的 Python 的话，你可能需要设置你的后端:
``` bash
echo "backend: TkAgg" > ~/.matplotlib/matplotlibrc
```

## 使用

一个开始的好方法是在 [Jupyter notebook](https://jupyter.org/) 上运行 pyfolio 案例。你首先要启动一个 Jupyter notebook 服务器:

```bash
jupyter notebook
```

从笔记本列表页面，导航到pyfolio示例目录，打开笔记本。通过单击笔记本单元格中的代码来执行它
然后按下Shift+Enter键。


## 有问题?

如果你发现了一个 bug, 在此库[新建一个 issue](https://github.com/quantopian/pyfolio/issues) 

你也可以加入我们的 [邮件列表](https://groups.google.com/forum/#!forum/pyfolio) 或者我们的 [Gitter 频道](https://gitter.im/quantopian/pyfolio).

## 支持

请 [新建一个 issue](https://github.com/quantopian/pyfolio/issues/new) 获取支持。

## 贡献

如果你想贡献代码或想法，请先看 [标记为 help-wanted 的 issues](https://github.com/quantopian/pyfolio/issues?q=is%3Aopen+is%3Aissue+label%3A%22help+wanted%22).

核心开发者和外部协作者列表见 [ GitHub 贡献者列表](https://github.com/quantopian/pyfolio/graphs/contributors).
