# 结构化交接协议 v1

Markdown 为默认可读交付物。需要导入生产系统时使用本协议导出 JSON；这是本项目约定，不是某个生成平台的直接 API 格式。下游自行转换为其需要的镜头或提示词字段。

## 标识与引用

- 角色 `CHAR001`、地点 `LOC001`、道具 `PROP001`：项目内唯一；服装变体可用 `CHAR001-LOOK01`。
- 集 `EP001`、场 `EP001-SC001`、时间块 `EP001-SC001-B001`、对白 `EP001-D001`、伏笔 `F001`。
- ID 分配后稳定；插场分配新 ID，在数组中调整顺序，不对旧场整体重编号。
- 人物名用于阅读，ID 用于关联；独白/画外音也要登记说话者，独立旁白可登记 `NARRATOR`。

## 顶层字段

| 字段 | 类型 | 要求 |
| --- | --- | --- |
| schema_version | string | 本协议为 `1.0` |
| project_id / episode_id / revision | string | 非空，唯一确定交付版本 |
| status | string | draft / reviewed / locked / superseded |
| source_script / bible_revision | string | 可追踪正文路径和设定版本 |
| lock_evidence | string 或 null | locked 时必须有实际依据；其他状态可 null |
| target_duration_seconds | object | min/max 正数且 min ≤ max |
| timing_basis | string | 估算方法及实测状态 |
| assets | object | characters/locations/props 数组，条目含 id/name；未用类型为空数组 |
| scenes | array | 按剧情顺序，每场结构见下 |
| unresolved | array[string] | 无则空数组；有则说明影响 |

场次必需字段：`id`、`location_id`、`time`、`character_ids`、`prop_ids`、`entry_state`、`blocks`、`exit_state`、`production_notes`。状态为可读字符串；blocks 为顺序数组，单块含 `id`、正数 `duration_seconds`、`action`、`dialogue`、`sound`、`screen_text`。对白含 `id`、`speaker_id`、`mode`（on_screen/off_screen/inner/narration）、`text`；sound 和 screen_text 为字符串数组，没有则空数组。

每块内动作、对白、声音可并行，总时长不得仅依字数相加。数组中各块按顺序串行。场次结束状态需要与下一场核对；结构检查不能替代语义检查。

## 最小格式示例

以下仅演示一个 8 秒片段，非完整单集，也非已获批准的制作稿。

```json
{
  "schema_version": "1.0",
  "project_id": "DEMO",
  "episode_id": "EP001",
  "revision": "v1.0",
  "status": "draft",
  "source_script": "episodes/EP001-v1.0.md",
  "bible_revision": "v1.0",
  "lock_evidence": null,
  "target_duration_seconds": {"min": 8, "max": 10},
  "timing_basis": "动作与对白并行，8秒预留；未朗读验证。",
  "assets": {
    "characters": [{"id": "CHAR001", "name": "林夏"}],
    "locations": [{"id": "LOC001", "name": "值班室"}],
    "props": [{"id": "PROP001", "name": "对讲机"}]
  },
  "scenes": [{
    "id": "EP001-SC001",
    "location_id": "LOC001",
    "time": "当晚，内景",
    "character_ids": ["CHAR001"],
    "prop_ids": ["PROP001"],
    "entry_state": "林夏独自值班，对讲机在桌面。",
    "blocks": [{
      "id": "EP001-SC001-B001",
      "duration_seconds": 8,
      "action": "林夏拿起对讲机，按下通话键，等待回复。",
      "dialogue": [{
        "id": "EP001-D001",
        "speaker_id": "CHAR001",
        "mode": "on_screen",
        "text": "有人在吗？"
      }],
      "sound": ["对讲机电流声，无人回答"],
      "screen_text": []
    }],
    "exit_state": "对讲机在林夏右手，尚未得到答复。",
    "production_notes": ["保留等待反应，不必连续展示按键手部特写。"]
  }],
  "unresolved": ["仅格式示例；完整剧情与实际录音尚未提供。"]
}
```

## 导出验收

1. JSON 可解析，字段类型正确，枚举有效，ID 唯一。
2. 场次及对白引用的角色、地点、道具存在；对白若来自画外角色，也需登记并列入场次角色引用。
3. 时间块时长为正且顺序相加落在目标范围；超范围说明原因并修订，不暗中改目标。
4. 逐句核对 JSON 与同版本正文，不丢对白、否定词、声音或关键屏幕文字。
5. 稿件状态、设定版本和锁定依据一致；空数组和 null 表达“无/未确认”，不要用假内容凑数。
6. 机器可解析只证明格式可读取；连续性、可表演性与制作接收情况仍需单独核实。
