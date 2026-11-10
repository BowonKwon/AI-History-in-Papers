# -*- coding: utf-8 -*-
"""Narrative text for the site (ko/en). Chapter texts are filled in stage 2 from verified cards;
numbers quoted here come from data/derived/winter_*.csv and papers.csv (recomputed in METHOD)."""
import html
import re

ERA_SPAN = {"E1": (1943, 1956), "E2": (1956, 1974), "E3": (1974, 1993), "E4": (1990, 2012), "E5": (2012, 2017), "E6": (2017, 2022), "E7": (2022, 2026)}
ERA_SHORT = {
    "ko": {"E1": "1장 기원 1943–56", "E2": "2장 기호와 퍼셉트론 1956–74", "E3": "3장 지식 시스템과 연결주의 1974–93", "E4": "4장 통계 학습 1990–2011", "E5": "5장 딥러닝 2012–17", "E6": "6장 사전학습·생성 2017–22", "E7": "7장 에이전트 2022–"},
    "en": {"E1": "Ch. 1 Origins 1943–56", "E2": "Ch. 2 Symbols and perceptrons 1956–74", "E3": "Ch. 3 Knowledge systems and connectionism 1974–93", "E4": "Ch. 4 Statistical learning 1990–2011", "E5": "Ch. 5 Deep learning 2012–17", "E6": "Ch. 6 Pretraining and generation 2017–22", "E7": "Ch. 7 Agents 2022–"},
}
ERA_TITLE = {
    "ko": {"E1": "기원 — 사이버네틱스와 계산 (1943–1956)", "E2": "기호 AI와 첫 신경망 (1956–1974)", "E3": "지식 시스템과 연결주의의 귀환 (1974–1993)", "E4": "통계 학습 (1990–2011)", "E5": "딥러닝 (2012–2017)", "E6": "사전학습과 생성 모델 (2017–2022)", "E7": "에이전트 (2022– )"},
    "en": {"E1": "Origins: cybernetics and computation (1943–1956)", "E2": "Symbolic AI and the first neural networks (1956–1974)", "E3": "Knowledge systems and the return of connectionism (1974–1993)", "E4": "Statistical learning (1990–2011)", "E5": "Deep learning (2012–2017)", "E6": "Pretraining and generative models (2017–2022)", "E7": "Agents (2022– )"},
}
ERA_LEAD = {
    "ko": {"E1": "뇌·기계·정보를 같은 언어로 쓸 수 있는가.", "E2": "탐색과 논리로 지능을 쓸 수 있는가, 퍼셉트론은 어디까지 배우는가.", "E3": "전문가의 지식을 규칙으로 옮길 수 있는가, 다층망을 학습시킬 수 있는가.", "E4": "데이터에서 일반화를 보장할 수 있는가.", "E5": "깊은 망, GPU, 대규모 데이터가 한자리에 모였다.", "E6": "규모·자기 지도·정렬.", "E7": "모델이 도구를 쓰고 행동한다."},
    "en": {"E1": "Can brain, machine and information be written in one language?", "E2": "Can intelligence be written as search and logic, and how much can a perceptron learn?", "E3": "Can expert knowledge be written as rules, and can multilayer networks be trained?", "E4": "Can generalization from data be guaranteed?", "E5": "Deep networks, GPUs and large datasets arrive together.", "E6": "Scale, self-supervision and alignment.", "E7": "Models use tools and act."},
}
# chapter narratives live in content_eras.py (stage 2)
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import content_eras as _A, content_eras_b as _B  # noqa: E402
try:
    import content_eras_c as _C  # noqa: E402
except ImportError:
    _C = None
_parts = [m for m in (_A, _B, _C) if m is not None]
ERA_KEY = {l: {e: next((m.ERA_KEY[l][e] for m in _parts if e in m.ERA_KEY[l]), []) for e in ERA_SPAN} for l in ("ko", "en")}
ERA_TEXT = {l: {e: next((m.ERA_TEXT[l][e] for m in _parts if e in m.ERA_TEXT[l]), "") for e in ERA_SPAN} for l in ("ko", "en")}


def _expand(h):
    """[[key|text]] -> card link on the chapter page; [[E3:key|text]] -> cross-chapter link."""
    return re.sub(r"\[\[(?:(E\d):)?([a-z0-9]+)\|(.*?)\]\]", lambda m: f'<a href="{m.group(1) + ".html" if m.group(1) else ""}#{m.group(2)}">{m.group(3)}</a>', h, flags=re.S)


ERA_TEXT = {l: {e: _expand(h) for e, h in d.items()} for l, d in ERA_TEXT.items()}
ERA_KEY = {l: {e: [_expand(x) for x in v] for e, v in d.items()} for l, d in ERA_KEY.items()}
BOXES = {l: {e: [_expand(x) for x in v] for e, v in (_C.BOXES[l] if _C else {}).items()} for l in ("ko", "en")}

