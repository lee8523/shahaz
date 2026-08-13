import { emptyFilter } from "./common.util.js";

/**
 * 统一收益计算函数（只输出年化，不计算实际金额）
 * @param {string} type 产品类型 single_shark / binary / three_element
 * @param {Object} params 结构参数
 * @param {number} sRatio St/S0 价格比例
 * @param {boolean} hasKnockIn 三元专用：是否触发过敲入
 * @returns {number|null} 年化小数
 */
export function calcProductReturn(type, params, sRatio, hasKnockIn = false) {
  const {
    strike_pct: K,
    up_barrier_pct: BU,
    min_return_pct: Rmin,
    knockout_base_pct: RKO,
    participation_rate: P
  } = params;

  if (Rmin === null || RKO === null) return null;

  switch (type) {
    case "single_shark":
      if (sRatio >= BU) {
        return RKO;
      } else if (sRatio >= K && sRatio < BU) {
        return Rmin + P * (sRatio - K);
      } else {
        return Rmin;
      }

    case "binary":
      return sRatio >= BU ? RKO : Rmin;

    case "three_element":
      if (sRatio >= BU) {
        return RKO;
      } else {
        return hasKnockIn ? Rmin : RKO;
      }

    default:
      return null;
  }
}