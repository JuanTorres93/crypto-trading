# DATE_QUERY = """
#         SELECT
# 	    status as "Result",
# 	    count(status) as "Count",
# 	    sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
#         FROM trade
#         WHERE
#         is_real IS TRUE
#         AND exit_date LIKE 'day/month/year %:%:%'	-- CAMBIAR ABAJO TAMBIÉN 'DD/MM/YYYY %:%:%'
#         GROUP BY status
#         UNION ALL
#         SELECT
#         	"TOTAL",
#         	count(status) as "Count",
#         	sum(vs_currency_result_no_fees) - sum(entry_fee_vs_currency) - sum(exit_fee_vs_currency) as "WITH Commissions"
#         FROM trade
#         WHERE
#         is_real IS TRUE
#         AND exit_date LIKE 'day/month/year %:%:%'	-- CAMBIAR ARRIBA TAMBIÉN 'DD/MM/YYYY %:%:%'
#         ;
# """

DATE_QUERY = """
    SELECT
    	   status as "Result",
    	   count(status) as "Count",
    	   sum("trade result")
    FROM control_view
    WHERE
    strategy_name LIKE "volume_ema_trading_strategy"
    AND is_real IS TRUE
    AND exit_date LIKE 'day/month/year %:%:%'	-- CAMBIAR ABAJO TAMBIÉN 'DD/MM/YYYY %:%:%'
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
    AND exit_date LIKE 'day/month/year %:%:%'	-- CAMBIAR ARRIBA TAMBIÉN 'DD/MM/YYYY %:%:%'
    ;
"""