HOME_KEY = {
    "ko": ["연대표의 점은 모두 원 논문이다. 점마다 원문 링크, 쪽을 밝힌 원문 한 문장, 「무엇을 바꿨나」 한두 줄이 붙어 있다.",
           "계보선은 인용이 확인된 것만 실선으로 긋는다. 교과서가 말하는 영향이지만 인용이 확인되지 않은 선은 점선이다.",
           "논문 선정 기준은 목록을 만들기 전에 등록했다(「방법·한계」). 우선권 논쟁은 양쪽 서지를 나란히 놓고 판정하지 않는다."],
    "en": ["Every dot on the timeline is an original paper, with a link to the source, one sentence quoted from it with a page number, and one or two lines on what changed.",
           "Lineage lines are solid only where a citation is confirmed. Influences stated in textbooks without a confirmed citation are dotted.",
           "The selection rules were registered before the list was made (see Method and limits). Priority disputes show both sides' bibliographies and make no ruling."],
}
HOME_INTRO = {
    "ko": """<h2>이 사이트가 하는 일</h2>
<p>인공지능 연구의 역사는 여러 곳에 정리되어 있다. 위키백과의 연대표, 컴퓨터역사박물관의 연표, 교과서의 역사 장, 한 연구자의 긴 주석 달린 역사. 이 사이트는 그것들을 대신하려는 것이 아니라 한 가지를 보태려 한다 — <b>모든 점을 원 논문에 묶어 두는 것</b>이다. 연도는 널리 알려진 연도가 아니라 처음 공개된 날짜를 쓰고, 「무엇을 바꿨나」는 논문 자신의 문장으로 쓰며, 영향 관계는 인용이 확인된 것과 그렇지 않은 것을 구분해 그린다.</p>
<p>수치는 서술을 받치는 데만 쓴다. 피인용 수는 카드에 조회일과 함께 작게 적지만 순위표는 없다. 「겨울과 붐」 면은 통념의 두 겨울(1974년 전후, 1987년 전후)을 논문 제목 수·학회 참가자 수·공공 연구비 기록으로 다시 본다.</p>""",
    "en": """<h2>What this site does</h2>
<p>The history of AI research has been written in many places: the Wikipedia timelines, the Computer History Museum's timeline, the history chapters of textbooks, one researcher's long annotated history. This site does not replace them. It adds one thing: <b>every point is tied to an original paper</b>. Dates are first-public dates rather than popularly quoted years, "what changed" is written from the paper's own sentences, and lines of influence distinguish confirmed citations from unconfirmed attributions.</p>
<p>Numbers only support the narrative. Citation counts appear small on each card with the date they were read, and there is no ranking. The page on winters and booms re-examines the two conventional winters (around 1974 and around 1987) against paper-title counts, conference attendance and public funding records.</p>""",
}
STAT = {"ko": {"papers": "원 논문", "edges": "확인된 인용선", "span": "첫 공개 연도 범위"}, "en": {"papers": "original papers", "edges": "confirmed citation lines", "span": "first-public years"}}
LINEAGE_LEAD = {"ko": "주제 묶음별 계보. 가로축은 첫 공개 연도, 선은 확인된 인용 관계다.", "en": "Lineage by theme group. Horizontal axis is the first-public year; lines are confirmed citations."}
LANE_LEAD = {
    "ko": {"neural": "형식 뉴런에서 퍼셉트론, 역전파, 합성곱·순환망, 정규화와 잔차 연결까지.", "rl": "동적 계획법과 시간차 학습에서 Q-학습, 정책 경사, 알파고 계열까지.", "lang": "통계적 언어 모델과 음성 인식에서 임베딩, 어텐션, 트랜스포머, 사전학습 언어 모델까지.", "vision": "네오코그니트론과 LeNet에서 ImageNet, ResNet, 생성 모델(GAN·VAE·확산)까지.", "search": "논리 이론가·GPS·A*·STRIPS·전문가 시스템·MCTS.", "stat": "사이버네틱스·정보 이론·PAC 학습·SVM·앙상블·베이지안 망.", "align": "스케일링 법칙, 인간 피드백 강화학습, 안전 문제 제기.", "agent": "ReAct 이후 — 추론·도구·기억·다중 에이전트·평가·보안."},
    "en": {"neural": "From formal neurons to perceptrons, backpropagation, convolutional and recurrent networks, normalization and residual connections.", "rl": "From dynamic programming and temporal-difference learning to Q-learning, policy gradients and the AlphaGo family.", "lang": "From statistical language models and speech recognition to embeddings, attention, the Transformer and pretrained language models.", "vision": "From the Neocognitron and LeNet to ImageNet, ResNet and generative models (GAN, VAE, diffusion).", "search": "Logic Theorist, GPS, A*, STRIPS, expert systems, MCTS.", "stat": "Cybernetics, information theory, PAC learning, SVMs, ensembles, Bayesian networks.", "align": "Scaling laws, reinforcement learning from human feedback, and the safety agenda.", "agent": "After ReAct: reasoning, tools, memory, multi-agent systems, evaluation and security."},
}
PAPERS_LEAD = {"ko": "선정된 논문 전체. 열 머리글을 누르면 정렬되고, 찾기 칸은 모든 열을 대상으로 한다. CSV 의 열 설명은 datapackage.json 에 있다.", "en": "All selected papers. Click a column header to sort; the filter box searches every column. Column definitions are in datapackage.json."}

