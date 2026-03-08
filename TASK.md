# RoastTime Dashboard 任務說明

## 目標
製作一個靜態 HTML Dashboard，視覺化 Sam 的 Aillio Bullet R1 烘豆機 2192 筆烘豆記錄。

## 資料位置
`/Users/leeabc/work/emilyorz/roast-dashboard/roasts/`
（2192 個 JSON 檔，每個是一次烘焙記錄）

## JSON 結構（每筆關鍵欄位）
- `dateTime` - 烘焙時間（ISO 或 timestamp）
- `roastNumber` - 烘豆編號
- `weightGreen` - 生豆重量（g），很多是 0（未記錄）
- `totalRoastTime` - 烘焙時間（秒）
- `beanChargeTemperature` - 入豆溫度（IBTS，℃）
- `beanDropTemperature` - 出豆溫度（℃）
- `drumChargeTemperature` - 鼓溫（入豆時）
- `preheatTemperature` - 預熱溫度（用 drumChargeTemperature 更準確）
- `beanTemperature[]` - 豆溫曲線（陣列）
- `drumTemperature[]` - 鼓溫曲線（陣列）
- `beanDerivative[]` - ROR（豆溫上升率）曲線
- `actions` - 操作記錄，格式 `[{actionTime, name, value}, ...]`
  - name 類型：F（風扇 Fan）、P（火力 Power）、D（轉速 Drum）

## 分析需求（三個面向）

### 1️⃣ 產能報告
- 總烘豆次數、時間範圍
- 每月烘豆次數折線/長條圖
- 烘焙時間分布直方圖

### 2️⃣ 參數一致性
- 入豆溫分布（所有記錄的 beanChargeTemperature 直方圖）
- 出豆溫分布直方圖
- 豆量分布（只用 weightGreen > 0 的記錄）

### 4️⃣ 操作行為
- 操作類型統計（F/P/D 各發生幾次）
- 操作時間點分析（每種操作平均在幾%烘焙時間時觸發）
- 展示「平均一次烘焙的操作序列」

## 技術規格

### Step 1：Python 預處理腳本（generate_data.py）
- 讀取 roasts/ 下所有 JSON
- 整理成 dashboard 需要的格式
- 輸出 `data.js`（`const ROAST_DATA = {...}`）

### Step 2：靜態 HTML（dashboard.html）
- 單檔，引用 data.js
- 使用 Chart.js（CDN）
- 風格：Industrial/深色，咖啡機感，Monospace 字體
- 六個 Panel 排列：
  1. KPI Header（總次數、本月、本週、平均時間）
  2. 月度趨勢折線圖
  3. 烘焙時間分布直方圖
  4. 入豆/出豆溫度分布
  5. 豆量分布（有記錄的 795 筆）
  6. 操作行為長條圖

## 完成後
1. `git add -A && git commit -m "feat: RoastTime dashboard v1"`
2. `GIT_SSH_COMMAND="ssh -i ~/.ssh/emily_github" git push origin main`
3. 通知 Emily（OpenClaw）：`openclaw message send --channel telegram --target 8566658313 --text "✅ roast-dashboard 完成！https://github.com/emilyorz/roast-dashboard"`
