SELECT
	   status as "Result",
	   symbol,
	   count(status) as "Count",
	   sum(vs_currency_result_no_fees) as "NO Commissions" ,
	   sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
FROM trade
WHERE status IS NOT "opened"
GROUP BY symbol, 
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