WINTER_LEAD = {"ko": "통념의 두 겨울을 세 가지 계열로 다시 본다: 논문 제목에 든 용어의 비율, 학회 참가자 수, 공공 연구비의 기록.", "en": "The two conventional winters re-examined with three series: the share of paper titles containing a term, conference attendance, and public-funding records."}
WINTER_KEY = {
    "ko": ["1987년 전후의 두 번째 겨울은 참가자 수에서 뚜렷하다. AAAI 참가자는 1986년 5,334명에서 1992년 1,685명으로 줄었다(AI Index 2019 자료; 1997년 1,262명).",
           "제목 수는 몇 년 늦게 따라온다. 「expert system」이 제목에 든 OpenAlex 레코드는 1990년 1,857건이 정점이고 1998년 490건이다. 같은 기간 「neural network」는 1,745건에서 4,243건으로 늘었다.",
           "1974년 전후의 첫 번째 겨울은 수치로 확인하지 못했다. 그 시기의 학회 참가자·연도별 연구비 자료를 찾지 못했고, OpenAlex 제목 수는 건수가 너무 적다."],
    "en": ["The second winter around 1987 is visible in attendance: AAAI attendance fell from 5,334 in 1986 to 1,685 in 1992 (AI Index 2019 data).",
           "Title counts lag by several years. OpenAlex records with “expert system” in the title peak at 1,857 in 1990 and fall to 490 in 1998; over the same years “neural network” rises from 1,745 to 4,243.",
           "The first winter around 1974 could not be confirmed with numbers: no attendance or year-by-year funding series for that period was found, and OpenAlex title counts are too small."],
}
WINTER_TEXT = {
    "ko": dict(
        intro="""<p>「AI 겨울」은 연구비와 관심이 식은 시기를 가리키는 말이다. 통념으로는 두 번이다. 첫 번째는 1973년 영국의 라이트힐 보고서와 미국 DARPA 의 지원 축소 전후, 두 번째는 1987년 전후 전문가 시스템 시장과 LISP 기계 시장이 꺼진 뒤다. 이 면은 그 통념을 수치로 다시 본다. 세 계열이 같은 방향을 가리킬 때만 「확인」이라고 쓰고, 자료가 없으면 없다고 쓴다.</p>""",
        h1="논문 제목에 든 용어", y1="만 건당", cap1="OpenAlex 에서 제목에 해당 구절이 든 레코드 수를 그해 전체 레코드 수로 나눠 만 건당으로 표시(2026-11-03 조회). 1970년 값은 날짜 없는 레코드가 몰린 것으로 보여 제외했다.",
        t1="""<p>세 구절은 서로 다른 이야기를 한다. 「expert system」은 1984년부터 급히 늘어 1988–1990년에 정점(만 건당 9건 안팎)을 찍고 1990년대에 내려와 2000년에는 1.5건이 된다. 「artificial intelligence」도 1987년 정점(3.4건) 뒤 2000년 0.84건까지 내려온다. 반면 「neural network」는 1988년부터 급증해 1994년 15.7건에 이르고, 그 뒤로도 크게 줄지 않는다. 즉 1990년대의 「겨울」은 분야 전체의 겨울이 아니라 <b>기호 AI·전문가 시스템이라는 이름의 겨울</b>이었고, 같은 해에 신경망 연구는 늘고 있었다.</p>
<p>제목 수의 하락이 참가자 수의 하락보다 몇 년 늦게 시작하는 것은 출판 지연과 색인 구성의 영향일 수 있다. 이 계열만으로 시점을 정하지 않는다.</p>
<p>1974년 전후는 이 계열로 판단할 수 없다. 1973–1975년 「artificial intelligence」 제목 레코드는 한 해 34–46건이고, 「perceptron」은 한 자릿수다. 건수가 작아 변동이 잡음에 묻힌다.</p>""",
        h2="학회 참가자", y2="명", cap2="AAAI·IJCAI·NeurIPS 참가자 수. 1984–2019년은 AI Index 2019 보고서 2장의 자료, 2020년 이후는 Our World in Data(AI Index 2026) 자료. IJCAI 는 2014년까지 홀수 해에만 열렸으므로 보고서가 평균으로 메운 짝수 해 값은 뺐다.",
        t2="""<p>AAAI 참가자는 1986년 5,334명에서 1992년 1,685명으로 해마다 줄고, 1994년 한 해 반등(1,964명)을 빼면 1997년 1,262명까지 내려간다. IJCAI 도 1985년 4,995명에서 1997년 1,325명으로 내려간다. 두 학회가 1980년대 중반 규모의 4분의 3가량(AAAI 76%, IJCAI 73%)을 잃는 동안 NeurIPS 는 작은 규모에서 조금씩 늘어난다(1995년 500명, 2005년 926명). 학회 규모로 보면 두 번째 겨울은 <b>1987년에 시작해 1990년대 말까지 이어진 긴 내리막</b>이고, 2000년대의 회복은 신경망 쪽에서 먼저 왔다. 2010년대 후반의 증가는 세 학회 모두에서 가파르다(NeurIPS 2019년 13,500명).</p>
<p>주의할 점이 둘 있다. 첫째, 1995–2001년 NeurIPS 값은 해마다 정확히 30명씩 늘어난다(500, 530, 560, …). 실제 집계라기보다 추정값으로 보이므로 이 구간은 추세로만 읽는다. 둘째, 1984년 이전 참가자 자료는 찾지 못했다. 첫 번째 겨울을 이 계열로 볼 수 없는 이유다.</p>""",
        h3="NeurIPS 채택 논문 수", y3="편(로그)", cap3="proceedings.neurips.cc 에 실린 연도별 논문 수를 2026-11-03 에 직접 센 것. 2025년 목록은 불완전해 뺐다.",
        t3="""<p>채택 논문 수는 1987년 90편에서 2000년 152편까지 완만히 늘고, 2012년 370편, 2017년 679편, 2020년 1,898편, 2024년 4,493편으로 가팔라진다. 신경망 학회의 규모는 1990년대 「겨울」 동안에도 전체로는 늘었다(해마다 늘지는 않아, 1992·1994·1997년은 전년보다 적다).</p>""",
        h4="공공 연구비 — 기록은 있으나 연도별 표는 없다",
        t4="""<p>연구비 계열은 그림으로 그리지 못했다. 찾은 것은 사건 기록이다.</p>
<ul>
<li><b>맨스필드 수정조항(1969).</b> 미국 공법 91-121 제203조는 「이 법으로 승인된 예산은 특정 군사 기능이나 작전과 직접적이고 명백한 관계가 없는 연구 과제에 쓸 수 없다」고 정했다(83 Stat. 206). 기초 연구비의 방향을 바꾼 조항으로 자주 인용되지만, AI 연구비가 그 뒤 몇 년에 얼마나 줄었는지를 보여 주는 연도별 표는 찾지 못했다.</li>
<li><b>라이트힐 보고서(1973).</b> 영국 과학연구위원회의 의뢰로 쓴 「Artificial Intelligence: A General Survey」와 그에 대한 반론·논평 전문이 공개되어 있다(Chilton Computing). 보고서가 영국의 AI 지원을 축소시켰다는 서술은 널리 받아들여지지만, 금액의 연도별 추이는 이 자료에 없다.</li>
<li><b>DARPA 전략 컴퓨팅 계획(1983–1993).</b> 약 10억 달러 규모로 알려져 있다(Roland & Shiman, <i>Strategic Computing</i>, 2002). 연도별 집행액은 책의 부록이나 예산 문서에 있고 온라인 표로는 찾지 못했다.</li>
<li><b>일본 제5세대 컴퓨터 계획(1982–1992).</b> 정보처리학회 컴퓨터박물관은 「11년간 약 540억 엔」이라고 적는다. 연도별 표는 없다.</li>
</ul>
<p>그래서 이 면의 결론은 이렇다. 두 번째 겨울은 참가자 수와 제목 수에서 확인된다. 첫 번째 겨울은 사건 기록은 있으나 수치 계열로 확인하지 못했다. 겨울이 없었다는 뜻이 아니라, 있었다고 수치로 말할 자료를 아직 찾지 못했다는 뜻이다.</p>""",
    ),
    "en": dict(
        intro="""<p>An "AI winter" is a period in which funding and attention cooled. By convention there were two: the first around the 1973 Lighthill report in Britain and the contraction of DARPA support in the United States, the second after the expert-system and Lisp-machine markets collapsed around 1987. This page re-examines that convention with numbers. We write "confirmed" only where the series point the same way, and we say so where there is no data.</p>""",
        h1="Terms in paper titles", y1="per 10,000 works", cap1="OpenAlex records whose title contains the phrase, divided by all OpenAlex records of that year, per 10,000 (read 2026-11-03). The 1970 value is omitted because undated records appear to have been assigned to that year.",
        t1="""<p>The three phrases tell different stories. “Expert system” rises steeply from 1984, peaks in 1988–1990 at about 9 per 10,000, and falls through the 1990s to 1.5 in 2000. “Artificial intelligence” also declines after a 1987 peak (3.4) to 0.84 in 2000. “Neural network”, by contrast, surges from 1988 to 15.7 in 1994 and does not fall much afterwards. The 1990s "winter" was therefore not a winter for the whole field but <b>a winter for the words symbolic AI and expert system</b>; neural-network research grew in the same years.</p>
<p>The decline in title counts begins several years after the decline in attendance. Publication lag and index coverage may both contribute, so this series alone does not date the winter.</p>
<p>The years around 1974 cannot be judged from this series. In 1973–1975 there are only 34–46 records a year with “artificial intelligence” in the title, and single digits for “perceptron”; the counts are too small to separate change from noise.</p>""",
        h2="Conference attendance", y2="attendees", cap2="Attendance at AAAI, IJCAI and NeurIPS. 1984–2019 from the AI Index 2019 report, chapter 2; 2020 onward from Our World in Data (AI Index 2026). IJCAI met only in odd years until 2014; the even-year values the report filled in by averaging are excluded.",
        t2="""<p>AAAI attendance falls year after year from 5,334 in 1986 to 1,685 in 1992 and, apart from a rise in 1994 (1,964), on to 1,262 in 1997. IJCAI falls from 4,995 in 1985 to 1,325 in 1997. While the two conferences lose about three quarters of their mid-1980s size (AAAI 76%, IJCAI 73%), NeurIPS grows slowly from a small base (500 in 1995, 926 in 2005). Measured by attendance, the second winter is <b>a long decline that begins in 1987 and lasts to the end of the 1990s</b>, and the recovery of the 2000s came first on the neural-network side. The late-2010s rise is steep at all three (NeurIPS 13,500 in 2019).</p>
<p>Two cautions. First, the NeurIPS values for 1995–2001 increase by exactly 30 a year (500, 530, 560, …); they look like estimates rather than counts, so we read that stretch only as a trend. Second, no attendance data before 1984 was found, which is why the first winter cannot be seen in this series.</p>""",
        h3="Papers accepted at NeurIPS", y3="papers (log scale)", cap3="Papers listed per year on proceedings.neurips.cc, counted on 2026-11-03. The 2025 listing was incomplete and is omitted.",
        t3="""<p>Accepted papers grow gently from 90 in 1987 to 152 in 2000, then steeply: 370 in 2012, 679 in 2017, 1,898 in 2020, 4,493 in 2024. The neural-network conference grew overall during the 1990s "winter" (not every year: 1992, 1994 and 1997 were below the year before).</p>""",
        h4="Public funding: records exist, year-by-year tables do not",
        t4="""<p>The funding series could not be drawn. What we found are event records.</p>
<ul>
<li><b>The Mansfield Amendment (1969).</b> Section 203 of U.S. Public Law 91-121 provides that none of the funds authorized "may be used to carry out any research project or study unless such project or study has a direct and apparent relationship to a specific military function or operation" (83 Stat. 206). It is often cited as redirecting basic research money, but no year-by-year table of AI funding in the following years was found.</li>
<li><b>The Lighthill report (1973).</b> "Artificial Intelligence: A General Survey", written for the UK Science Research Council, together with the published replies and commentaries, is available in full (Chilton Computing). The statement that it cut British AI support is widely accepted; the source does not give yearly amounts.</li>
<li><b>DARPA's Strategic Computing Initiative (1983–1993).</b> Usually given as about one billion dollars (Roland & Shiman, <i>Strategic Computing</i>, 2002). Yearly outlays are in the book's appendices or budget documents and were not found as an online table.</li>
<li><b>Japan's Fifth Generation Computer project (1982–1992).</b> The IPSJ Computer Museum states "approximately ¥54 billion was invested in the project over 11 years". No yearly table.</li>
</ul>
<p>The conclusion of this page is therefore: the second winter is confirmed by attendance and by title counts. The first winter has event records but no numerical series to confirm it. That does not mean there was no winter; it means we have not found the data to say so with numbers.</p>""",
    ),
}

