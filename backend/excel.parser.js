import { PRODUCT_TYPE_MAP } from "./constant.js";
import {
  emptyFilter,
  parsePercentStr,
  formatDate,
  extractDate,
  parseMaturity
} from "./common.util.js";

/**
 * 单条Excel行解析 + 参数合法性校验
 */
export function parseExcelRow(row) {
  const errors = [];

  // 基础字段
  const product_code = emptyFilter(row["产品代码"]);
  const product_name = emptyFilter(row["产品简称"]);
  const product_type_raw = emptyFilter(row["固收+期权产品类型"]);
  const underlying = emptyFilter(row["挂钩标的"]);

  // 结构参数解析
  const strike_pct = parsePercentStr(row["行权价格"]);
  const up_barrier_pct = parsePercentStr(row["上涨障碍价"]);
  const down_barrier_pct = parsePercentStr(row["下跌障碍价"]);
  const participation_rate = parsePercentStr(row["上涨参与率"]);
  const min_return_pct = parsePercentStr(row["最低收益"]);
  const knockout_base_pct = parsePercentStr(row["敲出收益"]);

  // 日期
  const establish_date = formatDate(row["产品成立日"]);
  const start_obs_date = extractDate(row["期初观察日"]);
  const end_obs_date = extractDate(row["期末观察日"]);
  const early_maturity_date = extractDate(row["产品提前终止日"]);
  const contract_maturity_date = parseMaturity(row["固收+期权结构期限"], establish_date) 
    || extractDate(row["合同到期日"]);
  
  // 最终基准（实际业绩报酬计提基准）
  const performance_base = parsePercentStr(row["实际业绩报酬计提基准"]);

  // 类型映射
  const product_type = PRODUCT_TYPE_MAP[product_type_raw] ?? null;

  // ========== 数据合法性校验 ==========
  if (!product_code) errors.push("产品代码不能为空");
  if (!product_type) errors.push(`无法识别产品类型：${product_type_raw}`);

  // 结构参数逻辑校验
  if (participation_rate !== null && participation_rate < 0) {
    errors.push("上涨参与率不能为负数");
  }
  if (up_barrier_pct !== null && strike_pct !== null && up_barrier_pct < strike_pct) {
    errors.push("上涨敲出价不能小于行权价");
  }

  if (errors.length > 0) {
    return { valid: false, errors, data: null };
  }

  // 组装标准对象
  const product = {
    product_code,
    product_name,
    product_type_raw,
    product_type,
    underlying,
    underlying_price: null, // 标的现价，行情接口回填
    establish_date,
    start_obs_date,
    end_obs_date,
    early_maturity_date,
    contract_maturity_date,

    performance_base: performance_base,
    estimated_base: null,
    actual_final_return: null,

    structure_params: {
      strike_pct,
      up_barrier_pct,
      down_barrier_pct,
      participation_rate,
      min_return_pct,
      knockout_base_pct,
      knock_out_obs_dates: [],
      obs_manual_confirm: false
    },

    event_record: {
      is_early_terminate: !!early_maturity_date,
      knockout_occur_date: early_maturity_date
    }
  };

  return { valid: true, errors: [], data: product };
}

/**
 * 批量解析Excel数组，并处理重复主键
 * @param {Array} rows Excel原始行数组
 * @param {String} repeatMode 重复策略 cover覆盖 / skip跳过 / cancel取消
 */
export function batchParseExcel(rows, existCodes, repeatMode = "cover") {
  const result = {
    successList: [],
    failList: [],
    repeatList: []
  };

  for (const row of rows) {
    const res = parseExcelRow(row);
    if (!res.valid) {
      result.failList.push({ row, errors: res.errors });
      continue;
    }
    const prod = res.data;
    if (existCodes.has(prod.product_code)) {
      if (repeatMode === "skip") {
        result.repeatList.push(prod.product_code);
        continue;
      }
      // cover模式直接加入，上层做替换
    }
    result.successList.push(prod);
  }

  return result;
}