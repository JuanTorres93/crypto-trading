SELECT
	   status as "Result",
	   count(status) as "Count",
	   sum(vs_currency_result_no_fees) as "NO Commissions" ,
	   sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
FROM trade
WHERE
strategy_name IS "support_and_resistance_higher_timeframe_bullish_divergence"
AND is_real IS TRUE
--AND entry_date LIKE '02/09/2022 %:%:%'	-- CAMBIAR ABAJO TAMBIÉN 'DD/MM/YYYY %:%:%'
GROUP BY status
UNION ALL
SELECT
	"TOTAL",
	count(status) as "Count",
	sum(vs_currency_result_no_fees) as "NO Commissions",
	sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
FROM trade
WHERE 
strategy_name IS "support_and_resistance_higher_timeframe_bullish_divergence"
AND is_real IS TRUE
--AND entry_date LIKE '02/09/2022 %:%:%'	-- CAMBIAR ARRIBA TAMBIÉN 'DD/MM/YYYY %:%:%'
;
-- hasta 463 con 100 barras para divergencia
