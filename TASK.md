# TASK.md — 原始任務需求

> ⚠️ 部分技術細節（尤其 actions 格式）已更新至 CONTEXT.md，以那邊為準。

## 目標
製作一個靜態 HTML Dashboard，視覺化 Sam 的 Aillio Bullet R1 烘豆機 2192 筆烘豆記錄。

## 資料位置
`/Users/leeabc/work/emilyorz/roast-dashboard/roasts/`
（2192 個 JSON 檔，每個是一次烘焙記錄）

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
