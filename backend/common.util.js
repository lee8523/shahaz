import { PRODUCT_STATUS } from "./constant.js";

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