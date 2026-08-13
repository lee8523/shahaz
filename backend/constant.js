// 产品原始类型 -> 系统内部编码
export const PRODUCT_TYPE_MAP = {
  "固收+单鲨": "single_shark",
  "固收+二元": "binary",
  "固收+三元": "three_element"
};

// 内部编码 -> 前端中文展示
export const TYPE_LABEL = {
  single_shark: "单鲨鲨鱼鳍结构",
  binary: "二元看涨结构",
  three_element: "三元雪球结构"
};

// 全部合法结构类型
export const ALL_PRODUCT_TYPES = ["single_shark", "binary", "three_element"];

// 产品状态枚举
export const PRODUCT_STATUS = {
  RUNNING: "存续中",
  EARLY_TERMINATE: "提前敲出终止",
  MATURED: "已到期结算",
  PENDING_INPUT: "待录入兑付收益"
};