# CONTEXT.md — 專案背景與接手說明

> 最後更新：2026-03-08 by Emily

## 專案概述

將 Sam 的 Aillio Bullet R1 烘豆機 **2192 筆**烘焙記錄（來自 RoasTime app）視覺化成靜態 HTML Dashboard。

## 檔案結構

```
roast-dashboard/
├── dashboard.html       # 單頁靜態 dashboard（Chart.js，深色工業風）
├── generate_data.py     # 讀 roasts/ → 輸出 data.js
├── data.js              # [gitignored] 產生的資料，每次跑 generate_data.py 重新生成
├── roasts/              # [gitignored] 2192 個原始 JSON 烘焙記錄
├── roasts.tar.gz        # [gitignored] 原始打包檔（從 MacBook Pro 複製過來）
├── TASK.md              # 原始任務需求
└── CONTEXT.md           # 本檔案
```

## 快速啟動

```bash
# 1. 生成 data.js（需要 roasts/ 目錄存在）
python3 generate_data.py

# 2. 開 local server 預覽（直接開 file:// 會有 CORS 問題）
python3 -m http.server 8877
# 然後開 http://localhost:8877/dashboard.html
```

## 原始資料來源

- **機器**：MacBook Pro，IP `192.168.0.19`，user `leeabc`
- **路徑**：`/Users/Leeabc/Library/Application Support/roast-time/roasts/`
- **格式**：每個檔案是一筆烘焙記錄的 JSON（無副檔名）

## JSON 關鍵欄位

| 欄位 | 說明 |
|------|------|
| `dateTime` | 烘焙時間（ISO 或 timestamp ms） |
| `roastNumber` | 烘豆編號 |
| `weightGreen` | 生豆重量（g），很多是 0 未記錄，有效筆數 795 |
| `totalRoastTime` | 烘焙時間（秒） |
| `beanChargeTemperature` | 入豆後豆溫（℃，~130-175°C，非 IBTS 預熱溫） |
| `beanDropTemperature` | 出豆溫度（℃） |
| `actions` | 操作記錄（見下方） |

### actions 欄位格式（重要）

```json
{
  "actionTempList": [...],
  "actionTimeList": [
    {"ctrlType": 0, "index": 120, "value": 80},
    {"ctrlType": 1, "index": 240, "value": 9}
  ]
}
```

- `ctrlType`：0 = P（火力），1 = F（風扇），2 = D（轉速）
- `index`：觸發時間（秒）
- `value`：設定值

> ⚠️ 注意：早期 session log 誤記 actions 為 array 格式（`[{actionTime, name, value}]`），**實際是 dict**，以上面為準。

## 六個 Dashboard Panel

1. **總覽**：KPI（總次數 2192、本月、本週、平均時間 11m 57s）
2. **月度趨勢**：2021-10 ~ 2026-03，54 個月折線圖
3. **烘焙時間分布**：bin=30s，主峰在 600-900s
4. **入豆 / 出豆溫度分布**：雙色疊加直方圖（bin=5°C）
5. **豆量分布**：795 筆有效記錄（bin=50g）
6. **操作行為**：F/P/D 次數長條 + 平均觸發時間% + 前8步操作序列

## 資料統計摘要（2026-03-08）

- 總烘焙：**2,192** 次
- 時間範圍：**2021-10-03 ~ 2026-03-08**（4 年 5 個月）
- 平均烘焙時間：**11m 57s**（716.73s）
- 操作統計：P=10,059 次、F=8,744 次、D=4,649 次
- 平均觸發時間：P=37.05%、F=36.54%、D=6.78%

## Git / 部署

- **Repo**：`https://github.com/emilyorz/roast-dashboard`
- **SSH**：`GIT_SSH_COMMAND='ssh -i ~/.ssh/emily_github' git push origin main`
- **Collaborator**：leeabc（write 權限）

## 已知問題 / 待優化

- [ ] 月度趨勢 X 軸 54 個月標籤過密，可改成每季顯示一個
- [ ] 烘焙時間直方圖 X 軸標籤過密（bin=30s），可疏化或旋轉
- [ ] `beanChargeTemperature` 名稱誤導性高，未來可改成「入豆後豆溫」

## 開發歷程

- 2026-03-08 由 Emily（minimax-portal/MiniMax-M2.5）發起、Claude Code（Sonnet 4.6）實作
- Commit `fc3d502`：初版 v1
- Commit `5f73df9`：清理 repo 結構（移除誤 commit 的 2×2192 JSON）、修正 Panel 標題
