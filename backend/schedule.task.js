import { isProductMatured, getEstimatedDisplay } from "./common.util.js";
import { calcProductReturn } from "./product.calc.js";

/**
 * 每日定时主任务
 * @param {Array} productList 全量产品数组
 * @param {String} todayStr YYYY-MM-DD
 * @param {Function} getUnderlyingPrice 外部传入获取标的现价的方法
 */
export function dailyScheduleTask(productList, todayStr, getUnderlyingPrice) {
  productList.forEach(prod => {
    // 已到期直接跳过
    if (isProductMatured(prod, todayStr)) return;

    // 1. 更新标的现价
    prod.underlying_price = getUnderlyingPrice(prod.underlying);

    // 2. 计算当日估算基准（后台内核执行，前端三元隐藏）
    const S0 = 1; // 占位，实际由行情S0/St计算比例
    const St = prod.underlying_price ?? 0;
    const sRatio = S0 === 0 ? 1 : St / S0;
    prod.estimated_base = calcProductReturn(prod.product_type, prod.structure_params, sRatio, false);

    // 3. 判断是否到期日，锁定最终基准
    if (prod.end_obs_date === todayStr) {
      let hasKnockIn = false;
      // 三元敲入判断外部传入，本次不做回溯逻辑
      prod.performance_base = calcProductReturn(prod.product_type, prod.structure_params, sRatio, hasKnockIn);
      prod.estimated_base = null;
    }

    // 4. 判断提前敲出终止日
    if (prod.early_maturity_date === todayStr) {
      const sRatioFinal = prod.underlying_price / 1;
      prod.performance_base = calcProductReturn(prod.product_type, prod.structure_params, sRatioFinal, false);
      prod.estimated_base = null;
    }
  });

  return productList;
}