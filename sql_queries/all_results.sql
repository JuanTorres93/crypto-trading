SELECT
	   status as "Result",
	   symbol,
	   count(status) as "Count",
	   sum(vs_currency_result_no_fees) as "NO Commissions" ,
	   sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
FROM trade
WHERE status IS NOT "opened"
AND strategy_name IS "support_and_resistance_higher_timeframe_bullish_divergence"
--AND id <= 463
AND id > 463
GROUP BY --symbol, 
status
UNION ALL
SELECT
	"TOTAL",
	"SYM",
	count(status) as "Count",
	sum(vs_currency_result_no_fees) as "NO Commissions",
	sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
FROM trade
WHERE status IS NOT "opened"
AND strategy_name IS "support_and_resistance_higher_timeframe_bullish_divergence"
--AND id <= 463
AND id > 463

-- hasta 463 con 100 barras para divergencia