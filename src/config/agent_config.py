"""子Agent模型配置管理 - 支持硅基流动."""

import os
from dataclasses import dataclass
from typing import Optional

# Load environment variables early
import dotenv
dotenv.load_dotenv()


@dataclass
class SubAgentModelConfig:
    """子Agent模型配置 - 针对硅基流动优化.
    
    支持为不同的子agent配置独立的模型，实现成本优化。
    
    环境变量:
        SILICONFLOW_API_KEY: 硅基流动API密钥（必填）
        SILICONFLOW_MODEL: 主Agent模型（可选，默认：deepseek-chat）
        SILICONFLOW_PDF_MODEL: PDF分析子Agent模型（可选）
        SILICONFLOW_REPORT_MODEL: 报告生成子Agent模型（可选）
    
    示例:
        >>> from config.agent_config import agent_model_config
        >>> print(agent_model_config.get_model_summary())
        {
            "main_agent": "deepseek-chat",
            "pdf_analyzer": "Qwen/Qwen2.5-7B-Instruct",
            "report_generator": "Qwen/Qwen2.5-72B-Instruct"
        }
    """
    
    # 主Agent模型
    main_model: str = "deepseek-chat"  # DeepSeek-V3, ¥1.33/百万tokens
    
    # PDF分析子Agent（轻量任务，适合文本提取）
    pdf_analyzer_model: Optional[str] = "Qwen/Qwen2.5-7B-Instruct"  # ¥0.42/百万tokens
    
    # 报告生成子Agent（高质量输出）
    report_generator_model: Optional[str] = "Qwen/Qwen2.5-72B-Instruct"  # ¥3.5/百万tokens
    
    # 硅基流动配置
    siliconflow_api_key: Optional[str] = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    
    # 模型参数配置
    temperature: float = 0.7  # 温度参数 (0.0-1.0)，控制输出随机性
    max_tokens: int = 20000   # 最大输出token数
    top_p: Optional[float] = None  # Top-p采样参数 (0.0-1.0)
    frequency_penalty: Optional[float] = None  # 频率惩罚 (-2.0-2.0)
    presence_penalty: Optional[float] = None  # 存在惩罚 (-2.0-2.0)
    
    # API配置
    api_timeout: int = 60  # API超时时间（秒）
    api_retry_attempts: int = 3  # API重试次数
    
    # 子Agent独立参数（可选）
    pdf_analyzer_temperature: Optional[float] = None  # PDF分析专用温度
    report_generator_temperature: Optional[float] = None  # 报告生成专用温度
    
    def __post_init__(self):
        """从环境变量加载配置."""
        # 加载API密钥
        self.siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY")
        
        # 加载模型配置
        self.main_model = os.getenv("SILICONFLOW_MODEL", self.main_model)
        self.pdf_analyzer_model = os.getenv("SILICONFLOW_PDF_MODEL", self.pdf_analyzer_model)
        self.report_generator_model = os.getenv("SILICONFLOW_REPORT_MODEL", self.report_generator_model)
        
        # 加载通用模型参数
        if temp := os.getenv("SILICONFLOW_TEMPERATURE"):
            self.temperature = float(temp)
        if tokens := os.getenv("SILICONFLOW_MAX_TOKENS"):
            self.max_tokens = int(tokens)
        if top_p := os.getenv("SILICONFLOW_TOP_P"):
            self.top_p = float(top_p)
        if freq_penalty := os.getenv("SILICONFLOW_FREQUENCY_PENALTY"):
            self.frequency_penalty = float(freq_penalty)
        if pres_penalty := os.getenv("SILICONFLOW_PRESENCE_PENALTY"):
            self.presence_penalty = float(pres_penalty)
        
        # 加载API配置
        if timeout := os.getenv("SILICONFLOW_API_TIMEOUT"):
            self.api_timeout = int(timeout)
        if retry := os.getenv("SILICONFLOW_API_RETRY"):
            self.api_retry_attempts = int(retry)
        
        # 加载子Agent独立参数
        if pdf_temp := os.getenv("SILICONFLOW_PDF_TEMPERATURE"):
            self.pdf_analyzer_temperature = float(pdf_temp)
        if report_temp := os.getenv("SILICONFLOW_REPORT_TEMPERATURE"):
            self.report_generator_temperature = float(report_temp)
    
    def create_model_instance(
        self,
        model_name: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """创建模型实例.
        
        Args:
            model_name: 模型名称（如: "Qwen/Qwen2.5-7B-Instruct"）
            temperature: 温度参数（可选），不指定则使用配置的默认值
            max_tokens: 最大token数（可选），不指定则使用配置的默认值
            **kwargs: 其他参数（top_p, frequency_penalty等）
        
        Returns:
            ChatOpenAI实例，配置了硅基流动的base_url
        
        Raises:
            ValueError: 如果SILICONFLOW_API_KEY未配置
        """
        if not self.siliconflow_api_key:
            raise ValueError(
                "SILICONFLOW_API_KEY not configured. "
                "Please set it in your environment variables or .env file."
            )
        
        from langchain_openai import ChatOpenAI
        
        # 构建模型参数
        model_kwargs = {
            "model": model_name,
            "base_url": self.siliconflow_base_url,
            "api_key": self.siliconflow_api_key,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "timeout": self.api_timeout,
            "max_retries": self.api_retry_attempts,
        }
        
        # 添加可选参数
        if self.top_p is not None:
            model_kwargs["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            model_kwargs["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            model_kwargs["presence_penalty"] = self.presence_penalty
        
        # 合并用户提供的额外参数
        model_kwargs.update(kwargs)
        
        return ChatOpenAI(**model_kwargs)
    
    def get_model_summary(self) -> dict[str, str]:
        """获取模型配置摘要.
        
        Returns:
            包含所有agent模型配置的字典
        """
        return {
            "main_agent": self.main_model,
            "pdf_analyzer": self.pdf_analyzer_model or f"default ({self.main_model})",
            "report_generator": self.report_generator_model or f"default ({self.main_model})"
        }
    
    def get_cost_estimate(self, pdf_count: int = 10) -> dict[str, any]:
        """估算成本.
        
        Args:
            pdf_count: PDF文件数量
        
        Returns:
            包含成本估算的字典
        """
        # 价格表 (¥/百万tokens)
        prices = {
            "deepseek-chat": 1.33,
            "Qwen/Qwen2.5-7B-Instruct": 0.42,
            "Qwen/Qwen2.5-72B-Instruct": 3.5,
        }
        
        # 假设每次调用平均1k tokens
        main_cost = (pdf_count * 0.001) * prices.get(self.main_model, 1.33)
        pdf_cost = (pdf_count * 0.001) * prices.get(self.pdf_analyzer_model, 1.33)
        report_cost = (1 * 0.001) * prices.get(self.report_generator_model, 1.33)
        
        total_cost = main_cost + pdf_cost + report_cost
        
        # 计算使用统一模型的成本
        uniform_cost = (pdf_count * 2 + 1) * 0.001 * prices.get(self.main_model, 1.33)
        savings = uniform_cost - total_cost
        savings_percent = (savings / uniform_cost) * 100 if uniform_cost > 0 else 0
        
        return {
            "total_cost_yuan": round(total_cost, 4),
            "savings_yuan": round(savings, 4),
            "savings_percent": round(savings_percent, 1),
            "pdf_count": pdf_count,
            "breakdown": {
                "main_agent": round(main_cost, 4),
                "pdf_analyzer": round(pdf_cost, 4),
                "report_generator": round(report_cost, 4)
            }
        }


# 全局配置实例
agent_model_config = SubAgentModelConfig()

