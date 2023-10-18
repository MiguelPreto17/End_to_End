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


def read_data(table_data, step):
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

	data = pd.DataFrame(table_data)

	"""# Read data in .csv as a dataframe; read index as datetime
	dateparse = lambda x: dt.datetime.strptime(x, '%d/%m/%Y  %H:%M')
	data = pd.read_csv('input/input_data.csv', parse_dates=['date'], index_col='date', decimal=',', sep=';',
	                   date_parser=dateparse)
	data.index.rename('datetime', inplace=True)"""

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


def optimize(_settings, _assets, _assets2, _milp_params, _measures, _measures2, _forecasts, a):
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
	problem.solve_milp(a)
	logger.info(f'Solving MILP ... OK! ({time() - solve_t:.3f}s)')

	outputs_t = time()
	logger.info(f'Generating outputs ...')
	problem.generate_outputs(a)
	logger.info(f'Generating outputs ... OK! ({time() - outputs_t:.3f}s)')

	return problem

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

