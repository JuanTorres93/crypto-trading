SELECT
	   status as "Status",
	   count(status) as "Count",
	   sum("trade result") as "Result" 
FROM control_view
WHERE
strategy_name LIKE "volume_ema_trading_strategy"
AND is_real IS TRUE
--AND exit_date LIKE '%/07/2023 %:%:%'	-- CAMBIAR ABAJO TAMBIÉN 'DD/MM/YYYY %:%:%'
GROUP BY status
UNION ALL
SELECT
	"TOTAL",
	count(status) as "Count",
	sum("trade result")
FROM control_view
WHERE 
strategy_name LIKE "volume_ema_trading_strategy"
AND is_real IS TRUE
--AND exit_date LIKE '%/07/2023 %:%:%'	-- CAMBIAR ARRIBA TAMBIÉN 'DD/MM/YYYY %:%:%'
;
