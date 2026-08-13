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

// 标的名称格式化映射（Excel原始值 -> 展示格式）
export const UNDERLYING_FORMAT = {
  "科创50": "科创50ETF（588000.SH）",
  "黄金": "黄金AU9999（SGE）",
  "中证1000": "中证1000（000852.SH）",
  "中证500": "中证500（000905.SH）",
  "沪深300": "沪深300（000300.SH）"
};

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