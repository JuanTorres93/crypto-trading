CREATE VIEW IF NOT EXISTS control_view AS
    SELECT
		id,
		symbol as "sym",
		vs_currency_symbol as "vs_s",
		entry_date,
		exit_date,
		COALESCE('(\/) ' || modified_take_profit || ' (\/)', take_profit) as "take profit",
		entry_price as "entry price",
		COALESCE('(/\) ' || modified_stop_loss || ' (/\)', stop_loss) as "stop loss",
		CASE
			WHEN entry_price = modified_stop_loss AND (vs_currency_result_no_fees - entry_fee_vs_currency - exit_fee_vs_currency) < 0.1 THEN 'break even'
			ELSE status
		END as "status",
		vs_currency_result_no_fees - entry_fee_vs_currency - exit_fee_vs_currency AS "trade result",
		COALESCE(crypto_quantity_exit, crypto_quantity_entry) * (take_profit - entry_price) - entry_fee_vs_currency - COALESCE(exit_fee_vs_currency, entry_fee_vs_currency) AS "trade if win COM",
		COALESCE(crypto_quantity_exit, crypto_quantity_entry) * (stop_loss - entry_price) - entry_fee_vs_currency - COALESCE(exit_fee_vs_currency, entry_fee_vs_currency) AS "trade if lose COM",
		100 * abs(entry_price - stop_loss) / entry_price AS "risked percentage",
		abs(take_profit - entry_price) / abs(entry_price - stop_loss) AS "RRR NO com",
		(COALESCE(crypto_quantity_exit, crypto_quantity_entry) * (take_profit - entry_price) - entry_fee_vs_currency - exit_fee_vs_currency) / -(COALESCE(crypto_quantity_exit, crypto_quantity_entry) * (stop_loss - entry_price) - entry_fee_vs_currency - exit_fee_vs_currency) AS "RRR COM",
		COALESCE(crypto_quantity_exit, crypto_quantity_entry) * entry_price AS "money on entry",
		strategy_name,
		is_real
	FROM trade
	ORDER BY id DESC
