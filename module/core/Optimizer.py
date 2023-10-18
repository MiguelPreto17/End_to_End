import helpers.milp_helpers as mhelper
import math
import numpy as np
import pandas as pd

from module.tasks.BESS import BESS
from loguru import logger
from pulp import *
from time import asctime
from settings.general_settings import GeneralSettings


seconds_in_min = 60
minutes_in_hour = 60
k1 = GeneralSettings.k1
k2 = GeneralSettings.k2
C1 = GeneralSettings.C1
C2 = GeneralSettings.C2

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
		#self.step_in_days = None
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
		self.plot = plot  # If True, the results will be plotted after solving the MILP; only for test mode
		# **************************************************************************************************************
		#         SYSTEM SETTINGS
		# **************************************************************************************************************
		self.pcc_limit_value = None  # power limit that can be transacted with the grid at PCC in kW
		self.add_on_inv = None  # activate add-on to calculate piecewise inverters' efficiencies' segments?
		self.seg_series = range(2)  # iterator over the number of segments considered (hardcoded to 2)
		self.add_on_soc = None  # activate add-on that considers the more realistic battery characteristics?
		# **************************************************************************************************************
		#         BESS PARAMETERS
		# **************************************************************************************************************
		self.bess = None  # harbours a class with methods and parameters used for all bess in the system
		self.bess2 = None  # harbours a class with methods and parameters used for all bess in the system
		# **************************************************************************************************************
		#         FORECASTS
		# **************************************************************************************************************
		self.pv_forecasts = None  # forecasted generation, in kWh, of the PV plant
		self.load_forecasts = None  # forecasted_demand, in kWh, of the inflexible load
		self.feedin_tariffs = None  # forecasted feed-in-tariffs in €/kWh
		self.market_prices = None  # forecasted market prices in €/kWh

	def initialize(self, settings, bess_asset, bess_asset2, milp_params, measures, measures2, forecasts):
		"""
		Function to initialize all internal variables of the Optimizer class with the inputs from the client.
		:param measures2: the real-time measurements required for the optimization endpoint
		:type measures2: dict
		:param bess_asset2: the BESS configured
		:type bess_asset2: dict
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
		#self.step_in_days = milp_params.get('step') / hours_in_day
		self.step_in_seconds = self.step_in_min * seconds_in_min
		self.time_intervals = int(self.horizon/self.step_in_hours)
		self.time_series = range(self.time_intervals)
		#self.teste = range(self.step_in_days)
		self.start_at = pd.to_datetime(init_dt)

		# System settings
		self.pcc_limit_value = settings.get('pccLimitValue')
		self.add_on_soc = settings['addOnSoc']
		self.add_on_inv = settings['addOnInv']

		# BESS parameters
		self.bess = BESS()
		self.bess2 = BESS()
		subset_add_ons = {add_on: settings[add_on] for add_on in ('addOnSoc', 'addOnInv')}
		subset_add_ons['addOnDeg'] = False
		self.bess.configure(bess_asset, measures.get('bessSoC'), subset_add_ons)
		self.bess2.configure(bess_asset2, measures2.get('bessSoC'), subset_add_ons)


		# Parse forecasts
		self.pv_forecasts = forecasts.get('pvForecasts')
		self.load_forecasts = forecasts.get('loadForecasts')
		self.market_prices = forecasts.get('marketPrices')
		self.feedin_tariffs = forecasts.get('feedinTariffs')

	def solve_milp(self, a):
		"""
		Function that heads the definition and solution of the optimization problem.
		:return: None
		:rtype: None
		"""
		logger.debug(' - defining MILP')
		self.milp = self.__define_milp(a)

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

	def __define_milp(self, a):
		"""
		Method to define the generic MILP problem.
		:return: object with the milp problem ready for solving and easy access to all parameters, variables and results
		:rtype: pulp.pulp.LpProblem
		"""
		# **************************************************************************************************************
		#        ADDITIONAL PARAMETERS
		# **************************************************************************************************************
		T = self.time_series
		S = self.seg_series
		# To calculate the dynamic energy content limits, in kWh, a linearization was generated which is dependent on
		# the charge/discharge current (kA) and not directly on the charge/discharge power (kW).
		# Being so, we create a constant here that will
		# 1) multiply the slope of the line by the charge/discharge power and
		# 2) divide that power by the nominal charge/discharge voltage in order to transform that power set point
		# into a current set point
		if self.add_on_soc:
			_dslope = self.bess.discharge_slope / self.bess.v_nom_discharge
			_cslope = self.bess.charge_slope / self.bess.v_nom_charge
			_dslope2 = self.bess2.discharge_slope / self.bess2.v_nom_discharge
			_cslope2 = self.bess2.charge_slope / self.bess2.v_nom_charge

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
		#p_inj = [LpVariable(f'p_inj_{t:03d}', lowBound=0) for t in T]
		# Aux. binary variable for non simultaneity of PCC flows
		delta_pcc = [LpVariable(f'delta_pcc_{t:03d}', cat=LpBinary) for t in T]
		# Energy content of the BESS (kWh)
		e_bess = [LpVariable(f'e_bess_{t:03d}', lowBound=0) for t in T]
		# Energy content of the BESS (kWh)
		e_bess2 = [LpVariable(f'e_bess2_{t:03d}', lowBound=0) for t in T]
		# Energy degraded per time step (kWh)
		e_deg = [LpVariable(f'e_deg_{t:03d}', lowBound=0) for t in T]
		# Energy degraded per time step (kWh)
		e_deg2 = [LpVariable(f'e_deg2_{t:03d}', lowBound=0) for t in T]
		# Max E content for p_ch set point (kWh)
		max_e_bes = [LpVariable(f'max_e_bes_{t:03d}', lowBound=0) for t in T]
		# Min E content for p_disch set point (kWh)
		min_e_bes = [LpVariable(f'min_e_bes_{t:03d}', lowBound=0) for t in T]
		# Max E content for p_ch set point (kWh)
		max_e_bes2 = [LpVariable(f'max_e_bes2_{t:03d}', lowBound=0) for t in T]
		# Min E content for p_disch set point (kWh)
		min_e_bes2 = [LpVariable(f'min_e_bes2_{t:03d}', lowBound=0) for t in T]

		if not self.add_on_inv:
			# Charge P at AC-side of the BESS (kW)
			p_ch = [LpVariable(f'p_ch_{t:03d}', lowBound=0) for t in T]
			# Discharge P at AC-side of the BESS (kW)
			p_disch = [LpVariable(f'p_disch_{t:03d}', lowBound=0) for t in T]
			# Aux. binary variable for non simultaneity of BESS flows
			delta_bess = [LpVariable(f'delta_bess_{t:03d}', cat=LpBinary) for t in T]


			# Charge P at AC-side of the BESS (kW)
			p_ch2 = [LpVariable(f'p_ch2_{t:03d}', lowBound=0) for t in T]
			# Discharge P at AC-side of the BESS (kW)
			p_disch2 = [LpVariable(f'p_disch2_{t:03d}', lowBound=0) for t in T]
			# Aux. binary variable for non simultaneity of BESS flows
			delta_bess2 = [LpVariable(f'delta_bess2_{t:03d}', cat=LpBinary) for t in T]


		else:
			# Charge P in 1st segment at DC-side of the BESS (kW)
			z_ch = [LpVariable(f'z_ch_{t:03d}', lowBound=0) for t in T]
			# Discharge P in 1st segment at DC-side of the BESS (kW)
			z_disch = [LpVariable(f'z_disch_{t:03d}', lowBound=0) for t in T]
			# Charge P at AC-side of the BESS (kW)
			p_ch = {s: [LpVariable(f'p_ch_{s}_{t:03d}', lowBound=0) for t in T] for s in S}
			# Discharge P at AC-side of the BESS (kW)
			p_disch = {s: [LpVariable(f'p_disch_{s}_{t:03d}', lowBound=0) for t in T] for s in S}
			# Aux. binary for setting the charge limits of the BESS
			delta_bess_ch = {s: [LpVariable(f'delta_bess_ch_{s}_{t:03d}', cat=LpBinary) for t in T] for s in S}
			# Aux. binary for setting the discharge limits of the BESS
			delta_bess_disch = {s: [LpVariable(f'delta_bess_disch_{s}_{t:03d}', cat=LpBinary) for t in T] for s in S}
			# Charge P at AC-side of the BESS (kW)
			e_bess = [LpVariable(f'e_bess_{t:03d}', lowBound=0) for t in T]
			# Aux. binary variable for non simultaneity of BESS flows
			delta_bess = [LpVariable(f'delta_bess_{t:03d}', cat=LpBinary) for t in T]

			# Charge P in 1st segment at DC-side of the BESS (kW)
			z_ch2 = [LpVariable(f'z_ch2_{t:03d}', lowBound=0) for t in T]
			# Discharge P in 1st segment at DC-side of the BESS (kW)
			z_disch2 = [LpVariable(f'z_disch2_{t:03d}', lowBound=0) for t in T]
			# Charge P at AC-side of the BESS (kW)
			p_ch2 = {s: [LpVariable(f'p_ch2_{s}_{t:03d}', lowBound=0) for t in T] for s in S}
			# Discharge P at AC-side of the BESS (kW)
			p_disch2 = {s: [LpVariable(f'p_disch2_{s}_{t:03d}', lowBound=0) for t in T] for s in S}
			# Aux. binary for setting the charge limits of the BESS
			delta_bess_ch2 = {s: [LpVariable(f'delta_bess_ch2_{s}_{t:03d}', cat=LpBinary) for t in T] for s in S}
			# Aux. binary for setting the discharge limits of the BESS
			delta_bess_disch2 = {s: [LpVariable(f'delta_bess_disch2_{s}_{t:03d}', cat=LpBinary) for t in T] for s in S}
			# Charge P at AC-side of the BESS (kW)
			e_bess2 = [LpVariable(f'e_bess2_{t:03d}', lowBound=0) for t in T]
			# Aux. binary variable for non simultaneity of BESS flows
			delta_bess2 = [LpVariable(f'delta_bess2_{t:03d}', cat=LpBinary) for t in T]

		# **************************************************************************************************************
		#        OBJECTIVE FUNCTION
		# **************************************************************************************************************
		# Eq. (1)
		#self.milp += lpSum(p_abs[t] * self.market_prices[t] + e_deg[t] + e_deg2[t] for t in self.time_series) * self.step_in_hours, 'Objective Function'
		#self.milp += lpSum(p_abs[t] * self.market_prices[t] for t in self.time_series) * self.step_in_hours, 'Objective Function'

		if a == "A":
			self.milp += lpSum(p_abs[t] * self.market_prices[t] + k1 * e_deg[t] + k2 * e_deg2[t] for t in self.time_series) * self.step_in_hours, 'Objective Function'
		else:
			#if a == "B" :
		#elif a == "B":
			self.milp += lpSum(p_abs[t] * self.market_prices[t] + C1 * e_deg[t] + C2 * e_deg2[t] for t in self.time_series) * self.step_in_hours, 'Objective Function'

		#self.milp += lpSum(p_abs[t] * self.market_prices[t] - p_inj[t] * self.feedin_tariffs[t] for t in self.time_series) * self.step_in_hours, 'Objective Function'

		# **************************************************************************************************************
		#           CONSTRAINTS
		# **************************************************************************************************************
		for t in self.time_series:
			# Eq. (2)
			# -- define P charged - P discharged for each t, depending on the activation of addOnInv
			if not self.add_on_inv:
				bess_flows = p_ch[t] - p_disch[t]
				bess_flows2 = p_ch2[t] - p_disch2[t]
			else:
				bess_flows = lpSum((p_ch[s][t] - p_disch[s][t]) for s in S)
				bess_flows2 = lpSum((p_ch2[s][t] - p_disch2[s][t]) for s in S)

			#  -- define the liquid consumption as load - generation (without bess flows)
			generation_and_demand = (self.load_forecasts[t] - self.pv_forecasts[t])
			self.milp += p_abs[t] == bess_flows + bess_flows2 + generation_and_demand, f'Equilibrium_{t:03d}'
			#self.milp += p_abs[t] - p_inj[t] == bess_flows + bess_flows2 + generation_and_demand, f'Equilibrium_{t:03d}'

			# Eq. (3)
			self.milp += p_abs[t] <= self.pcc_limit_value * delta_pcc[t], f'PCC_abs_limit_{t:03d}'

			# Eq. (4)
			#self.milp += p_inj[t] <= self.pcc_limit_value * (1 - delta_pcc[t]), f'PCC_inj_limit_{t:03d}'
			#self.milp += p_inj[t] <= self.pcc_limit_value * (1 - delta_pcc[t]), f'PCC_inj_limit_{t:03d}'

			if not self.add_on_inv:
				# Define variables for charging and discharging at DC-side
				bes_charge = p_ch[t] * self.bess.const_eff_ch
				bes_discharge = p_disch[t] * 1 / self.bess.const_eff_disch
				bes_charge2 = p_ch2[t] * self.bess2.const_eff_ch
				bes_discharge2 = p_disch2[t] * 1 / self.bess2.const_eff_disch

			# Eq. (5)
				self.milp += p_ch[t] <= self.bess.p_ac_max_c * delta_bess[t], \
				             f'Max_AC_charge_rate_{t:03d}'
				self.milp += p_ch2[t] <= self.bess2.p_ac_max_c * delta_bess2[t], \
							 f'Max_AC_charge2_rate_{t:03d}'
			#self.milp += p_ch[t] <= self.bess.p_dc_max_c * delta_bess[t], f'Max_DC_charge_rate_{t:03d}'
			#self.milp += p_ch2[t] <= self.bess2.p_dc_max_c * delta_bess[t], f'Max_DC_charge2_rate_{t:03d}'


			# Eq. (6)
				self.milp += p_disch[t] <= self.bess.p_ac_max_d * (1 - delta_bess[t]), \
					f'Max_AC_discharge_rate_{t:03d}'

				self.milp += p_disch2[t] <= self.bess2.p_ac_max_d * (1 - delta_bess2[t]), \
							 f'Max_AC_discharge2_rate_{t:03d}'

			else:
				# Define variables for charging and discharging at DC-side
				bes_charge = z_ch[t] + p_ch[1][t] * self.bess.const_eff_ch
				bes_discharge = z_disch[t] + p_disch[1][t] * 1 / self.bess.const_eff_disch
				bes_charge2 = z_ch2[t] + p_ch2[1][t] * self.bess2.const_eff_ch
				bes_discharge2 = z_disch2[t] + p_disch2[1][t] * 1 / self.bess2.const_eff_disch

				# Eq. (16) and (17)
				# -- define the applicable charge and discharge limits at AC-side
				for s in self.seg_series:
						if s == 0:
							min_climit = self.bess.p_ac_min_c_1 * delta_bess_ch[s][t]
							max_climit = self.bess.p_ac_max_c_1 * delta_bess_ch[s][t]
							min_dlimit = self.bess.p_ac_min_d_1 * delta_bess_disch[s][t]
							max_dlimit = self.bess.p_ac_max_d_1 * delta_bess_disch[s][t]
							min_climit2 = self.bess2.p_ac_min_c_1 * delta_bess_ch2[s][t]
							max_climit2 = self.bess2.p_ac_max_c_1 * delta_bess_ch2[s][t]
							min_dlimit2 = self.bess2.p_ac_min_d_1 * delta_bess_disch2[s][t]
							max_dlimit2 = self.bess2.p_ac_max_d_1 * delta_bess_disch2[s][t]

						else:
							min_climit = self.bess.p_ac_min_c_2 * delta_bess_ch[s][t]
							max_climit = self.bess.p_ac_max_c * delta_bess_ch[s][t]
							min_dlimit = self.bess.p_ac_min_d_2 * delta_bess_disch[s][t]
							max_dlimit = self.bess.p_ac_max_d * delta_bess_disch[s][t]
							min_climit2 = self.bess2.p_ac_min_c_2 * delta_bess_ch2[s][t]
							max_climit2 = self.bess2.p_ac_max_c * delta_bess_ch2[s][t]
							min_dlimit2 = self.bess2.p_ac_min_d_2 * delta_bess_disch2[s][t]
							max_dlimit2= self.bess2.p_ac_max_d * delta_bess_disch2[s][t]


						# -- Eq. (16 left-side)
						self.milp += min_climit <= p_ch[s][t], f'Min_AC_charge_rate_{s}_{t:03d}'
						self.milp += min_climit2 <= p_ch2[s][t], f'Min_AC_charge_rate2_{s}_{t:03d}'
						# -- Eq. (16 right-side)
						self.milp += p_ch[s][t] <= max_climit, f'Max_AC_charge_rate_{s}_{t:03d}'
						self.milp += p_ch2[s][t] <= max_climit2, f'Max_AC_charge_rate2_{s}_{t:03d}'
						# -- Eq. (17 left-side)
						self.milp += min_dlimit <= p_disch[s][t], f'Min_AC_discharge_rate_{s}_{t:03d}'
						self.milp += min_dlimit2 <= p_disch2[s][t], f'Min_AC_discharge_rate2_{s}_{t:03d}'
						# -- Eq. (17 right-side)
						self.milp += p_disch[s][t] <= max_dlimit, f'Max_AC_discharge_rate_{s}_{t:03d}'
						self.milp += p_disch2[s][t] <= max_dlimit2, f'Max_AC_discharge_rate2_{s}_{t:03d}'

				# Eq. (25)
				self.milp += z_ch[t] == self.bess.sl_eff_ch * p_ch[0][t] \
								+ self.bess.or_eff_ch * delta_bess_ch[0][t], \
								f'Z_ch_{t:03d}'
				self.milp += z_ch2[t] == self.bess2.sl_eff_ch * p_ch2[0][t] \
								+ self.bess2.or_eff_ch * delta_bess_ch2[0][t], \
							    f'Z_ch2_{t:03d}'


				# Eq. (26)
				self.milp += z_disch[t] == self.bess.sl_eff_disch * p_disch[0][t] \
									 + self.bess.or_eff_disch * delta_bess_disch[0][t], \
									 f'Z_disch_{t:03d}'

				self.milp += z_disch2[t] == self.bess2.sl_eff_disch * p_disch2[0][t] \
								 + self.bess2.or_eff_disch * delta_bess_disch2[0][t], \
						f'Z_disch2_{t:03d}'


				# Eq. (27)
				self.milp += lpSum((delta_bess_ch[s][t] + delta_bess_disch[s][t]) for s in self.seg_series) <= 1, \
									 f'Non_BESS_simultaneity_{t:03d}'

				self.milp += lpSum((delta_bess_ch2[s][t] + delta_bess_disch2[s][t]) for s in self.seg_series) <= 1, \
						f'Non_BESS_simultaneity2_{t:03d}'

			# Eq. (7) / (18)
			self.milp += bes_charge <= self.bess.p_dc_max_c, f'Max_DC_charge_rate_{t:03d}'
			self.milp += bes_charge2 <= self.bess2.p_dc_max_c, f'Max_DC_charge2_rate_{t:03d}'
			# Eq. (8) / (19)
			self.milp += bes_discharge <= self.bess.p_dc_max_d, f'Max_DC_discharge_rate_{t:03d}'
			self.milp += bes_discharge2 <= self.bess2.p_dc_max_d, f'Max_DC_discharge2_rate_{t:03d}'

			#self.milp += p_disch[t] <= self.bess.p_dc_max_d * (1 - delta_bess[t]), f'Max_DC_discharge_rate_{t:03d}'
			#self.milp += p_disch2[t] <= self.bess2.p_dc_max_d * (1 - delta_bess[t]), f'Max_DC_discharge2_rate_{t:03d}'

			# Update to BESS energy content
			e_bess_update = (bes_charge - bes_discharge) * self.step_in_hours
			e_bess_update2 = (bes_charge2 - bes_discharge2) * self.step_in_hours
			if t == 0:
				# Eq. (9) / (20)
				self.milp += e_bess[t] == self.bess.initial_e_bess + e_bess_update, f'Initial_E_update_{t:03d}'
				self.milp += e_bess2[t] == self.bess2.initial_e_bess + e_bess_update2, f'Initial_E_update2_{t:03d}'
			else:
				# Eq. (10) / (21)
				self.milp += e_bess[t] == e_bess[t - 1] + e_bess_update, f'E_update_{t:03d}'
				self.milp += e_bess2[t] == e_bess2[t - 1] + e_bess_update2, f'E_update2_{t:03d}'


			# Define energy content limits
			if self.add_on_soc:
				absolute_minimum = _dslope * bes_charge + self.bess.discharge_origin
				absolute_maximum = _cslope * bes_discharge + self.bess.charge_origin
				absolute_minimum2 = _dslope2 * bes_charge2 + self.bess2.discharge_origin
				absolute_maximum2 = _cslope2 * bes_discharge2 + self.bess2.charge_origin
			else:
				absolute_minimum = self.bess.min_e_bess
				absolute_maximum = self.bess.max_e_bess
				absolute_minimum2 = self.bess2.min_e_bess
				absolute_maximum2 = self.bess2.max_e_bess

			# Set left-side energy content limit
			self.milp += min_e_bes[t] == absolute_minimum, f'Minimum_E_content_{t:03d}'
			# Set right-side energy content limit
			self.milp += max_e_bes[t] == absolute_maximum, f'Maximum_E_content_{t:03d}'

			# Set left-side energy content limit
			self.milp += min_e_bes2[t] == absolute_minimum2, f'Minimum_E_content2_{t:03d}'
			# Set right-side energy content limit
			self.milp += max_e_bes2[t] == absolute_maximum2, f'Maximum_E_content2_{t:03d}'

			# Eq. (11 left-side) / (14 left-side) / (22 left-side)
			self.milp += min_e_bes[t] <= e_bess[t], f'E_content_low_boundary_{t:03d}'
			self.milp += min_e_bes2[t] <= e_bess2[t], f'E_content_low_boundary2_{t:03d}'
			# Eq. (11 left-side) / (14 right-side) / (22 right-side)
			self.milp += e_bess[t] <= max_e_bes[t], f'E_content_high_boundary_{t:03d}'
			self.milp += e_bess2[t] <= max_e_bes2[t], f'E_content_high_boundary2_{t:03d}'

		 	#Eq. (12) / (23)
			self.milp += e_deg[t] == self.bess.deg_slope * bes_discharge * self.step_in_hours, f'Degradation_{t:03d}'
			self.milp += e_deg2[t] == self.bess2.deg_slope * bes_discharge2 * self.step_in_hours, f'Degradation2_{t:03d}'


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

	def generate_outputs(self, a):
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
			self.__initialize_and_populate_outputs(a)

		# Generate the outputs JSON file
		master_path = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
		#structures_path = os.path.join('json', 'outputs.json')
		structures_path = os.path.join('outputs.json')
		output_path = os.path.join(master_path, structures_path)
		with open(output_path, 'w') as outfile:
			json.dump(self.outputs, outfile)

		if self.plot:
			from graphics.plot_results import plot_results
			plot_results(self)

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
		# Energy content of the BESS (kWh)
		self.varis['e_bess2'] = list(np.full(self.time_intervals, np.nan))
		# Energy degraded per time step (kWh)
		self.varis['e_deg'] = list(np.full(self.time_intervals, np.nan))
		# Energy degraded per time step (kWh)
		self.varis['e_deg2'] = list(np.full(self.time_intervals, np.nan))
		# Max E content for p_ch set point (kWh)
		self.varis['max_e_bes'] = list(np.full(self.time_intervals, np.nan))
		# Min E content for p_disch set point (kWh)
		self.varis['min_e_bes'] = list(np.full(self.time_intervals, np.nan))
		# Max E content for p_ch set point (kWh)
		self.varis['max_e_bes2'] = list(np.full(self.time_intervals, np.nan))
		# Min E content for p_disch set point (kWh)
		self.varis['min_e_bes2'] = list(np.full(self.time_intervals, np.nan))

		if not self.add_on_inv:
			# Charge P at AC-side of the BESS (kW)
			self.varis['p_ch'] = list(np.full(self.time_intervals, np.nan))
			# Discharge P at AC-side of the BESS (kW)
			self.varis['p_disch'] = list(np.full(self.time_intervals, np.nan))
			# Charge P at AC-side of the BESS (kW)
			# Aux. binary variable for non simultaneity of BESS flows
			self.varis['delta_bess'] = list(np.full(self.time_intervals, np.nan))
			# Charge P at AC-side of the BESS (kW)
			self.varis['p_ch2'] = list(np.full(self.time_intervals, np.nan))
			# Discharge P at AC-side of the BESS (kW)
			self.varis['p_disch2'] = list(np.full(self.time_intervals, np.nan))
			# Aux. binary variable for non simultaneity of BESS flows
			self.varis['delta_bess2'] = list(np.full(self.time_intervals, np.nan))

		else:
			# Charge P in 1st segment at DC-side of the BESS (kW)
			self.varis['z_ch'] = list(np.full(self.time_intervals, np.nan))
			# Discharge P in 1st segment at DC-side of the BESS (kW)
			self.varis['z_disch'] = list(np.full(self.time_intervals, np.nan))
			# Charge P at AC-side of the BESS (kW)
			self.varis['p_ch'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}
			# Discharge P at AC-side of the BESS (kW)
			self.varis['p_disch'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}
			# Aux. binary for setting the charge limits of the BESS
			self.varis['delta_bess_ch'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}
			# Aux. binary for setting the discharge limits of the BESS
			self.varis['delta_bess_disch'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}

			# Charge P in 1st segment at DC-side of the BESS (kW)
			self.varis['z_ch2'] = list(np.full(self.time_intervals, np.nan))
			# Discharge P in 1st segment at DC-side of the BESS (kW)
			self.varis['z_disch2'] = list(np.full(self.time_intervals, np.nan))
			# Charge P at AC-side of the BESS (kW)
			self.varis['p_ch2'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}
			# Discharge P at AC-side of the BESS (kW)
			self.varis['p_disch2'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}
			# Aux. binary for setting the charge limits of the BESS
			self.varis['delta_bess_ch2'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}
			# Aux. binary for setting the discharge limits of the BESS
			self.varis['delta_bess_disch2'] = {s: list(np.full(self.time_intervals, np.nan)) for s in self.seg_series}

		# **************************************************************************************************************
		#        FILL DECISION VARIABLES
		# **************************************************************************************************************
		for v in self.milp.variables():
			if not re.search('dummy', v.name):
				t = int(v.name[-3:])

			if re.search('p_abs_', v.name):
				self.varis['p_abs'][t] = v.varValue

			#elif re.search('p_inj_', v.name):
				#self.varis['p_inj'][t] = v.varValue

			elif re.search('delta_pcc_', v.name):
				self.varis['delta_pcc'][t] = v.varValue

			elif re.search(f'e_bess_', v.name):
				self.varis['e_bess'][t] = v.varValue

			elif re.search(f'e_bess2_', v.name):
				self.varis['e_bess2'][t] = v.varValue

			elif re.search(f'e_deg_', v.name):
				self.varis['e_deg'][t] = v.varValue

			elif re.search(f'e_deg2_', v.name):
				self.varis['e_deg2'][t] = v.varValue

			elif re.search(f'max_e_bes_', v.name):
				self.varis['max_e_bes'][t] = v.varValue

			elif re.search(f'min_e_bes_', v.name):
				self.varis['min_e_bes'][t] = v.varValue

			elif re.search(f'max_e_bes2_', v.name):
				self.varis['max_e_bes2'][t] = v.varValue

			elif re.search(f'min_e_bes2_', v.name):
				self.varis['min_e_bes2'][t] = v.varValue

			elif re.search(f'p_ch_', v.name) and not self.add_on_inv:
				self.varis['p_ch'][t] = v.varValue

			elif re.search(f'p_disch_', v.name) and not self.add_on_inv:
				self.varis['p_disch'][t] = v.varValue

			elif re.search(f'p_ch2_', v.name) and not self.add_on_inv:
				self.varis['p_ch2'][t] = v.varValue

			elif re.search(f'p_disch2_', v.name) and not self.add_on_inv:
				self.varis['p_disch2'][t] = v.varValue

			elif re.search(f'delta_bess_', v.name):
				self.varis['delta_bess'][t] = v.varValue

			elif re.search(f'z_ch_', v.name) and self.add_on_inv:
				self.varis['z_ch'][t] = v.varValue

			elif re.search(f'z_disch_', v.name) and self.add_on_inv:
				self.varis['z_disch'][t] = v.varValue

			elif re.search(f'delta_bess2_', v.name):
				self.varis['delta_bess2'][t] = v.varValue

			elif re.search(f'z_ch2_', v.name) and self.add_on_inv:
				self.varis['z_ch2'][t] = v.varValue

			elif re.search(f'z_disch2_', v.name) and self.add_on_inv:
				self.varis['z_disch2'][t] = v.varValue

			else:
				for s in self.seg_series:
					if re.search(f'p_ch_{s}_', v.name) and self.add_on_inv:
						self.varis[f'p_ch'][s][t] = v.varValue

					if re.search(f'p_ch2_{s}_', v.name) and self.add_on_inv:
						self.varis[f'p_ch2'][s][t] = v.varValue

					elif re.search(f'p_disch_{s}_', v.name) and self.add_on_inv:
						self.varis[f'p_disch'][s][t] = v.varValue

					elif re.search(f'p_disch2_{s}_', v.name) and self.add_on_inv:
						self.varis[f'p_disch2'][s][t] = v.varValue

					elif re.search(f'delta_bess_ch_{s}_', v.name) and self.add_on_inv:
						self.varis[f'delta_bess_ch'][s][t] = v.varValue

					elif re.search(f'delta_bess_ch2_{s}_', v.name) and self.add_on_inv:
						self.varis[f'delta_bess_ch'][s][t] = v.varValue

					elif re.search(f'delta_bess_disch_{s}_', v.name) and self.add_on_inv:
						self.varis[f'delta_bess_disch'][s][t] = v.varValue

					elif re.search(f'delta_bess_disch2_{s}_', v.name) and self.add_on_inv:
						self.varis[f'delta_bess_disch2'][s][t] = v.varValue
	def __initialize_and_populate_outputs(self, a):
		"""
		Initializes and populates the outputs' structure as a dictionary matching the outputs JSON format.
		:return: None
		:rtype: None
		"""
		# Sum the variables p_ch and p_dis values across the different segments to obtain a single value per asset
		# and per time step, in case add_on_inv is active
		if not self.add_on_inv:
			p_ch = self.varis.get('p_ch')
			p_disch = self.varis.get('p_disch')
			p_ch2 = self.varis.get('p_ch2')
			p_disch2 = self.varis.get('p_disch2')

		else:
			p_ch = list(pd.DataFrame(self.varis.get('p_ch')).sum(axis=1))
			p_disch = list(pd.DataFrame(self.varis.get('p_disch')).sum(axis=1))
			p_ch2 = list(pd.DataFrame(self.varis.get('p_ch2')).sum(axis=1))
			p_disch2 = list(pd.DataFrame(self.varis.get('p_disch2')).sum(axis=1))



		# Create a list of the set points' datetime corresponding values, as strings, in ISO 8601 format
		list_of_dates = mhelper.create_strftime_list(self.horizon, self.step_in_hours, self.start_at)

		# Calculate the expected revenues
		pcc_absorption = np.array(self.varis.get('p_abs'))
		edeg = np.array(self.varis.get('e_deg'))
		edeg2 = np.array(self.varis.get('e_deg2'))
		of = (pcc_absorption * self.market_prices ) * self.step_in_hours


		if a == "A":
			totdeg = k1 * edeg + k2 * edeg2
		else:
		#elif a == "B":
			totdeg = C1 * edeg + C2 * edeg2
		#else:
			#print("ERRO")
		tot = of + totdeg
		#merge = p_ch - p_disch
		merge = np.array(self.varis.get('p_ch')) - np.array(self.varis.get('p_disch'))


		#of = (pcc_absorption * self.market_prices - pcc_injection * self.feedin_tariffs) * self.step_in_hours

		#Initialize outputs as a dictionary
		self.outputs = dict(
			milpStatus=self.milp.status,
			pCharge=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, p_ch)],
			pDischarge=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, p_disch)],
			eBess=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('e_bess'))],
			eDeg=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('e_deg'))],
			pCharge2=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, p_ch2)],
			pDischarge2=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, p_disch2)],
			eBess2=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('e_bess2'))],
			eDeg2=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('e_deg2'))],
			pAbs=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('p_abs'))],
			#pInj=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, self.varis.get('p_inj'))],
			expectRevs=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, of)],
			Totaldeg=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, totdeg)],
			Total=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, tot)],
			Merge=[{'datetime': dt, 'setpoint': val} for dt, val in zip(list_of_dates, merge)],


		)

	@staticmethod
	def final_folder_cleaning():

		"""Cleans the directory of optimization byproducts by deleting the files with the specified extensions.
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
