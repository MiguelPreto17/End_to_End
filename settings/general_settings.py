"""
EDIT HERE your settings for running "run.py"
- all_days -----------> options: from range (0, 1) to range (0, 365) and between
- plot ---------------> set True to save plot of each days' forecasts and BESS set points
- scale_pv -----------> Installed pv capacity [kW]
- scale_inflex -------> Maximum demand capacity [kW]
- pcc_limit_value ----> a maximum power limit at the connection to the grid, in kW
- init_dt ------------> datetime at the beginning of the optimization horizon ("dd/mm/yyyy  HH:MM:SS")
"""


class GeneralSettings:
	all_days = range(0, 1)
	plot = False

	# milp_params
	mipgap = 0.001  # solver's tolerance
	timeout = 300  # time limit for solver (! does not consider time required for solving primal, relaxed, problem!)
	# WARNING: when choosing all_days with more than one day, don't change horizon = 24
	horizon = 24  # optimization horizon in hours
	# WARNING: don't choose a step greater than 60 minutes
	step = 60  # optimization step in minutes

	# settings
	scale_pv = 20.0  # kW
	scale_load = 15.0  # kW
	pcc_limit_value = 100.0  # kW
	init_dt = '01/01/2018  00:00:00'  # format: 'dd/mm/yyyy  HH:MM:SS'

	bess_initial_soc = 50.0  # SoC % at the beginning of the optimization horizon [%]
	bess_e_nom = 20.0  # nominal energy capacity [kWh]
	bess_inv_max_idc = 1.0  # inverter's maximum DC current [kA]
	bess_inv_s_nom = 10.0  # inverter's nominal power [kVA]
	bess_inv_v_nom = 400.0  # inverter's nominal voltage [V]
	bess_max_c_ch = 1  # maximum C-rate for charging [0, 1]
	bess_max_c_disch = 1  # maximum C-rate for charging [0, 1]
	bess_max_soc = 100.0  # maximum SoC [%]
	bess_min_p_ch = 0.0  # minimum power rate admissible for charging [%]
	bess_min_p_disch = 0.0  # minimum power rate admissible for discharging [%]
	bess_min_soc = 0.0  # minimum SoC [%]
	bess_v_nom = 720.0  # nominal voltage [V]
