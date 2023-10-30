import datetime as dt
import itertools
import numpy as np
import os
import pandas as pd
import sys
from copy import deepcopy
from helpers.set_loggers import *
from module.core.Optimizer import Optimizer
from settings.general_settings import GeneralSettings
from time import time


def read_data(step):
	"""
	Reader and parser for forecasted data:
	- generation (normalized 0-1),
	- load (inflexible; normalized 0-1),
	- price for energy consumed from the retailer (€/kWh) and
	- tariff for energy sold to the retailer (€/kWh)
	:param step: data and forecast step in minutes
	:type step: int
	:return: parsed dataframe with forecasts
	:rtype: pandas.core.frame.DataFrame
	"""
	t = time()
	logger.info('Reading and parsing forecasts ... ')

	# Read data in .csv as a dataframe; read index as datetime
	dateparse = lambda x: dt.datetime.strptime(x, '%d/%m/%Y  %H:%M')
	data = pd.read_csv('input/input_data.csv', parse_dates=['date'], index_col='date', decimal=',', sep=';',
	                   date_parser=dateparse)
	data.index.rename('datetime', inplace=True)

	# Fix lacking market and feed-in values
	data['market'].replace(to_replace=0, method='ffill', inplace=True)
	data['feedin'].replace(to_replace=0, method='ffill', inplace=True)

	# Scale data by nominal values of the configured assets
	data['pv'] *= GeneralSettings.scale_pv  # PV nominal power in kW - generation set points now in kWh
	data['load'] *= GeneralSettings.scale_load  # Load nominal power in kW - load set points now in kWh

	# Resample data to step
	# To up-sample (H -> min) a last row must be included with the last index hour + 1
	# e.g. when upsampling from [01/01/2022 00:00, 01/01/2022 23:00] to a 15' step, [02/01/2022 00:00]
	# must be added so that the resample does not end at [01/01/2022 23:00] but at [01/01/2022 23:45]
	idx_freq = pd.infer_freq(data.index)
	new_entry_idx = data.index[-1] + pd.Timedelta(1, unit=idx_freq)
	data.loc[new_entry_idx, :] = data.loc[data.index[-1]]
	data = data.resample(f'{step}T').ffill()
	data = data.iloc[:-1]

	logger.info(f'Reading and parsing forecasts ... OK! ({time()-t:.3f}s)')

	return data


def optimize(_settings, _assets, _assets2, _milp_params, _measures, _measures2, _forecasts):
	"""
	Main optimization orchestrator.
	:param _settings:
	:param _assets:
	:param _assets2:
	:param _milp_params:
	:param _measures:
	:param _measures2:
	:param _forecasts:

	:return:
	"""
	config_t = time()
	logger.info(f'Configuring data for MILP...')
	problem = Optimizer(plot=GeneralSettings.plot, solver='CBC')
	problem.initialize(_settings, _assets, _assets2, _milp_params, _measures, _measures2, _forecasts)
	logger.info(f'Configuring data for MILP ... OK! ({time() - config_t:.3f}s)')

	solve_t = time()
	logger.info(f'Solving MILP ...')
	problem.solve_milp()
	logger.info(f'Solving MILP ... OK! ({time() - solve_t:.3f}s)')

	outputs_t = time()
	logger.info(f'Generating outputs ...')
	problem.generate_outputs()
	logger.info(f'Generating outputs ... OK! ({time() - outputs_t:.3f}s)')

	return problem


