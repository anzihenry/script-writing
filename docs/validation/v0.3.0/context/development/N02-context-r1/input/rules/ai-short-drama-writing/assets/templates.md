# 剧本生产模板入口

以下为可复制的实际模板，按任务取用；`project-template/` 为唯一维护源，不再在本文件复制正文。初始化命令会替换项目/集ID并创建工作目录。每个新文件都有未填写标记，不能注册成已完成产物。

小型任务可只交付所需章节；进入批量管线时使用 project.json 跟踪版本，详见[生产管线](../references/pipeline.md)及[命令与数据协议](../references/operations.md)。

## 建议目录

```text
project.json
brief.md
bible.md
outline.md
changes.md
decisions.md
feedback.md
episodes/EP001-v1.0.md
continuity/EP001-v1.0.md
reviews/EP001-v1.0.md
handoff/EP001-v1.0.md
```

整季伏笔与跨集计划放 outline.md；正文实际状态按集保存在 continuity/，避免修改一集让全季台账依赖相互成环。旧项目可保留原文件名，但登记时应按真实依赖拆出单集记录或明确最小作用范围。

## 1. 项目简报

复制[项目简报模板](project-template/brief.md)。

## 2. 故事设定

复制[故事设定模板](project-template/bible.md)。

## 3. 分集规划

复制[分集规划模板](project-template/outline.md)。

## 4. 单集剧本

复制[单集剧本模板](project-template/episode.md)。

## 5. 连续性

复制[连续性模板](project-template/continuity.md)。

## 6. 审核记录

复制[审核记录模板](project-template/review.md)。

## 7. 制作交接

复制[制作交接模板](project-template/handoff.md)。

## 8. 变更记录

复制[变更记录模板](project-template/changes.md)。

## 决策与反馈

[决策与例外模板](project-template/decisions.md)记录选项及依据；[下游反馈模板](project-template/feedback.md)记录实际返回的问题与回验。
