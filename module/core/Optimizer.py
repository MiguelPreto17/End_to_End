import helpers.milp_helpers as mhelper
import math
import numpy as np
import pandas as pd

from module.tasks.BESS import BESS
from loguru import logger
from pulp import *
from time import asctime

seconds_in_min = 60
minutes_in_hour = 60

class Optimizer:
	def __init__(self, plot=False, solver='CBC'):
		# **************************************************************************************************************
		#         MILP PARAMETERS: PULP PARAMETERS
		# **************************************************************************************************************
		self.solv = solver  # solver chosen for the MILP
		self.mipgap = None  # controls the solvers tolerance; intolerant [0 - 1] futile
		self.timeout = None  # solvers temporal limit to find optimal solution, in seconds
		# **************************************************************************************************************
		#         MILP PARAMETERS: TIME PARAMETERS
		# **************************************************************************************************************
		self.horizon = None  # optimization horizon in hours
		self.step_in_seconds = None  # time interval of each step, in seconds
		self.step_in_min = None  # time interval of each step, in minutes
		self.step_in_hours = None  # time interval of each step, in hours
		self.time_intervals = None  # number of time intervals per horizon
		self.time_series = None  # ex.: for 1 day, range(96)
		self.start_at = None  # datetime for initial time step
		self.common_fname = f'{asctime().replace(":", "_").replace(" ", "_")}'  # files' name
		# **************************************************************************************************************
		#         MILP PARAMETERS: OTHER
		# **************************************************************************************************************
		self.milp = None  # stores the entire MILP problem (variables, objective function, restrictions and results)
		self.opt_val = None  # stores the milp numeric solution
		self.stat = None  # stores the status of the milp solution
		self.varis = None  # Dictionary to store all output variables values
		self.outputs = None  # Dictionary with the same structure as the outputs JSON that will be sent to the client
		# self.plot = plot  # If True, the results will be plotted after solving the MILP; only for test mode
		# **************************************************************************************************************
		#         SYSTEM SETTINGS
		# **************************************************************************************************************
		self.pcc_limit_value = None  # power limit that can be transacted with the grid at PCC in kW
		# **************************************************************************************************************
		#         BESS PARAMETERS
		# **************************************************************************************************************
		self.bess = None  # harbours a class with methods and parameters used for all bess in the system
		# **************************************************************************************************************
		#         FORECASTS
		# **************************************************************************************************************
		self.pv_forecasts = None  # forecasted generation, in kWh, of the PV plant
		self.load_forecasts = None  # forecasted_demand, in kWh, of the inflexible load
		# self.feedin_tariffs = None  # forecasted feed-in-tariffs in €/kWh
		self.market_prices = None  # forecasted market prices in €/kWh

	def initialize(self, settings, bess_asset, milp_params, measures, forecasts):
		"""
		Function to initialize all internal variables of the Optimizer class with the inputs from the client.
		:param settings: the system configuration settings
		:type settings: dict
		:param bess_asset: the BESS configured
		:type bess_asset: dict
		:param milp_params: the parameters set by the client for the MILP run
		:type milp_params: dict
		:param measures: the real-time measurements required for the optimization endpoint
		:type measures: dict
		:param forecasts: the forecasts required for the optimization horizon
		:type forecasts: pandas.core.frame.DataFrame
		:return: None
		:rtype: None
		"""
		# MILP parameters: PuLP parameters
		self.mipgap = milp_params.get('mipgap')
		self.timeout = milp_params.get('timeout')

		# MILP parameters: time parameters
		self.horizon = milp_params.get('horizon')
		init_dt = milp_params.get('init')
		self.step_in_min = milp_params.get('step')
		self.step_in_hours = milp_params.get('step') / minutes_in_hour
		self.step_in_seconds = self.step_in_min * seconds_in_min
		self.time_intervals = int(self.horizon/self.step_in_hours)
		self.time_series = range(self.time_intervals)
		self.start_at = pd.to_datetime(init_dt)

		# System settings
		self.pcc_limit_value = settings.get('pccLimitValue')

		# BESS parameters
		self.bess = BESS()
		self.bess.configure(bess_asset, measures.get('bessSoC'))

		# Parse forecasts
		self.pv_forecasts = forecasts.get('pvForecasts')
		self.load_forecasts = forecasts.get('loadForecasts')
		self.market_prices = forecasts.get('marketPrices')
		# self.feedin_tariffs = forecasts.get('feedinTariffs')

	def solve_milp(self):
		"""
		Function that heads the definition and solution of the optimization problem.
		:return: None
		:rtype: None
		"""
		logger.debug(' - defining MILP')
		self.milp = self.__define_milp()

		logger.debug(' - actually solving MILP')
		# noinspection PyBroadException
		try:
			self.milp.solve()
			stat = LpStatus[self.milp.status]
			opt_val = value(self.milp.objective)

		except Exception:
			logger.warning('Solver raised an error. Considering problem as "infeasible".')
			stat = 'Infeasible'
			opt_val = None

		self.stat = stat
		self.opt_val = opt_val

	def __define_milp(self):
		"""
		Method to define the generic MILP problem.
		:return: object with the milp problem ready for solving and easy access to all parameters, variables and results
		:rtype: pulp.pulp.LpProblem
		"""
		# **************************************************************************************************************
		#        ADDITIONAL PARAMETERS
		# **************************************************************************************************************
		T = self.time_series

		# **************************************************************************************************************
		#        OPTIMIZATION PROBLEM
		# **************************************************************************************************************
		self.milp = LpProblem(f'{self.common_fname}', LpMinimize)

		# **************************************************************************************************************
		#       INITIALIZE DECISION VARIABLES
		# **************************************************************************************************************
		# P absorption at the PCC (kW)
		p_abs = [LpVariable(f'p_abs_{t:03d}', lowBound=0) for t in T]
		# P injection at the PCC (kW)
		p_inj = [LpVariable(f'p_inj_{t:03d}', lowBound=0) for t in T]
		# Aux. binary variable for non simultaneity of PCC flows
		delta_pcc = [LpVariable(f'delta_pcc_{t:03d}', cat=LpBinary) for t in T]
		# Energy content of the BESS (kWh)
		e_bess = [LpVariable(f'e_bess_{t:03d}', lowBound=0) for t in T]
		# Charge P at AC-side of the BESS (kW)
		p_ch = [LpVariable(f'p_ch_{t:03d}', lowBound=0) for t in T]
		# Discharge P at AC-side of the BESS (kW)
		p_disch = [LpVariable(f'p_disch_{t:03d}', lowBound=0) for t in T]
		# Aux. binary variable for non simultaneity of BESS flows
		delta_bess = [LpVariable(f'delta_bess_{t:03d}', cat=LpBinary) for t in T]

		# **************************************************************************************************************
		#        OBJECTIVE FUNCTION
		# **************************************************************************************************************
		# Eq. (1)
		self.milp += lpSum(p_abs[t] * self.market_prices[t] for t in self.time_series) * self.step_in_hours, 'Objective Function'

		# **************************************************************************************************************
		#           CONSTRAINTS
		# **************************************************************************************************************
		for t in self.time_series:
			# Eq. (2)
			# -- define P charged - P discharged for each t
			bess_flows = p_ch[t] - p_disch[t]
			#  -- define the liquid consumption as load - generation (without bess flows)
			generation_and_demand = (self.load_forecasts[t] - self.pv_forecasts[t])
			self.milp += p_abs[t] - p_inj[t] == bess_flows + generation_and_demand, f'Equilibrium_{t:03d}'

			# Eq. (3)
			self.milp += p_abs[t] <= self.pcc_limit_value * delta_pcc[t], f'PCC_abs_limit_{t:03d}'

			# Eq. (4)
			self.milp += p_inj[t] <= self.pcc_limit_value * (1 - delta_pcc[t]), f'PCC_inj_limit_{t:03d}'

			# Eq. (5)
			self.milp += p_ch[t] <= self.bess.p_dc_max_c * delta_bess[t], f'Max_DC_charge_rate_{t:03d}'
			# Eq. (6)
			self.milp += p_disch[t] <= self.bess.p_dc_max_d * (1 - delta_bess[t]), f'Max_DC_discharge_rate_{t:03d}'

			# Update to BESS energy content
			e_bess_update = (p_ch[t] - p_disch[t]) * self.step_in_hours
			if t == 0:
				# Eq. (7)
				self.milp += e_bess[t] == self.bess.initial_e_bess + e_bess_update, f'Initial_E_update_{t:03d}'
			else:
				# Eq. (8)
				self.milp += e_bess[t] == e_bess[t - 1] + e_bess_update, f'E_update_{t:03d}'

			# Eq. (9 left-side)
			self.milp += self.bess.min_e_bess <= e_bess[t], f'E_content_low_boundary_{t:03d}'
			# Eq. (9 right-side)
			self.milp += e_bess[t] <= self.bess.max_e_bess, f'E_content_high_boundary_{t:03d}'

		# **************************************************************************************************************

		dir_name = os.path.abspath(os.path.join(__file__, '..'))
		lp_name = os.path.join(dir_name, f'{self.common_fname}.lp')
		self.milp.writeLP(lp_name)

		# The problem is solved using PuLP's choice of Solver
		if self.solv == 'CBC':
			self.milp.setSolver(pulp.PULP_CBC_CMD(msg=False, timeLimit=self.timeout, gapRel=self.mipgap, keepFiles=True))

		elif self.solv == 'GUROBI':
			self.milp.setSolver(GUROBI_CMD(msg=False, timeLimit=self.timeout, mip=self.mipgap))

		return self.milp

	def generate_outputs(self):
		"""
		Function for generating the outputs of optimization, namely the set points for each asset and all relevant
		variables, and to convert them into JSON format.
		:return: None
		:rtype: None
		"""
		if self.opt_val is None:
			# To avoid raising error whenever encountering the puLP solver error with CBC
			self.outputs = {}
		else:
			self.__get_variables_values()
			self.__initialize_and_populate_outputs()

		# # Generate the outputs JSON file
		# master_path = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
		# structures_path = os.path.join('json', 'outputs.json')
		# output_path = os.path.join(master_path, structures_path)
		# with open(output_path, 'w') as outfile:
		# 	json.dump(self.outputs, outfile)

		# if self.plot:
		# 	from graphics.plot_results import plot_results
		# 	plot_results(self)

	def __get_variables_values(self):
		"""
		Function for retrieving and storing the values of each decision variable into a dictionary.
		:return: None
		:rtype: None
		"""
		# **************************************************************************************************************
		#        INITIALIZE DECISION VARIABLES
		# **************************************************************************************************************
		self.varis = dict()

		# P absorption at the PCC (kW)
		self.varis['p_abs'] = list(np.full(self.time_intervals, np.nan))
		# P injection at the PCC (kW)
		self.varis['p_inj'] = list(np.full(self.time_intervals, np.nan))
		# Aux. binary variable for non simultaneity of PCC flows
		self.varis['delta_pcc'] = list(np.full(self.time_intervals, np.nan))
		# Energy content of the BESS (kWh)
		self.varis['e_bess'] = list(np.full(self.time_intervals, np.nan))
		# Charge P at AC-side of the BESS (kW)
		self.varis['p_ch'] = list(np.full(self.time_intervals, np.nan))
		# Discharge P at AC-side of the BESS (kW)
		self.varis['p_disch'] = list(np.full(self.time_intervals, np.nan))
		# Aux. binary variable for non simultaneity of BESS flows
		self.varis['delta_bess'] = list(np.full(self.time_intervals, np.nan))

		# **************************************************************************************************************
		#        FILL DECISION VARIABLES
		# **************************************************************************************************************
		for v in self.milp.variables():
			if not re.search('dummy', v.name):
				t = int(v.name[-3:])

			if re.search('p_abs_', v.name):
				self.varis['p_abs'][t] = v.varValue

			elif re.search('p_inj_', v.name):
				self.varis['p_inj'][t] = v.varValue

			elif re.search('delta_pcc_', v.name):
				self.varis['delta_pcc'][t] = v.varValue

			elif re.search(f'e_bess_', v.name):
				self.varis['e_bess'][t] = v.varValue

			elif re.search(f'e_deg_', v.name):
				self.varis['e_deg'][t] = v.varValue

			elif re.search(f'p_ch_', v.name):
				self.varis['p_ch'][t] = v.varValue

			elif re.search(f'p_disch_', v.name):
				self.varis['p_disch'][t] = v.varValue

			elif re.search(f'delta_bess_', v.name):
				self.varis['delta_bess'][t] = v.varValue

	def __initialize_and_populate_outputs(self):
		"""
		Initializes and populates the outputs' structure as a dictionary matching the outputs JSON format.
		:return: None
		:rtype: None
		"""

		p_ch = self.varis.get('p_ch')
		p_disch = self.varis.get('p_disch')

		# Create a list of the set points' datetime corresponding values, as strings, in ISO 8601 format
		list_of_dates = mhelper.create_strftime_list(self.horizon, self.step_in_hours, self.start_at)

		# Calculate the expected revenues
		pcc_absorption = np.array(self.varis.get('p_abs'))
		pcc_injection = np.array(self.varis.get('p_inj'))
		of = (pcc_absorption * self.market_prices) * self.step_in_hours

		# Initialize outputs as a dictionary
		self.outputs = dict(
			milpStatus=self.milp.status,
			pCharge=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, p_ch)],
			pDischarge=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, p_disch)],
			eBess=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('e_bess'))],
			pAbs=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('p_abs'))],
			pInj=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('p_inj'))],
			expectRevs=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, of)]
		)

	@staticmethod
	def final_folder_cleaning():
		"""
		Cleans the directory of optimization byproducts by deleting the files with the specified extensions.
		:return: None
		:rtype: None
		"""

		dir_name = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
		test = os.listdir(dir_name)
		for item in test:
			if item.endswith((".mps", ".sol")):
				os.remove(os.path.join(dir_name, item))

		dir_name = os.path.abspath(os.path.join(__file__, '..'))
		test = os.listdir(dir_name)
		for item in test:
			if item.endswith((".lp")):
				os.remove(os.path.join(dir_name, item))
		pass
