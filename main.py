# -*- coding: utf-8 -*-
"""
keypoint-cards（重点卡片）
==========================
把一篇文章的重点句子自动抽取出来，生成一组可直接打印 / 截图的 HTML 知识卡片。

用法：
    python main.py 文章.txt          # 默认生成 5 张卡片
    python main.py 文章.txt 8        # 生成 8 张卡片

只用 Python 标准库，无需安装任何第三方包。
核心思路（一句话版）：
    一篇文章里反复出现的字词组合，就是作者反复强调的概念；
    包含这些概念的句子，大概率就是重点句。
"""

import re
import sys
from datetime import date

# ================= 可调参数 =================

# 短于这个字符数的句子不参与评选（通常是过渡句、套话）
MIN_SENTENCE_LEN = 10

# 停用词：统计时忽略的无意义词（中文二字虚词 + 常见英文虚词）
STOPWORDS = {
    "一个", "一些", "一下", "一样", "已经", "正在", "不是", "都是", "也是",
    "我们", "你们", "他们", "她们", "自己", "什么", "这个", "那个", "这样",
    "那样", "这些", "那些", "可以", "应该", "因为", "所以", "但是", "然后",
    "就是", "还是", "如果", "即使", "虽然", "而且", "或者", "以及", "通过",
    "进行", "对于", "关于", "没有", "不能", "不会", "很多", "非常", "时候",
    "问题", "东西", "事情", "可能", "其实", "真的", "一定", "起来", "出来",
    "the", "and", "is", "of", "to", "in", "a", "it", "that", "for", "on",
    "with", "as", "are", "was", "be", "this", "or", "an", "we", "you",
    "they", "have", "has", "had", "not", "but", "can", "will", "by", "from",
}


# ================= 文本处理 =================

def read_text(path):
    """读取整个文本文件（要求 UTF-8 编码）。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_sentences(text):
    """按中英文句末标点切分句子，过滤太短的句子。"""
    parts = re.split(r"[。！？!?；;\n]+", text)
    return [p.strip() for p in parts if len(p.strip()) >= MIN_SENTENCE_LEN]


def extract_units(text):
    """
    提取"统计单元"（相当于简易分词）：
    - 中文：取相邻两字组成的组合（bigram），如「知识卡片」→ 知识/识卡/卡片
    - 英文：取长度≥2 的单词，统一转小写
    这样做不需要任何分词库，就能大致抓到"反复出现的概念"。
    """
    units = []
    for seg in re.findall(r"[\u4e00-\u9fff]+", text):
        for i in range(len(seg) - 1):
            units.append(seg[i:i + 2])
    for word in re.findall(r"[A-Za-z]{2,}", text):
        units.append(word.lower())
    return units


def unit_frequencies(units):
    """统计每个单元出现的次数，返回 {单元: 次数} 字典。"""
    freq = {}
    for u in units:
        freq[u] = freq.get(u, 0) + 1
    return freq


def keyword_units(sentence, freq):
    """取出句子里"有信息量"的单元：不在停用词表、且全文出现超过 1 次。"""
    return [u for u in extract_units(sentence)
            if u not in STOPWORDS and freq.get(u, 0) > 1]


def sentence_score(sentence, freq):
    """
    句子打分 = 关键单元在全文中的平均出现次数。
    用平均而不是总和，是为了避免长句子靠长度占便宜。
    """
    key_units = keyword_units(sentence, freq)
    if not key_units:
        return 0.0
    return sum(freq[u] for u in key_units) / len(key_units)


def top_keywords(sentence, freq, n=3):
    """取句子中得分最高的 n 个关键词，作为卡片的"关键词标签"。"""
    units = sorted(set(keyword_units(sentence, freq)),
                   key=lambda u: freq[u], reverse=True)
    return units[:n]


# ================= 卡片生成 =================

CARD_TEMPLATE = """
    <div class="card">
      <div class="card-head">
        <span class="no">#{no}</span>
        <span class="kws">{keywords}</span>
      </div>
      <p class="text">{sentence}</p>
    </div>"""


def build_html(cards, source_name):
    """把选出来的重点句渲染成一个独立 HTML 文件（内联样式，可离线打开）。"""
    cards_html = ""
    for idx, (sentence, keywords) in enumerate(cards, 1):
        kw_html = "".join(f'<span class="kw">{k}</span>' for k in keywords)
        cards_html += CARD_TEMPLATE.format(
            no=idx, keywords=kw_html, sentence=sentence)

    page = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>重点卡片 - """ + source_name + """</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f0f2f5; padding: 32px 16px; color: #1f2329;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .meta {{ color: #86909c; font-size: 13px; margin-bottom: 24px; }}
  .card {{
    background: #fff; border-radius: 12px; padding: 18px 20px;
    margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,.08);
  }}
  .card-head {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .no {{
    background: #165dff; color: #fff; font-size: 12px;
    border-radius: 6px; padding: 2px 8px; font-weight: bold;
  }}
  .kw {{
    background: #e8f3ff; color: #165dff; font-size: 12px;
    border-radius: 6px; padding: 2px 8px; margin-right: 4px;
  }}
  .text {{ font-size: 15px; line-height: 1.8; }}
  footer {{ text-align: center; color: #86909c; font-size: 12px; margin-top: 24px; }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .card {{ break-inside: avoid; box-shadow: none; border: 1px solid #e5e6eb; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>重点卡片</h1>
    <div class="meta">来源：""" + source_name + """ · 生成于 """ + date.today().isoformat() + """</div>
""" + cards_html + """
    <footer>由 keypoint-cards 生成 · 我的第一个开源项目</footer>
  </div>
</body>
</html>
"""
    return page


# ================= 主程序 =================

def main():
    # 1. 读取命令行参数
    if len(sys.argv) < 2:
        print("用法：python main.py 文章.txt [卡片数量]")
        print("示例：python main.py sample.txt 5")
        sys.exit(1)

    path = sys.argv[1]
    n_cards = 5
    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        n_cards = int(sys.argv[2])

    # 2. 读文章、切句子
    text = read_text(path)
    sentences = split_sentences(text)
    if not sentences:
        print("没有找到足够长的句子，换个文件试试？")
        sys.exit(1)

    # 3. 统计全文词频，给每个句子打分
    freq = unit_frequencies(extract_units(text))
    scored = [(sentence_score(s, freq), s) for s in sentences]

    # 4. 按分数取前 N 句，再按原文出现顺序排列
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:n_cards]
    top = [s for score, s in top if score > 0]
    top.sort(key=lambda s: text.find(s))

    if not top:
        print("文章太短或重复词太少，选不出重点句。")
        sys.exit(1)

    # 5. 渲染成 HTML 卡片
    import os
    source_name = os.path.basename(path)
    cards = [(s, top_keywords(s, freq)) for s in top]
    out_path = "cards.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(build_html(cards, source_name))

    print(f"完成！已生成 {len(cards)} 张重点卡片 → {out_path}")
    print("用浏览器打开即可查看，可打印或截图保存。")


if __name__ == "__main__":
    main()
