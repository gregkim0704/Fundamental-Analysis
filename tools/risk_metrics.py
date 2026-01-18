"""Risk metrics calculation tools."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import yfinance as yf
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RiskMetricsInput(BaseModel):
    """Input for risk metrics tool."""
    ticker: str = Field(..., description="Stock ticker")
    lookback_days: int = Field(default=252, description="Days to look back (252 = 1 year)")
    confidence_level: float = Field(default=0.95, description="VaR confidence level")


@tool(args_schema=RiskMetricsInput)
def calculate_risk_metrics(
    ticker: str,
    lookback_days: int = 252,
    confidence_level: float = 0.95,
) -> dict[str, Any]:
    """Calculate risk metrics including volatility, VaR, max drawdown.

    Args:
        ticker: Stock ticker
        lookback_days: Number of days for historical analysis
        confidence_level: Confidence level for VaR (e.g., 0.95 for 95%)

    Returns:
        Dictionary with risk metrics
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{lookback_days}d")

        if hist.empty or len(hist) < 30:
            return {"error": f"Insufficient historical data for {ticker}"}

        # Calculate daily returns
        returns = hist["Close"].pct_change().dropna()

        # Basic statistics
        mean_return = returns.mean()
        std_return = returns.std()

        # Annualized metrics
        annualized_return = mean_return * 252
        annualized_volatility = std_return * np.sqrt(252)

        # Value at Risk (Historical)
        var_percentile = 1 - confidence_level
        var_daily = np.percentile(returns, var_percentile * 100)
        var_annual = var_daily * np.sqrt(252)

        # Conditional VaR (Expected Shortfall)
        cvar_daily = returns[returns <= var_daily].mean()

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = drawdowns.min()
        max_drawdown_date = drawdowns.idxmin()

        # Sharpe Ratio (assuming risk-free rate of 4%)
        risk_free_rate = 0.04
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility != 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0

        # Beta (vs S&P 500)
        try:
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period=f"{lookback_days}d")
            spy_returns = spy_hist["Close"].pct_change().dropna()

            # Align dates
            common_dates = returns.index.intersection(spy_returns.index)
            aligned_returns = returns.loc[common_dates]
            aligned_spy = spy_returns.loc[common_dates]

            covariance = np.cov(aligned_returns, aligned_spy)[0, 1]
            spy_variance = np.var(aligned_spy)
            beta = covariance / spy_variance if spy_variance != 0 else 1
        except Exception:
            beta = None

        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        return {
            "ticker": ticker,
            "period_days": lookback_days,
            "confidence_level": confidence_level,
            "metrics": {
                "annualized_return": round(annualized_return * 100, 2),
                "annualized_volatility": round(annualized_volatility * 100, 2),
                "var_daily": round(var_daily * 100, 2),
                "var_annual": round(var_annual * 100, 2),
                "cvar_daily": round(cvar_daily * 100, 2) if cvar_daily else None,
                "max_drawdown": round(max_drawdown * 100, 2),
                "max_drawdown_date": max_drawdown_date.strftime("%Y-%m-%d") if max_drawdown_date else None,
                "sharpe_ratio": round(sharpe_ratio, 2),
                "sortino_ratio": round(sortino_ratio, 2),
                "beta": round(beta, 2) if beta else None,
                "skewness": round(skewness, 2),
                "kurtosis": round(kurtosis, 2),
            },
            "risk_assessment": {
                "volatility_level": (
                    "low" if annualized_volatility < 0.15 else
                    "moderate" if annualized_volatility < 0.30 else
                    "high" if annualized_volatility < 0.50 else
                    "very_high"
                ),
                "drawdown_severity": (
                    "minimal" if max_drawdown > -0.10 else
                    "moderate" if max_drawdown > -0.20 else
                    "significant" if max_drawdown > -0.35 else
                    "severe"
                ),
                "risk_adjusted_return": (
                    "excellent" if sharpe_ratio > 1.5 else
                    "good" if sharpe_ratio > 1.0 else
                    "fair" if sharpe_ratio > 0.5 else
                    "poor"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error calculating risk metrics for {ticker}: {e}")
        return {"error": str(e)}


class FinancialRiskInput(BaseModel):
    """Input for financial risk assessment."""
    ticker: str = Field(..., description="Stock ticker")


@tool(args_schema=FinancialRiskInput)
def assess_financial_risk(ticker: str) -> dict[str, Any]:
    """Assess financial/credit risk based on financial statements.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with financial risk assessment
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        balance = stock.balance_sheet
        income = stock.income_stmt
        cashflow = stock.cashflow

        risks = []
        risk_scores = []

        # Leverage risk
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None:
            if debt_to_equity > 200:
                risks.append({
                    "category": "leverage",
                    "severity": "high",
                    "description": f"High debt-to-equity ratio: {debt_to_equity:.1f}%"
                })
                risk_scores.append(8)
            elif debt_to_equity > 100:
                risks.append({
                    "category": "leverage",
                    "severity": "medium",
                    "description": f"Moderate debt-to-equity ratio: {debt_to_equity:.1f}%"
                })
                risk_scores.append(5)
            else:
                risk_scores.append(2)

        # Interest coverage risk
        if not income.empty and not balance.empty:
            try:
                operating_income = income.iloc[0, 0] if "Operating Income" in income.index else None
                if operating_income and operating_income in income.index:
                    operating_income = income.loc["Operating Income"].iloc[0]

                interest_expense = income.loc["Interest Expense"].iloc[0] if "Interest Expense" in income.index else None

                if operating_income and interest_expense and interest_expense != 0:
                    interest_coverage = abs(operating_income / interest_expense)
                    if interest_coverage < 1.5:
                        risks.append({
                            "category": "interest_coverage",
                            "severity": "critical",
                            "description": f"Critical interest coverage: {interest_coverage:.1f}x"
                        })
                        risk_scores.append(10)
                    elif interest_coverage < 3:
                        risks.append({
                            "category": "interest_coverage",
                            "severity": "high",
                            "description": f"Low interest coverage: {interest_coverage:.1f}x"
                        })
                        risk_scores.append(7)
                    else:
                        risk_scores.append(2)
            except Exception:
                pass

        # Liquidity risk
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")

        if current_ratio is not None:
            if current_ratio < 1:
                risks.append({
                    "category": "liquidity",
                    "severity": "high",
                    "description": f"Current ratio below 1: {current_ratio:.2f}"
                })
                risk_scores.append(8)
            elif current_ratio < 1.5:
                risks.append({
                    "category": "liquidity",
                    "severity": "medium",
                    "description": f"Low current ratio: {current_ratio:.2f}"
                })
                risk_scores.append(4)
            else:
                risk_scores.append(2)

        # Cash flow risk
        operating_cf = info.get("operatingCashflow")
        if operating_cf is not None and operating_cf < 0:
            risks.append({
                "category": "cash_flow",
                "severity": "high",
                "description": "Negative operating cash flow"
            })
            risk_scores.append(8)

        # Profitability risk
        profit_margin = info.get("profitMargins")
        if profit_margin is not None:
            if profit_margin < 0:
                risks.append({
                    "category": "profitability",
                    "severity": "high",
                    "description": "Company is unprofitable"
                })
                risk_scores.append(7)
            elif profit_margin < 0.05:
                risks.append({
                    "category": "profitability",
                    "severity": "medium",
                    "description": f"Low profit margin: {profit_margin*100:.1f}%"
                })
                risk_scores.append(4)

        # Calculate overall financial risk score
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 5

        if avg_risk_score >= 7:
            overall_level = "high"
        elif avg_risk_score >= 4:
            overall_level = "medium"
        else:
            overall_level = "low"

        return {
            "ticker": ticker,
            "financial_risks": risks,
            "risk_score": round(avg_risk_score, 1),
            "overall_risk_level": overall_level,
            "key_metrics": {
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
                "quick_ratio": quick_ratio,
                "profit_margin": profit_margin,
                "operating_cash_flow": operating_cf,
            },
        }

    except Exception as e:
        logger.error(f"Error assessing financial risk for {ticker}: {e}")
        return {"error": str(e)}


def get_comprehensive_risk_assessment(ticker: str) -> dict[str, Any]:
    """Get comprehensive risk assessment combining market and financial risks.

    Args:
        ticker: Stock ticker

    Returns:
        Dictionary with comprehensive risk assessment
    """
    # Get market risk metrics
    market_risk = calculate_risk_metrics.invoke({
        "ticker": ticker,
        "lookback_days": 252,
        "confidence_level": 0.95,
    })

    # Get financial risk assessment
    financial_risk = assess_financial_risk.invoke({"ticker": ticker})

    # Combine assessments
    risk_factors = []

    # Add market risks
    if "metrics" in market_risk:
        metrics = market_risk["metrics"]

        if metrics.get("annualized_volatility", 0) > 40:
            risk_factors.append({
                "category": "market",
                "type": "volatility",
                "severity": "high",
                "description": f"High price volatility: {metrics['annualized_volatility']}%"
            })

        if metrics.get("max_drawdown", 0) < -30:
            risk_factors.append({
                "category": "market",
                "type": "drawdown",
                "severity": "high",
                "description": f"Significant historical drawdown: {metrics['max_drawdown']}%"
            })

        if metrics.get("beta") and metrics["beta"] > 1.5:
            risk_factors.append({
                "category": "market",
                "type": "beta",
                "severity": "medium",
                "description": f"High market sensitivity (beta): {metrics['beta']}"
            })

    # Add financial risks
    if "financial_risks" in financial_risk:
        risk_factors.extend([
            {**r, "category": "financial"} for r in financial_risk["financial_risks"]
        ])

    # Determine overall risk level
    high_risks = sum(1 for r in risk_factors if r.get("severity") == "high" or r.get("severity") == "critical")
    medium_risks = sum(1 for r in risk_factors if r.get("severity") == "medium")

    if high_risks >= 2:
        overall_level = "critical"
    elif high_risks >= 1:
        overall_level = "high"
    elif medium_risks >= 2:
        overall_level = "medium"
    else:
        overall_level = "low"

    return {
        "ticker": ticker,
        "market_risk": market_risk,
        "financial_risk": financial_risk,
        "combined_risk_factors": risk_factors,
        "overall_risk_level": overall_level,
        "risk_summary": {
            "high_risk_count": high_risks,
            "medium_risk_count": medium_risks,
            "total_risk_factors": len(risk_factors),
        },
    }
