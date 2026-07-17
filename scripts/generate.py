# -*- coding: utf-8 -*-
"""GitHub Actions 每天跑：抓源 → DeepSeek 出稿 → 写 briefing.json。"""
import os, json, base64, datetime, urllib.request, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
NEWSNOW = ["weibo","douyin","baidu","zhihu","bilibili-hot-search","toutiao","thepaper","ifeng","wallstreetcn-hot","cls-hot"]
RSSHUB = "https://rsshub-hotspot.onrender.com"
RSS_ROUTES = ["/adquan","/36kr/newsflashes"]
HEADS = {"龙秋帆":"longqiufan","孙旭":"sunxu25","赵雨婷":"zhaoyuting32","邵子益":"shaoziyi.3","刘柳":"liuliu41","王洪晶":"wanghongjing1","关楚凡":"guanchufan1","陈卓":"chenzhuo108","戴宜哲":"daiyizhe1","杨岭":"yangling62","申雯萱":"","王畅":"wangchang50"}

def bj_now(): return datetime.datetime.utcnow()+datetime.timedelta(hours=8)
def readfile(p):
    try: return open(p,encoding="utf-8").read()
    except Exception: return ""
def fetch(url,timeout=30):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read().decode("utf-8","replace")
def hot_lists():
    out=[]
    for pid in NEWSNOW:
        try:
            d=json.loads(fetch("https://newsnow.busiyi.world/api/s?id=%s&latest"%pid))
            ts=[it.get("title","").strip() for it in d.get("items",[])][:15]; ts=[t for t in ts if t]
            if ts: out.append("【%s】%s"%(pid," / ".join(ts)))
        except Exception: pass
    return "\n".join(out)
def rss_titles():
    out=[]
    for rt in RSS_ROUTES:
        for _ in range(3):
            try:
                xml=fetch(RSSHUB+rt,timeout=70)
                ts=re.findall(r"<title>(.*?)</title>",xml,re.S)[1:13]
                ts=[re.sub(r"<!\[CDATA\[|\]\]>","",t).strip() for t in ts]; ts=[t for t in ts if t]
                if ts: out.append("【%s】%s"%(rt," / ".join(ts))); break
            except Exception: continue
    return "\n".join(out)
def yesterday():
    try: return json.loads(readfile(os.path.join(REPO,"briefing.json"))).get("briefing_body","")
    except Exception: return ""
def deepseek(prompt):
    key=os.environ["DEEPSEEK_API_KEY"]
    body=json.dumps({"model":"deepseek-chat","messages":[{"role":"user","content":prompt}],"temperature":0.7,"max_tokens":4000}).encode("utf-8")
    req=urllib.request.Request("https://api.deepseek.com/chat/completions",data=body,headers={"Content-Type":"application/json","Authorization":"Bearer "+key},method="POST")
    with urllib.request.urlopen(req,timeout=180) as r: return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]

def build_prompt():
    _dl=os.environ.get("DILIAO_B64","")
    diliao=""
    if _dl:
        try:
            diliao=base64.b64decode(_dl).decode("utf-8")
        except Exception:
            diliao=_dl  # 用户直接贴了中文原文，非base64
    if not diliao:
        diliao=readfile(os.path.join(REPO,"diliao.md"))
    today=bj_now().strftime("%Y-%m-%d")
    dx=[t.strip() for t in readfile(os.path.join(REPO,"dingxiang.txt")).splitlines() if t.strip() and not t.strip().startswith("#")]
    jd="\n".join(l for l in readfile(os.path.join(REPO,"jingdui.txt")).splitlines() if l.strip() and not l.strip().startswith("#"))
    return (diliao+"\n\n=== 以上是部门底料，据此筛选/路由/按第八节格式与铁律写 ===\n\n"
        +"今天日期："+today+"\n昨天那版播报（不要重复，除非有大变化）：\n"+yesterday()[:3000]+"\n\n"
        +"定向必盯词："+("、".join(dx) if dx else "无")+"\n\n"
        +"竞对手动喂料（每条必收进竞对板块）：\n"+(jd or "（今天为空）")+"\n\n"
        +"全网热榜：\n"+hot_lists()+"\n\n"
        +"营销垂媒/行业(广告门+36氪)：\n"+rss_titles()+"\n\n"
        +"写一份【营销热点日报 · "+today+"】：首行 `# 营销热点日报 · "+today+"`；二行'今天最值得关注的：…'不带括号；6板块每板块≤2条精选；每条'【看得懂标题】：一两句。@花名 关注，可考虑…'，@直接跟花名不加'建议'不带部门名；标题正文说人话不用黑话、绝不写'（窗口X）'；@后建议要礼貌简短、商量口吻，不批评不甩锅不教训（不写'别再…''别只…''别被…盖过'这类）；竞对板块务必含喂料线索；结尾'以上各业务侧可参考&评估跟进~'另起一行'内容由AI助手整理发布，有问题或建议请随时联系huke1。'。只输出播报正文。")

def main():
    body=deepseek(build_prompt()).strip()
    if body.startswith("```"):
        body=body.strip("`"); body=body.split("\n",1)[1] if "\n" in body else body
    names=re.findall(r"@([^\s，,、：:；;（）()@]+)",body); erps=[]
    for n in names:
        e=HEADS.get(n,"")
        if e and e not in erps: erps.append(e)
    dx=[t.strip() for t in readfile(os.path.join(REPO,"dingxiang.txt")).splitlines() if t.strip() and not t.strip().startswith("#")]
    out={"briefing_body":body,"default_erps":erps,"topics":dx,"updated_at":bj_now().strftime("%Y-%m-%d %H:%M")}
    open(os.path.join(REPO,"briefing.json"),"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False))
    print("done",out["updated_at"])

if __name__=="__main__": main()
