import { PRODUCT_STATUS, UNDERLYING_FORMAT } from "./constant.js";

/**
 * 标的名称格式化
 */
export function formatUnderlying(name) {
  if (!name) return "--";
  return UNDERLYING_FORMAT[name] || name;
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
 * 估算基准渲染规则：三元全部隐藏显示--
 */
export function getEstimatedDisplay(prod) {
  if (prod.product_type === "three_element") return "--";
  return formatPercentShow(prod.estimated_base);
}