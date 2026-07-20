# -*- coding: utf-8 -*-
"""GitHub Actions 每天跑：抓源 → DeepSeek 出稿 → 写 briefing.json。"""
import os, json, base64, datetime, urllib.request, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
NEWSNOW = ["weibo","douyin","baidu","zhihu","bilibili-hot-search","toutiao","thepaper","ifeng","wallstreetcn-hot","cls-hot"]
RSSHUB = "https://rsshub-hotspot.onrender.com"
RSS_ROUTES = ["/adquan","/36kr/newsflashes"]
HEADS = {"龙秋帆":"longqiufan","孙旭":"sunxu25","赵雨婷":"zhaoyuting32","邵子益":"shaoziyi.3","刘柳":"liuliu41","王洪晶":"wanghongjing1","关楚凡":"guanchufan1","陈卓":"chenzhuo108","戴宜哲":"daiyizhe1","杨岭":"yangling62","申雯萱":"","王畅":"wangchang50"}

# 对接人分工路由表（让模型@对人，不@错不@泛）
ROUTING = (
"【对接人分工·按业务@对的人（只@下面这些花名）】\n"
"龙秋帆=平台营销部：大促/明星/IP/体育赛事/看球季/综艺\n"
"孙旭=家电家居：家电/家居/3C大家电/智能家居\n"
"赵雨婷=3C数码：手机/电脑/平板/耳机手表/游戏设备/AI硬件/苹果华为新品\n"
"邵子益=大商超：商超/生鲜果蔬/食品饮料/日用快消/烘焙/酒水\n"
"刘柳=大时尚：服饰/鞋包/运动户外/美妆护肤/珠宝\n"
"王洪晶=健康与自有品牌：医药/保健/健康/医美（法规敏感，谨慎）\n"
"关楚凡=企业营销：外卖/酒旅/秒送/本地生活/餐饮到家\n"
"陈卓=跨境业务与汽车：全球购/进口好物/跨境/汽车\n"
"戴宜哲=品牌部：品牌策划/campaign/品牌传播打法\n"
"杨岭=综合媒体官号：官方账号趣味/科普/话题互动内容\n"
"王畅=小红书官号：小红书种草/出片/达人内容\n"
)

def bj_now(): return datetime.datetime.utcnow()+datetime.timedelta(hours=8)
def readfile(p):
    try: return open(p,encoding="utf-8").read()
    except Exception: return ""
def fetch(url,timeout=30):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read().decode("utf-8","replace")
def hot_lists():
    # 带简介(hover)喂料：百度/知乎等平台的条目自带摘要，喂进去让模型抓准“为什么火、怎么接”
    out=[]
    for pid in NEWSNOW:
        try:
            d=json.loads(fetch("https://newsnow.busiyi.world/api/s?id=%s&latest"%pid))
            rows=[]
            for it in d.get("items",[])[:13]:
                t=(it.get("title") or "").strip()
                if not t: continue
                ex=it.get("extra") or {}
                hv=(ex.get("hover") or "").strip()
                hv=re.sub(r"\s+"," ",hv)
                rows.append("· "+t+("——"+hv[:90] if hv else ""))
            if rows: out.append("【%s】\n"%pid+"\n".join(rows))
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
    body=json.dumps({"model":"deepseek-chat","messages":[{"role":"user","content":prompt}],"temperature":0.6,"max_tokens":4000}).encode("utf-8")
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
    return (diliao+"\n\n=== 以上是部门底料，据此筛选/路由/按格式与铁律写 ===\n\n"
        +ROUTING+"\n"
        +"今天日期："+today+"\n昨天那版播报（今天不要重复同一话题，除非有新数据/新进展/新对阵/新争议/新梗）：\n"+yesterday()[:3000]+"\n\n"
        +"定向必盯词："+("、".join(dx) if dx else "无")+"\n\n"
        +"竞对手动喂料：\n"+(jd or "（今天为空）")+"\n\n"
        +"全网热榜（含简介，据此判断为什么火、怎么接）：\n"+hot_lists()+"\n\n"
        +"营销垂媒/行业(广告门+36氪)：\n"+rss_titles()+"\n\n"
        +"写一份【营销热点日报 · "+today+"】，严格按下列铁律：\n"
        +"1) 首行 `# 营销热点日报 · "+today+"`；二行『今天最值得关注的：…』不带括号补充。\n"
        +"2) 固定6板块（社会民生/体育赛事/娱乐明星/科技数码/消费生活/竞对营销），**每板块最多2条、精选**。\n"
        +"3) **板块没真料就整块省略**：某板块当天没有真实、有增量的内容就不出这个板块。\n"
        +"4) **竞对营销板块**：只有真实竞对/品牌营销案例（来自竞对喂料或广告门/36氪垂媒）才出；**没有就整块省略，绝不写『营销圈热议』『通道受限』『暂未抓到』这类占位废话硬凑，更不为了凑内容@人**。\n"
        +"5) **@必须对应一条真实、且有行动价值的热点**；没有值得某业务行动的点就不@。@只用上面路由表里的花名、按业务@对人；@直接跟花名、不加『建议』二字、不带部门名。\n"
        +"6) 每条格式：『【看得懂的标题】：一两句人话。@花名 关注，可考虑…』。建议要礼貌、简短、商量口吻、点到为止一句话；**不批评/不甩锅/不教训**（不写『别再…』『别只…』『别被…盖过』这类否定式）。\n"
        +"7) **说人话**：标题正文都用大白话、不懂行的人一眼看懂；**禁黑话缩写**（站内承接/导成/对位/心智/UGC/进站搜索等换成人话）；**绝不写『（窗口X/X前）』这类项目传播时间**。\n"
        +"8) **重大灾害/伤亡/讣告**（山体崩塌、地震、事故、名人去世等）：只客观简述、当一条热点让大家知道即可，**不@任何对接人、不给任何营销建议**（尺度难控、不消费苦难）。\n"
        +"9) 剔除『内部尽人皆知的自家事』纯复述（如某合作是京东独家），除非有新增量。\n"
        +"10) 结尾固定两行：『以上各业务侧可参考&评估跟进~』 和 『内容由AI助手整理发布，有问题或建议请随时联系huke1。』。\n"
        +"只输出播报正文，不要任何解释或代码块标记。")

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