DATAPACKAGE_RESOURCES = [
    {"name": "papers", "path": "papers.csv", "description": "One row per selected paper: first-public date and type, identifiers, venue, pages, a verbatim sentence with page, what changed (en/ko), OpenAlex id and citation count with the date read, selection rules, source status.", "sources": ["original papers", "OpenAlex (CC0)", "Crossref", "arXiv metadata (CC0)"]},
    {"name": "edges", "path": "edges.csv", "description": "Citation lineage among selected papers; kind = OA (OpenAlex referenced_works), original (seen in the citing paper's reference list), notion (textbook attribution without a confirmed citation).", "sources": ["OpenAlex (CC0)", "original papers"]},
    {"name": "winter_title_phrases", "path": "winter_title_phrases.csv", "description": "OpenAlex records per year with a phrase in the title, and per 10,000 of all records (read 2026-11-03).", "sources": ["OpenAlex (CC0)"]},
    {"name": "winter_attendance", "path": "winter_attendance.csv", "description": "Conference attendance 1984–2025; source column names the AI Index 2019 sheet or Our World in Data (AI Index 2026, CC BY).", "sources": ["AI Index 2019", "Our World in Data"]},
    {"name": "winter_neurips_accepted", "path": "winter_neurips_accepted.csv", "description": "Papers per year on proceedings.neurips.cc, counted 2026-11-03.", "sources": ["proceedings.neurips.cc"]},
    {"name": "awards", "path": "awards.csv", "description": "Turing Award laureates (Wikidata, CC0) and 2024 Nobel laureates (Nobel API, CC0) linked to papers in the list.", "sources": ["Wikidata (CC0)", "Nobel Prize API (CC0)"]},
]


