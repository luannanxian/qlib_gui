"""
Strategy Template Seed Data

Seeds 8 built-in strategy templates covering different categories:
- TREND_FOLLOWING (3 templates)
- OSCILLATION (3 templates)
- MULTI_FACTOR (2 templates)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.models.strategy import StrategyTemplate, StrategyCategory


STRATEGY_TEMPLATES = [
    # ========================================
    # TREND_FOLLOWING Strategies
    # ========================================
    {
        "id": "template-trend-ma-double",
        "name": "双均线策略 (Double MA Crossover)",
        "category": StrategyCategory.TREND_FOLLOWING,
        "description": "基于短期和长期移动平均线交叉的经典趋势跟踪策略。当短期均线上穿长期均线时买入,下穿时卖出。",
        "logic_flow": {
            "nodes": [
                {"id": "ma_short", "type": "INDICATOR", "indicator": "MA", "parameters": {"period": 5}},
                {"id": "ma_long", "type": "INDICATOR", "indicator": "MA", "parameters": {"period": 20}},
                {"id": "condition_buy", "type": "CONDITION", "condition": "ma_short > ma_long"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "ma_short < ma_long"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "ma_short", "to": "condition_buy"},
                {"from": "ma_long", "to": "condition_buy"},
                {"from": "condition_buy", "to": "signal_buy"},
                {"from": "ma_short", "to": "condition_sell"},
                {"from": "ma_long", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "ma_short_period": {"type": "int", "default": 5, "min": 3, "max": 20, "description": "短期均线周期"},
            "ma_long_period": {"type": "int", "default": 20, "min": 10, "max": 60, "description": "长期均线周期"}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.35,
            "sharpe": 1.2,
            "max_drawdown": -0.15
        }
    },
    {
        "id": "template-trend-macd",
        "name": "MACD策略 (MACD Strategy)",
        "category": StrategyCategory.TREND_FOLLOWING,
        "description": "使用MACD指标的金叉和死叉信号进行交易。MACD线上穿信号线时买入,下穿时卖出。",
        "logic_flow": {
            "nodes": [
                {"id": "macd", "type": "INDICATOR", "indicator": "MACD", "parameters": {"fast": 12, "slow": 26, "signal": 9}},
                {"id": "condition_buy", "type": "CONDITION", "condition": "macd_line > signal_line"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "macd_line < signal_line"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "macd", "to": "condition_buy"},
                {"from": "condition_buy", "to": "signal_buy"},
                {"from": "macd", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "fast_period": {"type": "int", "default": 12, "min": 5, "max": 20},
            "slow_period": {"type": "int", "default": 26, "min": 15, "max": 40},
            "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.28,
            "sharpe": 1.1,
            "max_drawdown": -0.18
        }
    },
    {
        "id": "template-trend-turtle",
        "name": "海龟交易法 (Turtle Trading)",
        "category": StrategyCategory.TREND_FOLLOWING,
        "description": "基于唐奇安通道突破的经典趋势跟踪策略。价格突破N日最高点买入,跌破N日最低点卖出。",
        "logic_flow": {
            "nodes": [
                {"id": "highest", "type": "INDICATOR", "indicator": "HIGHEST", "parameters": {"period": 20}},
                {"id": "lowest", "type": "INDICATOR", "indicator": "LOWEST", "parameters": {"period": 10}},
                {"id": "condition_buy", "type": "CONDITION", "condition": "close > highest"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "close < lowest"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "highest", "to": "condition_buy"},
                {"from": "condition_buy", "to": "signal_buy"},
                {"from": "lowest", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "entry_period": {"type": "int", "default": 20, "min": 10, "max": 60},
            "exit_period": {"type": "int", "default": 10, "min": 5, "max": 30}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.42,
            "sharpe": 1.3,
            "max_drawdown": -0.20
        }
    },

    # ========================================
    # OSCILLATION Strategies
    # ========================================
    {
        "id": "template-osc-rsi",
        "name": "RSI震荡策略 (RSI Oscillation)",
        "category": StrategyCategory.OSCILLATION,
        "description": "使用RSI指标判断超买超卖。RSI低于30时买入,高于70时卖出。",
        "logic_flow": {
            "nodes": [
                {"id": "rsi", "type": "INDICATOR", "indicator": "RSI", "parameters": {"period": 14}},
                {"id": "condition_oversold", "type": "CONDITION", "condition": "rsi < 30"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_overbought", "type": "CONDITION", "condition": "rsi > 70"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "rsi", "to": "condition_oversold"},
                {"from": "condition_oversold", "to": "signal_buy"},
                {"from": "rsi", "to": "condition_overbought"},
                {"from": "condition_overbought", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "rsi_period": {"type": "int", "default": 14, "min": 7, "max": 28},
            "oversold_threshold": {"type": "int", "default": 30, "min": 20, "max": 40},
            "overbought_threshold": {"type": "int", "default": 70, "min": 60, "max": 80}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.22,
            "sharpe": 0.9,
            "max_drawdown": -0.12
        }
    },
    {
        "id": "template-osc-boll",
        "name": "布林带策略 (Bollinger Bands)",
        "category": StrategyCategory.OSCILLATION,
        "description": "使用布林带上下轨判断买卖点。价格触及下轨买入,触及上轨卖出。",
        "logic_flow": {
            "nodes": [
                {"id": "boll", "type": "INDICATOR", "indicator": "BOLL", "parameters": {"period": 20, "std": 2}},
                {"id": "condition_buy", "type": "CONDITION", "condition": "close < lower_band"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "close > upper_band"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "boll", "to": "condition_buy"},
                {"from": "condition_buy", "to": "signal_buy"},
                {"from": "boll", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "period": {"type": "int", "default": 20, "min": 10, "max": 50},
            "std_dev": {"type": "number", "default": 2.0, "min": 1.0, "max": 3.0}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.19,
            "sharpe": 0.85,
            "max_drawdown": -0.14
        }
    },
    {
        "id": "template-osc-kdj",
        "name": "KDJ策略 (KDJ Strategy)",
        "category": StrategyCategory.OSCILLATION,
        "description": "使用KDJ指标的K线和D线交叉判断买卖点。K线上穿D线买入,下穿卖出。",
        "logic_flow": {
            "nodes": [
                {"id": "kdj", "type": "INDICATOR", "indicator": "KDJ", "parameters": {"n": 9, "m1": 3, "m2": 3}},
                {"id": "condition_buy", "type": "CONDITION", "condition": "k > d AND k < 20"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "k < d AND k > 80"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "kdj", "to": "condition_buy"},
                {"from": "condition_buy", "to": "signal_buy"},
                {"from": "kdj", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "n_period": {"type": "int", "default": 9, "min": 5, "max": 14},
            "m1_period": {"type": "int", "default": 3, "min": 2, "max": 5},
            "m2_period": {"type": "int", "default": 3, "min": 2, "max": 5}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.25,
            "sharpe": 0.95,
            "max_drawdown": -0.16
        }
    },

    # ========================================
    # MULTI_FACTOR Strategies
    # ========================================
    {
        "id": "template-multi-value",
        "name": "价值因子策略 (Value Factor)",
        "category": StrategyCategory.MULTI_FACTOR,
        "description": "基于市盈率、市净率等价值因子选股。选择低估值股票买入并持有。",
        "logic_flow": {
            "nodes": [
                {"id": "pe", "type": "INDICATOR", "indicator": "PE_RATIO"},
                {"id": "pb", "type": "INDICATOR", "indicator": "PB_RATIO"},
                {"id": "condition_value", "type": "CONDITION", "condition": "pe < 15 AND pb < 2"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "pe > 25 OR pb > 3"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "pe", "to": "condition_value"},
                {"from": "pb", "to": "condition_value"},
                {"from": "condition_value", "to": "signal_buy"},
                {"from": "pe", "to": "condition_sell"},
                {"from": "pb", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "pe_threshold_low": {"type": "number", "default": 15, "min": 10, "max": 25},
            "pb_threshold_low": {"type": "number", "default": 2, "min": 1, "max": 3},
            "rebalance_days": {"type": "int", "default": 30, "min": 7, "max": 90}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.32,
            "sharpe": 1.05,
            "max_drawdown": -0.17
        }
    },
    {
        "id": "template-multi-quality-momentum",
        "name": "质量-动量组合策略 (Quality-Momentum)",
        "category": StrategyCategory.MULTI_FACTOR,
        "description": "结合质量因子(ROE)和动量因子(过去20日涨幅)选股。选择高质量且有动量的股票。",
        "logic_flow": {
            "nodes": [
                {"id": "roe", "type": "INDICATOR", "indicator": "ROE"},
                {"id": "momentum_20d", "type": "INDICATOR", "indicator": "MOMENTUM", "parameters": {"period": 20}},
                {"id": "condition_quality", "type": "CONDITION", "condition": "roe > 0.15"},
                {"id": "condition_momentum", "type": "CONDITION", "condition": "momentum_20d > 0.05"},
                {"id": "condition_buy", "type": "CONDITION", "condition": "quality AND momentum"},
                {"id": "signal_buy", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "condition_sell", "type": "CONDITION", "condition": "momentum_20d < -0.05"},
                {"id": "signal_sell", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "roe", "to": "condition_quality"},
                {"from": "momentum_20d", "to": "condition_momentum"},
                {"from": "condition_quality", "to": "condition_buy"},
                {"from": "condition_momentum", "to": "condition_buy"},
                {"from": "condition_buy", "to": "signal_buy"},
                {"from": "momentum_20d", "to": "condition_sell"},
                {"from": "condition_sell", "to": "signal_sell"}
            ]
        },
        "parameters": {
            "roe_threshold": {"type": "number", "default": 0.15, "min": 0.10, "max": 0.25},
            "momentum_period": {"type": "int", "default": 20, "min": 10, "max": 60},
            "momentum_threshold": {"type": "number", "default": 0.05, "min": 0.02, "max": 0.10}
        },
        "is_system_template": True,
        "backtest_example": {
            "period": "2021-01-01 to 2023-12-31",
            "return": 0.45,
            "sharpe": 1.4,
            "max_drawdown": -0.19
        }
    }
]


async def seed_strategy_templates(db: AsyncSession) -> None:
    """
    Seed built-in strategy templates

    Args:
        db: Database session
    """
    logger.info("Seeding strategy templates...")

    for template_data in STRATEGY_TEMPLATES:
        # Check if template already exists
        existing = await db.get(StrategyTemplate, template_data["id"])

        if existing:
            logger.debug(f"Template {template_data['id']} already exists, skipping")
            continue

        # Create new template
        template = StrategyTemplate(**template_data)
        db.add(template)
        logger.debug(f"Created template: {template_data['name']}")

    await db.commit()
    logger.info(f"Successfully seeded {len(STRATEGY_TEMPLATES)} strategy templates")


# Export for use in main seed script
__all__ = ["seed_strategy_templates", "STRATEGY_TEMPLATES"]
