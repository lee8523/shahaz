// 产品原始类型 -> 系统内部编码
export const PRODUCT_TYPE_MAP = {
  "固收+单鲨": "single_shark",
  "固收+二元": "binary",
  "固收+三元": "three_element"
};

// 内部编码 -> 前端中文展示
export const TYPE_LABEL = {
  single_shark: "鲨鱼鳍",
  binary: "二元",
  three_element: "三元"
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

// 标的名称格式化映射（已废弃，标准化后名称即展示名）
// formatUnderlying 函数现在直接返回原值

// 内置标的名称 → akshare代码映射（优先级低于用户配置）
export const BUILTIN_UNDERLYING_CODES = {
  "黄金": "AU9999",
  "AU9999": "AU9999",
  "中证1000": "000852",
  "000852": "000852",
  "中证500": "000905",
  "000905": "000905",
  "沪深300": "000300",
  "000300": "000300",
  "科创50": "588000",
  "588000": "588000"
};

// 标的品种名标准化映射（各种写法 -> 标准品种名）
export const UNDERLYING_VARIETY_MAP = {
  // 贵金属
  "白银": "白银",
  "沪银": "白银",
  "SGE黄金9999": "黄金",
  "黄金9999": "黄金",
  "黄金AU9999": "黄金",
  "黄金": "黄金",
  // 有色金属
  "沪铜": "沪铜",
  "沪铝": "沪铝",
  "碳酸锂": "碳酸锂",
  // 指数
  "中证1000": "中证1000",
  "中证500": "中证500",
  "沪深300": "沪深300",
  "科创50": "科创50",
  "科创50ETF": "科创50",
  "创业板ETF": "创业板",
  "恒生科技ETF": "恒生科技",
  "南方东英恒生科技etf": "恒生科技",
  "恒生科技": "恒生科技"
};