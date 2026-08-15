import { PRODUCT_STATUS, UNDERLYING_FORMAT, UNDERLYING_VARIETY_MAP } from "./constant.js";

/**
 * 标的名称格式化（用于展示）
 */
export function formatUnderlying(name) {
  if (!name) return "--";
  return UNDERLYING_FORMAT[name] || name;
}

/**
 * 标的标准化：提取品种+合约代码
 * @param {string} raw 原始标的字符串
 * @returns {object} {standard: "白银2604", variety: "白银", contract: "2604"} 
 *                   或 {standard: "中证1000", variety: "中证1000", contract: null} (指数类)
 *                   或 {needConfirm: true, rawName: "沪铜期货", variety: "沪铜"} 表示需要用户补全
 */
export function normalizeUnderlying(raw) {
  if (!raw) return { standard: null, variety: null, contract: null };
  
  const trimmed = raw.trim();
  
  // 不需要合约代码的品种（指数、现货等）
  const NO_CONTRACT_VARIETIES = ["黄金", "中证1000", "中证500", "沪深300", "科创50", "创业板", "恒生科技"];
  
  // 1. 先尝试直接匹配映射表（处理"中证1000"、"黄金"等简单情况）
  for (const [key, value] of Object.entries(UNDERLYING_VARIETY_MAP)) {
    if (trimmed === key || trimmed.startsWith(key)) {
      // 检查是否是不需要合约代码的品种
      if (NO_CONTRACT_VARIETIES.includes(value)) {
        return { standard: value, variety: value, contract: null };
      }
    }
  }
  
  // 2. 提取合约代码（字母+数字，如AG2604、CU2608、AL2608）
  // 支持格式：AG2604、CU2608.SHF、588000.SH
  const codeMatch = trimmed.match(/([A-Za-z]{1,3})(\d{3,4})(?:\.[A-Z]+)?/);
  
  // 3. 提取品种名（从开头提取中文字符，直到遇到数字、括号或特定后缀）
  let variety = "";
  
  // 尝试匹配：中文字符 + 可选的"期货"/"ETF"/"指数"后缀
  const varietyMatch = trimmed.match(/^([\u4e00-\u9fa5]+?)(?:期货|ETF|指数|和|ETF指数)?(?:\s|[\(（]|$|\d)/);
  if (varietyMatch) {
    variety = varietyMatch[1].trim();
  } else {
    // 如果上面没匹配到，尝试更宽松的匹配：取所有开头的中文字符
    const cnMatch = trimmed.match(/^([\u4e00-\u9fa5]+)/);
    if (cnMatch) {
      variety = cnMatch[1].trim();
    }
  }
  
  // 4. 品种名标准化映射
  const normalizedVariety = UNDERLYING_VARIETY_MAP[variety] || variety;
  
  // 5. 判断是否需要合约代码
  const needsContract = !NO_CONTRACT_VARIETIES.includes(normalizedVariety);
  
  if (needsContract) {
    // 期货类需要合约代码
    if (codeMatch) {
      const contract = codeMatch[2]; // 只取数字部分
      const standard = normalizedVariety + contract;
      return { standard, variety: normalizedVariety, contract };
    } else {
      // 没有合约代码，需要用户补全
      return { needConfirm: true, rawName: trimmed, variety: normalizedVariety };
    }
  } else {
    // 指数/现货类不需要合约代码
    return { standard: normalizedVariety, variety: normalizedVariety, contract: null };
  }
}

/**
 * 产品名称格式化（去除"华夏资本"）
 */
export function formatProductName(name) {
  if (!name) return "--";
  return name.replace(/^华夏资本/, "");
}

/**
 * 空值过滤：/ 空字符串 undefined null 统一返回null
 */
export function emptyFilter(val) {
  if (val === undefined || val === null) return null;
  const s = String(val).trim();
  return s === "" || s === "/" ? null : s;
}

/**
 * 百分比字符串转小数 "4%" => 0.04
 */
export function parsePercentStr(str) {
  const clean = emptyFilter(str);
  if (clean === null) return null;
  let numStr = clean.replace(/%|\/年/g, "").trim();
  const num = parseFloat(numStr);
  return isNaN(num) ? null : num / 100;
}

/**
 * 日期标准化 YYYY-MM-DD
 */
export function formatDate(raw) {
  const clean = emptyFilter(raw);
  if (!clean) return null;
  const d = new Date(clean);
  if (isNaN(d.getTime())) return null;
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * 从混合文本提取日期（支持Excel序列号、纯日期、带文字日期、中文日期）
 */
export function extractDate(raw) {
  const clean = emptyFilter(raw);
  if (!clean) return null;
  
  // Excel序列号（数字）
  if (/^\d+(\.\d+)?$/.test(clean)) {
    const serial = parseFloat(clean);
    const d = new Date(Date.UTC(1899, 11, 30) + serial * 86400000);
    if (!isNaN(d.getTime())) {
      return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,'0')}-${String(d.getUTCDate()).padStart(2,'0')}`;
    }
  }
  
  // 中文日期格式：YYYY年MM月DD日
  const cnMatch = clean.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (cnMatch) {
    const y = cnMatch[1], m = cnMatch[2].padStart(2,'0'), d = cnMatch[3].padStart(2,'0');
    const dt = new Date(`${y}-${m}-${d}`);
    if (!isNaN(dt.getTime())) return `${y}-${m}-${d}`;
  }
  
  // 提取文本中的日期数字 YYYY-MM-DD 或 YYYY/MM/DD
  const m = clean.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
  if (m) {
    const d = new Date(`${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`);
    if (!isNaN(d.getTime())) return `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
  }
  
  return formatDate(clean);
}

/**
 * 解析期限字段：支持"XX个月"/"XX年"或日期
 */
export function parseMaturity(term, establishDate) {
  const clean = emptyFilter(term);
  if (!clean) return null;
  
  const date = extractDate(clean);
  if (date) return date;
  
  if (!establishDate) return null;
  const base = new Date(establishDate);
  
  const monthMatch = clean.match(/(\d+)\s*个月/);
  if (monthMatch) {
    base.setMonth(base.getMonth() + parseInt(monthMatch[1]));
    return `${base.getFullYear()}-${String(base.getMonth()+1).padStart(2,'0')}-${String(base.getDate()).padStart(2,'0')}`;
  }
  
  const yearMatch = clean.match(/(\d+)\s*年/);
  if (yearMatch) {
    base.setFullYear(base.getFullYear() + parseInt(yearMatch[1]));
    return `${base.getFullYear()}-${String(base.getMonth()+1).padStart(2,'0')}-${String(base.getDate()).padStart(2,'0')}`;
  }
  
  return null;
}

/**
 * 百分比格式化展示 0.04 => 4.00%
 */
export function formatPercentShow(num) {
  if (num === null || num === undefined) return "--";
  return `${(num * 100).toFixed(2)}%`;
}

/**
 * 标的价格格式化
 */
export function formatPriceShow(price) {
  if (price === null || price === undefined || isNaN(price)) return "--";
  return Number(price).toFixed(2);
}

/**
 * 判断产品是否已到期
 */
export function isProductMatured(prod, todayStr) {
  // 1. 已有最终计提基准
  if (prod.performance_base !== null) return true;
  // 2. 存在提前终止日
  if (prod.early_maturity_date) return true;
  // 3. 超过合同到期日
  if (!prod.contract_maturity_date) return false;
  const today = new Date(todayStr);
  const endDate = new Date(prod.contract_maturity_date);
  return today > endDate;
}

/**
 * 获取产品状态文本与样式class
 */
export function getProductStatusInfo(prod, todayStr) {
  const matured = isProductMatured(prod, todayStr);
  if (prod.early_maturity_date) {
    return { text: PRODUCT_STATUS.EARLY_TERMINATE, className: "tag-red" };
  }
  if (matured) {
    if (prod.actual_final_return === null) {
      return { text: PRODUCT_STATUS.PENDING_INPUT, className: "tag-yellow" };
    }
    return { text: PRODUCT_STATUS.MATURED, className: "tag-gray" };
  }
  return { text: PRODUCT_STATUS.RUNNING, className: "tag-green" };
}

/**
 * 估算基准渲染规则：三元隐藏，其他根据当前价格实时计算
 * @param {Object} prod 产品对象
 * @param {number} initialPrice 期初价格（可选）
 */
export function getEstimatedDisplay(prod, initialPrice) {
  if (prod.product_type === "three_element") return "--";
  
  // 如果没有期初价格或当前价格，返回已存储的值或--
  if (!initialPrice || !prod.underlying_price) {
    return formatPercentShow(prod.estimated_base);
  }
  
  // 实时计算估算基准
  const sRatio = prod.underlying_price / initialPrice;
  const p = prod.structure_params;
  
  if (!p || p.min_return_pct === null || p.knockout_base_pct === null) {
    return formatPercentShow(prod.estimated_base);
  }
  
  const K = p.strike_pct;
  const BU = p.up_barrier_pct;
  const Rmin = p.min_return_pct;
  const RKO = p.knockout_base_pct;
  const P = p.participation_rate || 0;
  
  let result;
  
  switch (prod.product_type) {
    case "single_shark":
      if (sRatio >= BU) {
        result = RKO;
      } else if (sRatio >= K && sRatio < BU) {
        result = Rmin + P * (sRatio - K);
      } else {
        result = Rmin;
      }
      break;
      
    case "binary":
      result = sRatio >= BU ? RKO : Rmin;
      break;
      
    default:
      result = prod.estimated_base;
  }
  
  return formatPercentShow(result);
}