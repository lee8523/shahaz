# 场外期权结构化产品台账

固收+期权结构化产品的跟踪与公示系统：GitHub Actions 每日自动拉取标的行情、检测敲出、结算期末基准；前端纯静态页面面向投资人展示产品信息与收益估算。

## 架构

```
GitHub Actions (每日 16:00 北京时间)
  └─ backend/update_prices.py
       ├─ [1/4] 刷新实时价   → backend/prices.json
       ├─ [2/4] 刷新期初价   → backend/initial_prices.json
       ├─ [3/4] 单鲨敲出检测 → products.json（敲出日+冻结敲出日收盘价）
       └─ [4/4] 期末结算     → products.json（最终基准+冻结期末收盘价）
     依赖 backend/vendor/market-data（git submodule，多数据源 fallback）

backend/*.json  ← 唯一数据源（无数据库）

frontend/  纯静态 HTML + ES Module，无构建步骤，直接 import backend/*.js
  ├─ admin/index.html      管理后台（Excel导入/编辑/删除，经 GitHub API 写回）
  ├─ invest/investor_list.html  产品列表公示
  └─ invest/investor_view.html  单产品详情
```

## 关键规则

- **收益公式唯一来源**：`backend/product.calc.js`。Python 侧结算（update_prices.py 第4步）与它保持一致，改公式需两边同步。
- **现价冻结**：产品过了期末观察日后，前端不再用行情覆盖其"标的现价"；脚本在敲出/结算时把事件日收盘价写入产品作为冻结值。每日行情只刷新仍有存续产品的标的。
- **三元产品不自动结算**（涉及敲入判定，暂人工录入 `performance_base`）。
- 到期产品先锁定"最终基准"（业绩报酬计提基准，仅为费用计提标准，不构成收益承诺），实际兑付收益由人工录入 `actual_final_return`。

## 日常维护

| 操作 | 位置 |
|------|------|
| 新增产品 | admin 页 Excel 导入，或直接编辑 products.json |
| 编辑产品参数 | admin 详情弹窗"保存修改"（写回 GitHub） |
| 新增标的 | products.json 的 `underlyings` 加 `"名称": {"code": "代码"}` |
| 改收益公式 | backend/product.calc.js + update_prices.py settle_final_base |
| 改敲出/结算逻辑 | backend/update_prices.py |
| 改数据源/fallback | backend/vendor/market-data（submodule，独立仓库） |
| 补录期初/期末观察日 | products.json 对应产品字段 |

## 本地预览

```bash
python -m http.server 8080
# 浏览器打开 http://localhost:8080/frontend/invest/investor_list.html
```

本地跑每日任务：`python backend/update_prices.py`（需 requests；黄金/期货 K 线部分数据源在公司网络下可能取不到，Actions 环境正常）。

## 已知注意点

- admin 的 GitHub PAT 存于浏览器 localStorage，注意页面别引入第三方脚本。
- Excel 导入依赖 cdn.sheetjs.com，内网不通时导入不可用。
- `double_shark`（双鲨）仅做了类型映射与展示，无收益计算分支，产品到期后人工录入基准。
