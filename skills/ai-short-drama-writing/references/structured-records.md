# 多集结构化记录

仅在需要索引或确定性核对时采用。结构化块是所属产物的一部分，改动后须登记新版本。每种标签每文件最多一个块，不从任意旧 Markdown 猜测数据。缺块返回 UNVERIFIED，不代表故事有错。

## 连续性

在 continuity 文件记录以下块，location 与 quote 必须能回查同版本正文。before=null 表示此前未知；每个 field 是可比较的离散状态，例如 knows_page、holder。观众使用独立对象 AUDIENCE，不与角色知识混写。闪回使用 temporal=flashback，只进入历史，不覆盖当前状态。

```continuity-json
{"states":[{"object":"PROP001","field":"holder","before":null,"after":"CHAR001","location":"EP001-SC001","quote":"钥匙在林夏右手","temporal":"current"}],"foreshadows":[{"id":"F001","status":"planted","location":"EP001-SC001","quote":"纸片撕口与登记簿吻合"}]}
```

字段和引用通过，只能证明证据存在，不能证明提取语义正确。不要为让 before 一致而修改正文事实。出现冲突交审核处理；取消伏笔使用 cancelled 并给 reason；paid 必须有已投放记录。

## 伏笔计划

outline 文件中的计划与实际记录分开。plant/payoff 是已纳入项目的集 ID，计划改动会使下游失效。样稿阶段只登记本次实际纳入范围的计划，未纳入集数的远期构想保留在文字中。

```outline-json
{"foreshadows":[{"id":"F001","plant":"EP001","payoff":"EP002"}]}
```

运行 `pipeline.py index PROJECT --through EP002 --object PROP001` 查询状态历史；不传 object 则返回所有对象。索引按需构建，缺覆盖或过期时为 UNVERIFIED，冲突/到期漏收为 CONFLICT。RECORDED 表示结构与记录可用，不是语义审核通过。未写到回收集不能按漏收处理。
