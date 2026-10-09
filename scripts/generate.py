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
    diliao=""
    _b64=os.environ.get("DILIAO_B64","").strip()
    if _b64:
        try: diliao=base64.b64decode(_b64).decode("utf-8")
        except Exception: diliao=""
    if not diliao: diliao=readfile(os.path.join(REPO,"diliao.md"))
    today=bj_now().strftime("%Y-%m-%d")
    dx=[t.strip() for t in readfile(os.path.join(REPO,"dingxiang.txt")).splitlines() if t.strip() and not t.strip().startswith("#")]
    jd=readfile(os.path.join(REPO,"jingdui.txt"))
    return (diliao+"\n\n=== 以上是部门底料，据此筛选/路由/按下面格式与铁律写 ===\n\n"
        +"今天日期："+today+"\n昨天那版播报（下面这份，不要重复，除非有大变化或下面规则里说的升级重报）：\n"+yesterday()[:3000]+"\n\n"
        +"定向必盯词："+("、".join(dx) if dx else "无")+"\n\n"
        +"竞对手动喂料（每条必收进竞对板块；为空就按规则不出竞对板块）：\n"+(jd or "（今天为空）")+"\n\n"
        +"全网热榜：\n"+hot_lists()+"\n\n"
        +"营销垂媒/行业(广告门+36氪)：\n"+rss_titles()+"\n\n"
        +"写一份【营销热点日报 · "+today+"】，严格按下面的规则和铁律，只输出播报正文、不要任何解释：\n"
        +"【格式】首行 `# 营销热点日报 · "+today+"`；第二行 '今天最值得关注的：…'（一句话串当天最重要的几条，不带任何括号补充）；固定6板块、板块名加粗、板块之间空一行：社会民生 / 体育赛事 / 娱乐明星 / 科技数码 / 消费生活 / 竞对营销；每板块精选不超过2条；结尾另起一行 '以上各业务侧可参考&评估跟进~'，再另起一行 '内容由AI助手整理发布，有问题或建议请随时联系huke1。'。\n"
        +"【每条怎么写】'【看得懂的标题】：一两句说清这是什么事。@花名 关注，可考虑…'；@直接跟花名、不加'建议'二字、不带部门名。\n"
        +"【★落点必须具体、禁空话】'可考虑'后面必须落到一个具体的承接动作，要具体到品类/货盘/玩法/场景（例：'带一带体脂秤、筋膜枪这类家用运动好物'；'把家用血压计叠国补做成在家测血压的科普带货'）。严禁写'聊内容方向''做个专题''做相关内容''顺势承接'这类没有实际抓手的空话；想不出具体落点的，宁可不@、把这条删掉。\n"
        +"【说人话】标题和正文都要让不懂行的人、老板一眼看懂；不许写'（窗口X/X前）'这类内部时间；不用黑话缩写（站内承接、导成、对位、心智、UGC、进站搜索、超级周期等换成大白话，缩写首次出现带一句解释）。\n"
        +"【建议口吻】@后面的建议礼貌、简短、商量口吻、一句话够；不批评不甩锅不教训，不写'别再…''别只…''别被…盖过'这类否定提醒。\n"
        +"【筛选】①京东自己尽人皆知的既定合作/热度（纯复述、无增量）不要写，只有出现新进展/新数据/新争议/新梗/竞对也在蹭 才报；②不要重复上面昨天那版已报的，同一话题只是复述昨天、没新进展＝不写；③但某事件量级跃升或换了维度（国内→出海、单平台→登全球榜、明星个人→产业级破纪录、口碑→争议撕裂），即使昨天出现过也是新增量、必须重报并按更大维度重写标题；④定向必盯词当天只要有动静就必须报，尤其苹果新品/发布会/开卖这类节点。\n"
        +"【三硬beat别偏科】AI与科技趋势、3C新品官宣（手机/电脑/数码新品发布开卖）、竞对大促或代言官宣——这三类常常不在大众热搜榜上但对我们最有用，每天主动从营销垂媒和热榜里挖，别只盯社会八卦和娱乐。\n"
        +"【竞对板块】竞对喂料每条都必须收进竞对板块，另从广告门/36氪里挑真实的竞对动作或可借鉴的品牌案例；当天确实没有真料就整个竞对板块不出，不要写'营销圈热议''暂未抓到'这类占位废话，更不要为凑数去@人。\n"
        +"【空板块】任何板块当天没有真实、有增量、且值得某业务行动的内容，就整块省略；@必须对应一条真实且有行动价值的热点，没有就不@。\n"
        +"【雷区】①重大灾害、伤亡事故、讣告（地震/山体滑坡/重大车祸/空难等）只客观简述一句、当作一条让大家知道即可，绝不@人、绝不给任何营销建议；②其他一般灾害/事故只从安全防护、公益、科普的正向角度切；③健康类不夸大功效、不写疗效承诺；④不碰政治、宗教、性别对立等敏感对立话题。")

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