if __name__ == '__main__':
	# Set paths
	ROOT_PATH = os.path.abspath(os.path.join(__file__, '..'))
	JSON_PATH = os.path.join(ROOT_PATH, 'json')
	HELPERS_PATH = os.path.join(ROOT_PATH, 'helpers')

	# Set loggers
	set_stdout_logger()
	logfile_handler_id = set_logfile_handler()

	# Read and scale data
	data_df = read_data(GeneralSettings.step)

	# Iterate over each day requested
	first_day = data_df.index[0]
	total_iter = len(GeneralSettings.all_days)
	iteration = 0

	# Create a variable to store the setpoints
	daily_outputs = None
	# Create a variable to store the main results
	final_outputs = None



	"""final_outputs ={
		'datetime': [],
		'status': [],
		'status_real': [],
		'expected_revenues': [],
		'degradation': [],
		'degradation2': [],
		'last_soc': [],
		'time': [],
	}"""

	expected_revenues = 0
	last_soc = 0
	last_soc2 = 0
	degradation = 0
	degradation2 = 0
	total_degradation = 0
	total = 0
	first_dt_text = 0

	for day in GeneralSettings.all_days:
		# Log the current iteration
		iteration += 1
		iter_time = time()
		logger.info(f' * Day {iteration} of {total_iter} ... * ')

		# Truncate data to present day
		first_dt = first_day + dt.timedelta(days=day)
		last_dt = first_dt + dt.timedelta(hours=GeneralSettings.horizon) - dt.timedelta(minutes=GeneralSettings.step)
		df = data_df.loc[first_dt:last_dt, :].copy()

		# Updates between runs
		if iteration == 1:
			degraded = 0
			degraded2 = 0
			init = first_dt
			soc = GeneralSettings.bess_initial_soc
			soc2 = GeneralSettings.bess_initial_soc2
		else:
			degraded += degradation
			degraded2 += degradation2
			init += dt.timedelta(days=1)
			last_soc /= (GeneralSettings.bess_e_nom - degraded) * 100
			last_soc2 /= (GeneralSettings.bess_e_nom2 - degraded2) * 100
			soc = last_soc
			soc2 = last_soc2

		before_init = init - dt.timedelta(hours=1)

		# Preparing inputs for optimization (format is API-friendly)
		settings = {
			'pccLimitValue': GeneralSettings.pcc_limit_value,
			'addOnInv': GeneralSettings.add_on_inv,
			'addOnSoc': GeneralSettings.add_on_soc,
		}

		original_test_data = deepcopy(GeneralSettings.bess_test_data)
		original_test_data2 = deepcopy(GeneralSettings.bess_test_data2)

		bess_asset = {
			'actualENom': GeneralSettings.bess_e_nom - degraded,
			'chEff': GeneralSettings.bess_ch_eff,
			'degCurve': GeneralSettings.bess_deg_curve,
			'dischEff': GeneralSettings.bess_disch_eff,
			'eNom': GeneralSettings.bess_e_nom,
			'eolCriterion': GeneralSettings.bess_eol_criterion,
			'invMaxIDC': GeneralSettings.bess_inv_max_idc,
			'invSNom': GeneralSettings.bess_inv_s_nom,
			'invVNom': GeneralSettings.bess_inv_v_nom,
			'maxCCh': GeneralSettings.bess_max_c_ch,
			'maxCDch': GeneralSettings.bess_max_c_disch,
			'maxSoc': GeneralSettings.bess_max_soc,
			'minPCh': GeneralSettings.bess_min_p_ch,
			'minPDch': GeneralSettings.bess_min_p_disch,
			'minSoc': GeneralSettings.bess_min_soc,
			'reserveSoc': GeneralSettings.bess_reserve_soc,
			'testData': original_test_data,
			'vNom': GeneralSettings.bess_v_nom,
		}

		bess_asset2 = {
			'actualENom': GeneralSettings.bess_e_nom2 - degraded2,
			'chEff': GeneralSettings.bess_ch_eff2,
			'degCurve': GeneralSettings.bess_deg_curve2,
			'dischEff': GeneralSettings.bess_disch_eff2,
			'eNom': GeneralSettings.bess_e_nom2,
			'eolCriterion': GeneralSettings.bess_eol_criterion2,
			'invMaxIDC': GeneralSettings.bess_inv_max_idc2,
			'invSNom': GeneralSettings.bess_inv_s_nom2,
			'invVNom': GeneralSettings.bess_inv_v_nom2,
			'maxCCh': GeneralSettings.bess_max_c_ch2,
			'maxCDch': GeneralSettings.bess_max_c_disch2,
			'maxSoc': GeneralSettings.bess_max_soc2,
			'minPCh': GeneralSettings.bess_min_p_ch2,
			'minPDch': GeneralSettings.bess_min_p_disch2,
			'minSoc': GeneralSettings.bess_min_soc2,
			'reserveSoc': GeneralSettings.bess_reserve_soc2,
			'testData': original_test_data2,
			'vNom': GeneralSettings.bess_v_nom2,
		}



		milp_params = {
			'mipgap': GeneralSettings.mipgap,
			'timeout': GeneralSettings.timeout,
			'init': init,
			'horizon': GeneralSettings.horizon,
			'step': GeneralSettings.step,
		}

		measures = {
			'bessSoC':  soc,
		}

		measures2 = {
			'bessSoC': soc2,
		}

		forecasts_and_other_arrays = {
			'pvForecasts': df['pv'].values,
			'loadForecasts': df['load'].values,
			'marketPrices': df['market'].values,
			'feedinTariffs': df['feedin'].values,
		}

		# Run optimization
		t0 = time()
		prob_obj = optimize(settings, bess_asset, bess_asset2, milp_params, measures, measures2, forecasts_and_other_arrays)
		t1 = time() - t0

		# Get the needed outputs
		outputs = prob_obj.outputs

		outputs.pop('milpStatus')

		# -- get a single dataframe from all outputs
		col_names = outputs.keys()
		for i, col in enumerate(col_names):
			aux_df = pd.DataFrame(outputs[col])
			aux_df.columns = ['datetime', col]
			aux_df.set_index('datetime', inplace=True)
			df = aux_df if i == 0 else df.join(aux_df)

		# -- if first day, create df, else append to existing df
		if daily_outputs is not None:
			daily_outputs = daily_outputs.append(df)
		else:
			daily_outputs = df

		status = prob_obj.stat
		logger.warning(f'{status}')


		expected_revenues += pd.DataFrame(outputs.get('expectRevs')).sum().get('setpoint')
		last_soc += pd.DataFrame(outputs['eBess']).loc[prob_obj.time_intervals-1, 'setpoint']
		last_soc2 += pd.DataFrame(outputs['eBess2']).loc[prob_obj.time_intervals - 1, 'setpoint']
		degradation += pd.DataFrame(outputs['eDeg']).sum().get('setpoint')
		degradation2 += pd.DataFrame(outputs['eDeg2']).sum().get('setpoint')
		total_degradation += pd.DataFrame(outputs.get('Totaldeg')).sum().get('setpoint')
		total += pd.DataFrame(outputs.get('Total')).sum().get('setpoint')
		first_dt_text = dt.datetime.strftime(first_dt, '%Y-%m-%d %H:%M:%S')



		with open(f'{prob_obj.common_fname}-pulp.sol', newline='\n') as csvfile:
			init_text = csvfile.read(50)
			status_real = init_text.split(sep=' - ')[0]

		# Clean unnecessary files from "core" folder
		prob_obj.final_folder_cleaning()

		# Create a final outputs JSON (for future API purposes)
		final_outputs = {
			'datetime': [],
			'status': [],
			'status_real': [],
			'expected_revenues': [],
			'degradation': [],
			'degradation2': [],
			'total_degradation': [],
			'total': [],
			'last_soc': [],
			'time': [],
		}

		final_outputs['datetime'].append(first_dt_text)
		final_outputs['status'].append(status)
		final_outputs['status_real'].append(status_real)
		final_outputs['expected_revenues'].append(expected_revenues)
		final_outputs['degradation'].append(degradation)
		final_outputs['degradation2'].append(degradation2)
		final_outputs['total_degradation'].append(total_degradation)
		final_outputs['total'].append(total)
		final_outputs['last_soc'].append(last_soc)
		final_outputs['time'].append(t1)

		logger.info(f' * Day {iteration} of {total_iter} ... OK! ({iter_time-time():.3f}s) * ')

	daily_outputs.to_csv(rf'outputs/{prob_obj.common_fname}_setpoints.csv',
	                     sep=';', decimal=',', index=True)
	pd.DataFrame(final_outputs).to_csv(rf'outputs/{prob_obj.common_fname}_main_outputs.csv',
	                                   sep=';', decimal=',', index=True)

	# Remove the log file handler
	remove_logfile_handler(logfile_handler_id)