def METHOD(lang):
    def f(papers, edges):
        n = len(papers)
        by_rule = {}
        for p in papers:
            for r in p["rules"].split("+"):
                by_rule[r.split("(")[0]] = by_rule.get(r.split("(")[0], 0) + 1
        kinds = {k: sum(1 for e in edges if e["kind"] == k) for k in ("OA", "original", "notion")}
        status = {k: sum(1 for p in papers if p["source_status"] == k) for k in ("verified", "partial", "not_accessible")}
        if lang == "ko":
            return f"""<h1>방법과 한계</h1>
<p class="lead">선정 기준은 목록을 만들기 전에 등록했고, 날짜는 원문에서, 계보선은 인용 자료에서 가져왔다. 이 면은 그 절차와 거기서 생기는 한계를 적는다.</p>
<h2>논문 선정 — 2026-11-03 등록</h2>
<p>기준 문헌 여섯 종을 먼저 정했다: Nilsson 『The Quest for Artificial Intelligence』(2010), Russell & Norvig 『Artificial Intelligence: A Modern Approach』 4판(2020), Goodfellow·Bengio·Courville 『Deep Learning』(2016), Sutton & Barto 『Reinforcement Learning』 2판(2018), Prince 『Understanding Deep Learning』(2023), Jurafsky & Martin 『Speech and Language Processing』 3판 초고. 1.1에서 Murphy 『Probabilistic Machine Learning: An Introduction』(2022)을 더해 일곱 종이 되었다. 포함 규칙은 넷이다.</p>
<ul><li><b>R1 교과서.</b> 기준 문헌 가운데 두 종 이상이 그 업적의 원 논문을 참고문헌에 올림. ({by_rule.get('R1', 0)}편)</li>
<li><b>R2 계보.</b> 이미 선정된 논문 세 편 이상이 인용(OpenAlex 또는 인용한 논문의 참고문헌 목록으로 확인). ({by_rule.get('R2', 0)}편)</li>
<li><b>R3 수상.</b> 튜링상·노벨상의 공적 설명이 가리키는 업적의 원 논문. ({by_rule.get('R3', 0)}편)</li>
<li><b>R4 최근(2021년 이후).</b> 동료 심사 게재(또는 공개된 심사 기록)와 원문 확인. ({by_rule.get('R4', 0)}편)</li></ul>
<p>그 결과 {n}편이다. 교과서 대조는 참고문헌 텍스트를 제목·저자·연도로 자동 대조한 뒤 표본을 손으로 확인했다. 손으로 바로잡은 적중은 근거와 함께 <a href="https://github.com/BowonKwon/AI-History-in-Papers/blob/main/method/textbook_overrides.csv">textbook_overrides.csv</a>에 적었다. Nilsson 의 책은 참고문헌을 장 끝의 주(註)에 두므로 책 전문(저자 공개 PDF, Internet Archive 2026-10-11 보존본)을 대조 텍스트로 썼다 — 본문에서 제목이나 저자·연도로 거명한 것도 인용으로 세었다는 뜻이다. Schmidhuber 의 「Annotated History of Modern AI and Deep Learning」(2022)은 기준 문헌에 넣지 않고 우선권 상자의 한쪽 자료로만 썼다.</p>
<h2>1.1.2 — 2026-11-11</h2>
<p>원문을 구하지 못해 비어 있던 책 일곱 권의 카드를 채웠다. Bellman(1957년판 6쇄), Minsky–Papert(1988년 증보판), Holland(1992년 MIT Press 판), Marr(2010년 MIT Press 재간본), Pearl(1988)은 책을 읽었고, Schank–Abelson(1977)과 Quinlan의 C4.5(1993)는 출판사 미리보기만 읽어 「부분 확인」이다. 읽은 판과 쪽은 카드에 적었다. 이로써 「접근 불가」 카드는 없다. 책의 참고문헌에서 읽은 인용선 17개가 더해졌다. 함께, 1.0.1에서 카드는 채웠으나 장 본문에는 「읽지 못했다」로 남아 있던 네 편(McCarthy 1960, Buchanan–Feigenbaum 1978, Werbos 1982, Boser 외 1992)의 서술을 카드에 맞게 고쳤다. 선정은 바뀌지 않았다.</p>
<h2>1.1.1 — 2026-11-08</h2>
<p>한국어판에서 우리말로 옮긴 용어는 쪽마다 처음 나올 때 원어를 괄호로 붙였다(예: 생각의 사슬(chain of thought)). 대응표는 <a href="https://github.com/BowonKwon/AI-History-in-Papers/blob/main/method/glossary_ko.csv">glossary_ko.csv</a>에 있다. 선정과 카드 내용은 바뀌지 않았다.</p>
<h2>1.1 개정 — 2026-11-07</h2>
<p>두 가지를 바꿨다. 첫째, 통계적 기계학습 쪽 교과서가 빠져 있어 Murphy 『Probabilistic Machine Learning: An Introduction』(MIT Press 2022)을 일곱 번째 기준 문헌으로 더했다. 대조에는 저자가 공개한 초고 PDF(2025-04-18판)의 참고문헌을 썼다. 둘째, 후보를 넓혔다. 이미 선정된 논문 세 편 이상이 OpenAlex 에서 인용하고 기준 문헌 세 종 이상이 참고문헌에 올린 논문 가운데 후보에 없던 것을 더했다. 교과서·개관 논문, 이미 있는 점과 같은 업적의 다른 판본은 넣지 않았다. 더한 논문도 위 네 규칙으로만 선정했다. 더한 16편과 각 편의 인용 수·기준 문헌은 <a href="https://github.com/BowonKwon/AI-History-in-Papers/blob/main/method/pool-1.1-added.csv">pool-1.1-added.csv</a>에 있다. 그 가운데 Jelinek 1976은 한 기준 문헌(Jurafsky & Martin)의 적중이 같은 저자의 다른 논문을 잡은 것으로 뒤에 밝혀졌다. 바로잡으면 기준 문헌이 두 종이라 확장 조건(세 종)에 못 미치므로, 등록한 조건대로 후보에서 빼고 선정하지 않았다. 후보에 남은 것은 15편이다.</p>
<h2>날짜</h2>
<p>점의 위치는 처음 공개된 날짜다 — 기술 보고서, 학위논문, arXiv v1, 학회 발표 중 기록으로 확인되는 가장 이른 것. 저널 게재일·학회 발표일·재판 연도는 카드에 따로 적는다. OpenAlex 의 발행 연도는 재판이나 학회판 날짜가 섞여 있어 쓰지 않았다(1.0 후보 234편 중 23편에서 연도가 달랐다).</p>
<h2>원문 확인</h2>
<p>카드의 인용문과 쪽은 그 판본을 직접 읽고 옮긴 것이다. 읽은 판본은 카드에 적혀 있다(저널판·학회판·arXiv 판 번호). 상태별로 확인 {status['verified']}편, 부분 확인 {status['partial']}편, 접근 불가 {status['not_accessible']}편이다. 접근 불가는 합법적 공개 사본을 찾지 못한 경우이며, 그 카드에는 인용문이 없다. 공개 사본이 없는 몇 편(예: Werbos 1974 박사논문, Werbos 1982 학회 논문집 장)은 엮은이가 구한 출판본·원본 사본으로 읽었고, 카드의 「읽은 판본」에 그렇게 적었다.</p>
<h2>계보선</h2>
<p>세 종류다. OpenAlex 의 참고문헌 목록에 있는 것({kinds['OA']}건), OpenAlex 에는 없으나 인용한 논문의 참고문헌 목록에서 직접 확인한 것({kinds['original']}건), 교과서가 영향을 말하지만 인용이 확인되지 않은 것({kinds['notion']}건, 점선). OpenAlex 만으로는 선이 크게 빈다 — 후보 목록에서 1990년 이전 레코드의 30%, arXiv 레코드의 40%가 참고문헌 0건이었다.</p>
<h2>우선권 논쟁</h2>
<p>역전파·합성곱망·심층망 학습·잔차 연결처럼 「누가 먼저인가」가 다투어지는 자리에는 양쪽 원 논문의 서지와 원문 문장만 나란히 놓는다. 판정하는 문장은 쓰지 않는다. 판정이 담긴 2차 문헌은 「이런 주장이 있다」로 출처와 함께 소개한다.</p>
<h2>편중</h2>
<p>기준 문헌이 영어 교과서라는 점에서 오는 편중을 숨기지 않는다. 소련·일본의 초기 신경망 연구(Ivakhnenko, Amari, Fukushima)와 핀란드의 Linnainmaa 는 교과서 두 종 기준을 넘지 못한 경우가 있고, 그런 논문은 우선권 상자에서 다룬다. 선정 논문의 저자 소속 국가 분포는 이 판의 papers.csv 와 OpenAlex 레코드로 계산할 수 있다.</p>
<h2>자료원과 이용 조건</h2>
<ul><li>OpenAlex — 서지·인용·피인용 수·연도별 건수. 데이터 CC0. 피인용 수는 조회일(2026-11-03)과 함께만 싣는다.</li>
<li>arXiv — 메타데이터(제목·저자·v1 날짜) CC0. PDF 는 링크만 한다.</li>
<li>Crossref — DOI 서지 대조.</li>
<li>Wikidata(튜링상 수상자, CC0)·노벨상 API(CC0).</li>
<li>AI Index 2019 보고서 2장의 참가자 자료, Our World in Data(CC BY), proceedings.neurips.cc.</li></ul>
<p>이 사이트의 글은 CC BY-NC 4.0, 코드는 PolyForm Noncommercial 1.0.0, 데이터 편집물은 CC BY 4.0(원자료는 CC0 또는 CC BY)이다. 논문 본문은 재배포하지 않고 짧은 인용과 링크만 한다.</p>"""
        return f"""<h1>Method and limits</h1>
<p class="lead">The selection rules were registered before the list was made; dates come from the originals and lineage lines from citation data. This page records the procedure and the limits it carries.</p>
<h2>Selecting papers — registered 2026-11-03</h2>
<p>Six reference works were fixed first: Nilsson, <i>The Quest for Artificial Intelligence</i> (2010); Russell & Norvig, <i>Artificial Intelligence: A Modern Approach</i>, 4th ed. (2020); Goodfellow, Bengio & Courville, <i>Deep Learning</i> (2016); Sutton & Barto, <i>Reinforcement Learning</i>, 2nd ed. (2018); Prince, <i>Understanding Deep Learning</i> (2023); Jurafsky & Martin, <i>Speech and Language Processing</i>, 3rd ed. draft. Version 1.1 added a seventh, Murphy, <i>Probabilistic Machine Learning: An Introduction</i> (2022). Four inclusion rules apply.</p>
<ul><li><b>R1 Textbooks.</b> At least two of the reference works cite the original publication. ({by_rule.get('R1', 0)} papers)</li>
<li><b>R2 Lineage.</b> At least three already-selected papers cite it (OpenAlex or the citing paper's reference list). ({by_rule.get('R2', 0)})</li>
<li><b>R3 Awards.</b> The Turing Award or Nobel Prize citation names the achievement. ({by_rule.get('R3', 0)})</li>
<li><b>R4 Recent (2021 onward).</b> Peer-reviewed publication or public review record, original text checked. ({by_rule.get('R4', 0)})</li></ul>
<p>The result is {n} papers. Textbook matching compared bibliography text by title, author and year automatically, with samples checked by hand; hits corrected by hand are listed with the evidence in <a href="https://github.com/BowonKwon/AI-History-in-Papers/blob/main/method/textbook_overrides.csv">textbook_overrides.csv</a>. Nilsson's book keeps its references in chapter endnotes, so the whole text (the author's public PDF, Internet Archive capture of 2026-10-11) was used as the comparison text; a work named by title or by author and year in the body counts as cited. Schmidhuber's "Annotated History of Modern AI and Deep Learning" (2022) is not a reference work here; it is used only as one side in the priority boxes.</p>
<h2>Revision 1.1.2 — 2026-11-11</h2>
<p>The cards of seven books that had been empty for lack of the original are now filled. Bellman (1957 edition, sixth printing), Minsky–Papert (1988 expanded edition), Holland (1992 MIT Press edition), Marr (2010 MIT Press reissue) and Pearl (1988) were read in the book; Schank–Abelson (1977) and Quinlan's C4.5 (1993) were read only in a publisher's preview and are marked "partially checked". Each card names the edition and page read. No card is "not accessible" any longer. Seventeen citation links read from the books' reference lists were added. Four papers whose cards were filled in 1.0.1 but whose chapter text still said "not read" (McCarthy 1960, Buchanan–Feigenbaum 1978, Werbos 1982, Boser et al. 1992) now agree with their cards. Selection is unchanged.</p>
<h2>Revision 1.1.1 — 2026-11-08</h2>
<p>Korean edition only: technical terms rendered in Korean now carry the English original in parentheses at their first appearance on each page. The term list is <a href="https://github.com/BowonKwon/AI-History-in-Papers/blob/main/method/glossary_ko.csv">glossary_ko.csv</a>. Selection and cards are unchanged.</p>
<h2>Revision 1.1 — 2026-11-07</h2>
<p>Two changes. First, statistical machine learning lacked a textbook, so Murphy, <i>Probabilistic Machine Learning: An Introduction</i> (MIT Press 2022), was added as the seventh reference work; its bibliography was taken from the author's public draft PDF (version of 2025-04-18). Second, the candidate pool was widened: papers cited in OpenAlex by at least three selected papers and listed by at least three reference works were added when they were not yet candidates. Textbooks, surveys, and other versions of a contribution already on the timeline were left out. Added papers were selected only under the four rules above. The 16 works added, with their citation counts and reference works, are listed in <a href="https://github.com/BowonKwon/AI-History-in-Papers/blob/main/method/pool-1.1-added.csv">pool-1.1-added.csv</a>. One of them, Jelinek 1976, was later found to have been matched in one reference work (Jurafsky & Martin) to a different paper by the same author. Corrected, it is matched in two reference works, short of the three the widening requires, so under the registered condition it was taken out of the pool and is not selected. Fifteen remain in the pool.</p>
<h2>Dates</h2>
<p>A point sits at the first public date: the earliest documented technical report, thesis, arXiv v1 or conference presentation. Journal issue dates, conference dates and reprint years are listed on the card. OpenAlex publication years were not used because they mix in reprint and conference dates (23 of the 234 candidates for 1.0 differed).</p>
<h2>Checking the originals</h2>
<p>Each card's quotation and page were read from the stated version (journal, conference, or arXiv version number). By status: {status['verified']} verified, {status['partial']} partially checked, {status['not_accessible']} not accessible. "Not accessible" means no legitimate public copy was found; those cards carry no quotation. A few papers with no public copy (for example Werbos's 1974 thesis and his 1982 proceedings chapter) were read from copies of the printed or original text obtained by the editor, as the card's "version read" says.</p>
<h2>Lineage lines</h2>
<p>Three kinds: in OpenAlex's reference list ({kinds['OA']}), not in OpenAlex but seen in the citing paper's own reference list ({kinds['original']}), and stated in a textbook without a confirmed citation ({kinds['notion']}, dotted). OpenAlex alone leaves large gaps: among the candidates, 30% of pre-1990 records and 40% of arXiv records had zero references.</p>
<h2>Priority disputes</h2>
<p>Where "who was first" is disputed (backpropagation, convolutional networks, deep network training, residual connections), the boxes place both sides' original bibliographies and sentences side by side and make no ruling. Secondary sources that do rule are introduced as claims, with their source.</p>
<h2>Bias</h2>
<p>The reference set is English-language textbooks, and the resulting bias is not hidden. Early neural-network work from the Soviet Union and Japan (Ivakhnenko, Amari, Fukushima) and Linnainmaa in Finland sometimes fails the two-textbook rule; such papers appear in the priority boxes. The country distribution of author affiliations can be computed from this version's papers.csv and the OpenAlex records.</p>
<h2>Sources and terms</h2>
<ul><li>OpenAlex — bibliographic data, citations, citation counts, yearly counts. Data CC0. Citation counts appear only with the date read (2026-11-03).</li>
<li>arXiv — metadata (title, authors, v1 date) CC0. PDFs are linked, not hosted.</li>
<li>Crossref — DOI checks.</li>
<li>Wikidata (Turing Award laureates, CC0) and the Nobel Prize API (CC0).</li>
<li>AI Index 2019, chapter 2 attendance data; Our World in Data (CC BY); proceedings.neurips.cc.</li></ul>
<p>Text on this site is CC BY-NC 4.0, code PolyForm Noncommercial 1.0.0, and the data compilation CC BY 4.0 (sources CC0 or CC BY). Paper texts are not redistributed; only short quotations and links.</p>"""
    return f


METHOD = {"ko": METHOD("ko"), "en": METHOD("en")}
