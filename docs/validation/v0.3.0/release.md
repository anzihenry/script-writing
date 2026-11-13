# 0.3.0 远端发布记录

2026-11-13，用户在M5本地验收完成后明确授权推送和发布。

- 发布入口：[v0.3.0](https://github.com/anzihenry/script-writing/releases/tag/v0.3.0)。
- 实现与集成提交：`7c4e7c9f6ef4aff107da30d19e2f0382dcd4e89d`，此前M0–M5六次提交已推送至main。
- 实现提交的[远端CI](https://github.com/anzihenry/script-writing/actions/runs/43389373275)：三项矩阵作业全部通过（Linux/Python3.9、Linux/Python3.15、macOS/Python3.15），均完成测试、规模测量与示例回放；原始结果见[release-ci.json](release-ci.json)。
- 标签包含实现提交及发布说明更新；最终标签提交的CI链接附在GitHub Release正文。发布说明更新不改变skills、scripts、tests、examples或CI工作流。

沿用仓库既有发布方式：Git标签与GitHub正式Release，GitHub提供源码压缩包，不另制安装包。发布说明保留108项工程测试、47/48保留集通过及1项未验证的边界；不把相同规则两组间差异当作方法收益。

[集成报告](integration/report.md)记录的是发布前本地验收时点，其中“远端CI未运行、未发布”保留为历史事实。真实配音、样片、外部接收和费用等未验证项不会因发布而变为通过。
