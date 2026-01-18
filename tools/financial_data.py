"""Financial statements data tools."""
import logging
from typing import Any, Optional

import yfinance as yf
import pandas as pd
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _clean_financial_data(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert financial DataFrame to list of dictionaries.

    Args:
        df: DataFrame with financial data

    Returns:
        List of dictionaries with financial data by period
    """
    if df.empty:
        return []

    records = []
    for col in df.columns:
        period_data = {"period": col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)}
        for idx in df.index:
            value = df.loc[idx, col]
            if pd.notna(value):
                # Convert to float and format large numbers
                if isinstance(value, (int, float)):
                    period_data[str(idx)] = float(value)
                else:
                    period_data[str(idx)] = value
        records.append(period_data)

    return records


class FinancialStatementsInput(BaseModel):
    """Input for financial statements tool."""
    ticker: str = Field(..., description="Stock ticker symbol")
    period: str = Field(
        default="annual",
        description="Period type: 'annual' or 'quarterly'"
    )


@tool(args_schema=FinancialStatementsInput)
def get_financial_statements(ticker: str, period: str = "annual") -> dict[str, Any]:
    """Get all financial statements (income, balance sheet, cash flow) for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Period type ('annual' or 'quarterly')

    Returns:
        Dictionary with all financial statements
    """
    try:
        stock = yf.Ticker(ticker)

        if period == "quarterly":
            income = stock.quarterly_income_stmt
            balance = stock.quarterly_balance_sheet
            cashflow = stock.quarterly_cashflow
        else:
            income = stock.income_stmt
            balance = stock.balance_sheet
            cashflow = stock.cashflow

        return {
            "ticker": ticker,
            "period_type": period,
            "income_statement": _clean_financial_data(income),
            "balance_sheet": _clean_financial_data(balance),
            "cash_flow": _clean_financial_data(cashflow),
        }

    except Exception as e:
        logger.error(f"Error fetching financial statements for {ticker}: {e}")
        return {"error": str(e)}


@tool(args_schema=FinancialStatementsInput)
def get_income_statement(ticker: str, period: str = "annual") -> dict[str, Any]:
    """Get income statement for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Period type ('annual' or 'quarterly')

    Returns:
        Dictionary with income statement data
    """
    try:
        stock = yf.Ticker(ticker)

        if period == "quarterly":
            df = stock.quarterly_income_stmt
        else:
            df = stock.income_stmt

        if df.empty:
            return {"error": f"No income statement data found for {ticker}"}

        return {
            "ticker": ticker,
            "period_type": period,
            "data": _clean_financial_data(df),
        }

    except Exception as e:
        logger.error(f"Error fetching income statement for {ticker}: {e}")
        return {"error": str(e)}


@tool(args_schema=FinancialStatementsInput)
def get_balance_sheet(ticker: str, period: str = "annual") -> dict[str, Any]:
    """Get balance sheet for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Period type ('annual' or 'quarterly')

    Returns:
        Dictionary with balance sheet data
    """
    try:
        stock = yf.Ticker(ticker)

        if period == "quarterly":
            df = stock.quarterly_balance_sheet
        else:
            df = stock.balance_sheet

        if df.empty:
            return {"error": f"No balance sheet data found for {ticker}"}

        return {
            "ticker": ticker,
            "period_type": period,
            "data": _clean_financial_data(df),
        }

    except Exception as e:
        logger.error(f"Error fetching balance sheet for {ticker}: {e}")
        return {"error": str(e)}


@tool(args_schema=FinancialStatementsInput)
def get_cash_flow(ticker: str, period: str = "annual") -> dict[str, Any]:
    """Get cash flow statement for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Period type ('annual' or 'quarterly')

    Returns:
        Dictionary with cash flow data
    """
    try:
        stock = yf.Ticker(ticker)

        if period == "quarterly":
            df = stock.quarterly_cashflow
        else:
            df = stock.cashflow

        if df.empty:
            return {"error": f"No cash flow data found for {ticker}"}

        return {
            "ticker": ticker,
            "period_type": period,
            "data": _clean_financial_data(df),
        }

    except Exception as e:
        logger.error(f"Error fetching cash flow for {ticker}: {e}")
        return {"error": str(e)}


def get_financial_metrics(ticker: str) -> dict[str, Any]:
    """Calculate key financial metrics from statements (non-tool function).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with calculated metrics
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get statements
        income = stock.income_stmt
        balance = stock.balance_sheet
        cashflow = stock.cashflow

        metrics = {
            "ticker": ticker,
            "currency": info.get("currency", "USD"),
        }

        # Profitability metrics
        if not income.empty and income.shape[1] > 0:
            latest = income.iloc[:, 0]

            revenue = latest.get("Total Revenue")
            gross_profit = latest.get("Gross Profit")
            operating_income = latest.get("Operating Income")
            net_income = latest.get("Net Income")
            ebitda = latest.get("EBITDA")

            if revenue and revenue != 0:
                metrics["gross_margin"] = (gross_profit / revenue * 100) if gross_profit else None
                metrics["operating_margin"] = (operating_income / revenue * 100) if operating_income else None
                metrics["net_margin"] = (net_income / revenue * 100) if net_income else None
                metrics["ebitda_margin"] = (ebitda / revenue * 100) if ebitda else None

            metrics["revenue"] = revenue
            metrics["operating_income"] = operating_income
            metrics["net_income"] = net_income
            metrics["ebitda"] = ebitda

        # Balance sheet metrics
        if not balance.empty and balance.shape[1] > 0:
            latest = balance.iloc[:, 0]

            total_assets = latest.get("Total Assets")
            total_liabilities = latest.get("Total Liabilities Net Minority Interest")
            total_equity = latest.get("Total Equity Gross Minority Interest") or latest.get("Stockholders Equity")
            total_debt = latest.get("Total Debt")
            cash = latest.get("Cash And Cash Equivalents")

            metrics["total_assets"] = total_assets
            metrics["total_liabilities"] = total_liabilities
            metrics["total_equity"] = total_equity
            metrics["total_debt"] = total_debt
            metrics["cash"] = cash

            if total_equity and total_equity != 0:
                metrics["debt_to_equity"] = (total_debt / total_equity) if total_debt else None

            if total_debt and cash:
                metrics["net_debt"] = total_debt - cash

        # Cash flow metrics
        if not cashflow.empty and cashflow.shape[1] > 0:
            latest = cashflow.iloc[:, 0]

            operating_cf = latest.get("Operating Cash Flow")
            capex = latest.get("Capital Expenditure")
            fcf = latest.get("Free Cash Flow")

            metrics["operating_cash_flow"] = operating_cf
            metrics["capital_expenditure"] = capex
            metrics["free_cash_flow"] = fcf if fcf else (operating_cf + capex if operating_cf and capex else None)

            # Cash flow quality
            if operating_cf and operating_income and operating_income != 0:
                metrics["ocf_to_operating_income"] = operating_cf / operating_income

        # Return metrics from info
        metrics["roe"] = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None
        metrics["roa"] = info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None

        return metrics

    except Exception as e:
        logger.error(f"Error calculating financial metrics for {ticker}: {e}")
        return {"error": str(e)}


def get_multi_year_financials(ticker: str, years: int = 5) -> dict[str, Any]:
    """Get multi-year financial data for trend analysis.

    Args:
        ticker: Stock ticker symbol
        years: Number of years of data

    Returns:
        Dictionary with multi-year financial data
    """
    try:
        stock = yf.Ticker(ticker)

        income = stock.income_stmt
        balance = stock.balance_sheet
        cashflow = stock.cashflow

        # Build time series data
        time_series = []

        for i, col in enumerate(income.columns[:years]):
            year_data = {
                "year": col.strftime("%Y") if hasattr(col, "strftime") else str(col),
            }

            # Income statement items
            if not income.empty:
                year_data["revenue"] = income.loc["Total Revenue", col] if "Total Revenue" in income.index else None
                year_data["operating_income"] = income.loc["Operating Income", col] if "Operating Income" in income.index else None
                year_data["net_income"] = income.loc["Net Income", col] if "Net Income" in income.index else None

            # Balance sheet items (may have different dates)
            if not balance.empty and i < len(balance.columns):
                bcol = balance.columns[i]
                year_data["total_assets"] = balance.loc["Total Assets", bcol] if "Total Assets" in balance.index else None
                year_data["total_equity"] = balance.loc["Stockholders Equity", bcol] if "Stockholders Equity" in balance.index else None
                year_data["total_debt"] = balance.loc["Total Debt", bcol] if "Total Debt" in balance.index else None

            # Cash flow items
            if not cashflow.empty and i < len(cashflow.columns):
                ccol = cashflow.columns[i]
                year_data["operating_cf"] = cashflow.loc["Operating Cash Flow", ccol] if "Operating Cash Flow" in cashflow.index else None
                year_data["capex"] = cashflow.loc["Capital Expenditure", ccol] if "Capital Expenditure" in cashflow.index else None
                year_data["fcf"] = cashflow.loc["Free Cash Flow", ccol] if "Free Cash Flow" in cashflow.index else None

            time_series.append(year_data)

        return {
            "ticker": ticker,
            "years": years,
            "data": time_series,
        }

    except Exception as e:
        logger.error(f"Error fetching multi-year financials for {ticker}: {e}")
        return {"error": str(e)}
