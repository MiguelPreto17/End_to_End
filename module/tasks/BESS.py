"""
BESS class. This class encompasses all information regarding the BESS of the system.
"""
import math
import numpy as np
import pandas as pd

from helpers.dynamic_bess_helpers import *
from loguru import logger
from time import time


class BESS:
    def __init__(self):
        # Input data
        self.bess_asset = None  # Object to harbour the BESS's main characteristics
        self.bess_soc = None  # Object to harbour measured BESS SoC
        self.bess_tests = None  # Object to harbour BESS test data required for better modelling
        self.deg_curve = None  # Object to harbour BESS degradation curve
        self.add_ons = None  # Object whit information about

        # Dict for getting the values' names for each possible test set
        self.key2test_value = dict(vNomD='vAvg',
                                   vNomC='vAvg',
                                   dLim='eRemain',
                                   cLim='eRemain',
                                   effD='effDchAvg',
                                   effC='effChAvg',
                                   roundEff='roundEffAvg')

        # Dict for getting the action regarding a respective test set
        self.test_value2action = dict(effDchAvg='discharge',
                                      effChAvg='charge',
                                      roundEffAvg='roundtrip')

        # Inverter's data
        self.inverter_nominal_power = None  # kVA
        self.inverter_nominal_current = None  # kA
        self.inverter_nominal_voltage = None  # Vac
        self.inverter_max_idc = None  # Inverter's maximum admissible current on DC side (A)
        self.p_ac_min_c_1 = None  # Min. charge P rate for first segment of piecewise lin. of eff. curve (kVA)
        self.p_ac_max_c_1 = None  # Max. charge P rate for first segment of piecewise lin. of eff. curve (kVA)
        self.p_ac_min_c_2 = None  # Min. charge P rate for second segment of piecewise lin. of eff. curve (kVA)
        self.p_ac_min_d_1 = None  # Min. discharge P rate for first segment of piecewise lin. of eff. curve (kVA)
        self.p_ac_max_d_1 = None  # Max. discharge P rate for first segment of piecewise lin. of eff. curve (kVA)
        self.p_ac_min_d_2 = None  # Min. discharge P rate for second segment of piecewise lin. of eff. curve (kVA)
        self.p_ac_max_c = None  # Maximum power rate for charging (kVA)
        self.p_ac_max_d = None  # Maximum power rate for discharging (kVA)



        # Trapezium's S approach parameters
        # self.nr_trapeziums = None  # number of total trapeziums
        # self.trap_left_p = None  # list with the left P limits of each trapezium
        # self.trap_right_p = None  # list with the right P limits of each trapezium
        # self.trap_left_q = None  # list with the left Q limits of each trapezium
        # self.trap_right_q = None  # list with the right Q limits of each trapezium

        # BESS's data
        self.nominal_voltage = None  # Vdc
        self.initial_energy = None  # BESS initial energy capacity, before any degradation (kWh)
        self.nominal_energy = None  # kWh
        self.nominal_capacity = None  # kAh
        self.max_e_bess = None  # BES's maximum E content (kWh)
        self.maximum_e_bess = None  # BES's maximum E content before any degradation (kWh)
        self.min_e_bess = None  # BES's minimum E content (kWh) or BESS's reserve SoC (>= minimum SoC) (kWh)
        self.initial_e_bess = None  # BES's initial E content (kWh)
        self.c_rate_max_ch = None  # Maximum charging c-rate
        self.c_rate_max_disch = None  # Maximum discharging c-rate
        self.p_dc_max_c = None  # Maximum power rate for charging the battery from DC view point (kW)
        self.p_dc_max_d = None  # Maximum power rate for discharging the battery from DC view point (kW)

        self.charge_slope = None  # Line slope parameter for maximum BESS energy limit
        self.charge_origin = None  # Line origin parameter for maximum BESS energy limit
        self.discharge_slope = None  # Line slope parameter for minimum BESS energy limit
        self.discharge_origin = None  # Line origin parameter for minimum BESS energy limit
        self.v_nom_charge = None  # BESS's nominal charge voltage
        self.v_nom_discharge = None   # BESS's nominal discharge voltage
        self.constant_eff_flag = None  # Flag for considering efficiency as constant

        self.default_deg_slope = 4.5E-5  # Default degradation slope for when no data is provided
        self.deg_curve = None  # Placeholder for degradation curves data provided
        self.deg_slope = None  # Degradation curve linearization slope
        self.lifetime = None  # Desired lifetime in years
        self.degradation_level = None  # End Of Life Criterion in %
        self.capacity_loss = None  # 100 - EOL Criterion

        # Efficiencies' data
        # AC power rate (in p.u.) above which effs. are considered as constant
        self.__cut_values = dict(charge=0.1,
                                 discharge=0.1,
                                 roundtrip=0.1)

        self.sl_eff_ch = None  # slope of charge eff. lin. (BES + inverter)
        self.or_eff_ch = None  # origin of charge eff. lin. (BES + inverter)
        self.sl_eff_disch = None  # slope of discharge eff. lin. (BES + inverter)
        self.or_eff_disch = None  # origin of discharge eff. lin. (BES + inverter)
        self.const_eff_ch = None  # value of constant charge eff. (after cut value) (BES + inverter)
        self.const_eff_disch = None  # value of constant discharge eff. (after cut value) (BES + inverter)

    def configure(self, bess_asset, bess_soc, add_ons):
        """
        Configure initialized BESS class with data from input JSON regarding the BES system
        :param bess_asset: main structure with BESS's characteristics ( = "bessAsset" structure)
        :type bess_asset: dict
        :param bess_soc: measured BESS SoC
        :type bess_soc: float
        :param add_ons: dictionary with all add_ons status
        :type add_ons: dict of bool
        :return: None
        :rtype: None
        """
        config_t = time()
        logger.debug(f'Configuring BESS asset ...')

        self.bess_asset = bess_asset
        self.bess_soc = bess_soc
        self.add_ons = add_ons
        self.bess_tests = bess_asset.get('testData')
        self.deg_curve = bess_asset.get('degCurve')
        self.lifetime = bess_asset.get('lifetime')
        self.degradation_level = bess_asset.get('eolCriterion')

        # Assign inverters data (AC side)
        logger.debug(f' - parsing AC-side parameters')
        self.inverter_nominal_power = self.bess_asset.get('invSNom')
        self.inverter_nominal_voltage = self.bess_asset.get('invVNom')
        self.inverter_nominal_current = self.inverter_nominal_power / (math.sqrt(3) * self.inverter_nominal_voltage)
        self.p_ac_min_c_1 = self.bess_asset.get('minPCh') / 100 * self.inverter_nominal_power
        self.p_ac_min_d_1 = self.bess_asset.get('minPDch') / 100 * self.inverter_nominal_power
        self.p_ac_max_c_1 = self.inverter_nominal_power * self.__cut_values.get('charge')
        self.p_ac_max_d_1 = self.inverter_nominal_power * self.__cut_values.get('discharge')
        self.p_ac_min_c_2 = self.p_ac_max_c_1
        self.p_ac_min_d_2 = self.p_ac_max_d_1
        self.p_ac_max_c = self.inverter_nominal_power
        self.p_ac_max_d = self.inverter_nominal_power

        # Calculate Q and P left and right limits for trapezium approach to P^2 <= S^2 - Q^2
        # logger.debug(f' - calculating trapezium limits of PQ-circle')
        # self.__calc_trapezium_limits()

        # Assign batteries data (DC side)
        logger.debug(f' - parsing DC-side parameters')
        self.initial_energy = self.bess_asset.get('eNom')
        self.nominal_energy = self.bess_asset.get('actualENom')
        self.nominal_voltage = self.bess_asset.get('vNom')
        self.nominal_capacity = self.nominal_energy / self.nominal_voltage
        self.max_e_bess = self.bess_asset.get('maxSoc') / 100 * self.nominal_energy
        self.maximum_e_bess = self.bess_asset.get('maxSoc') / 100 * self.initial_energy
        operational_min = max(self.bess_asset['minSoc'], self.bess_asset['reserveSoc'])
        self.min_e_bess = operational_min / 100 * self.nominal_energy
        self.initial_e_bess = self.bess_soc / 100 * self.nominal_energy
        self.inverter_max_idc = self.bess_asset.get('invMaxIDC')
        self.c_rate_max_ch = c_rate_limits(self.bess_asset.get('maxCCh'), self.nominal_capacity,
                                           self.inverter_max_idc)
        self.c_rate_max_disch = c_rate_limits(self.bess_asset.get('maxCDch'), self.nominal_capacity,
                                              self.inverter_max_idc)
        self.p_dc_max_c = self.c_rate_max_ch * self.nominal_capacity * self.nominal_voltage
        self.p_dc_max_d = self.c_rate_max_disch * self.nominal_capacity * self.nominal_voltage

        # Check how efficiency should be approximated given the power limits imposed
        logger.debug(f' - parsing efficiency parameters')
        self.__is_constant_eff_applicable()
        self.const_eff_ch = self.bess_asset.get('chEff') / 100
        self.const_eff_disch = self.bess_asset.get('dischEff') / 100

        # Calculate the degradation slope when data is provided or assign default value
        logger.debug(f'- parsing degradation curve')
        self.capacity_loss = 100 - self.degradation_level
        if self.deg_curve is not None:
            self.deg_slope = deg_curve_linearization(pd.DataFrame(self.deg_curve), self.capacity_loss)
        else:
            self.deg_slope = self.default_deg_slope

        # Check for test data in the input data provided
        if self.bess_tests is not None:
            logger.debug(f' - parsing test data')
            self.__read_tests()
            logger.debug(f'Configuring BESS asset ... OK! ({time() - config_t:.3f}s)')
            return True

        # With no test data provided, linearization of the efficiency curves can nonetheless be performed
        else:
            logger.debug(f' - no test data available; linearizing efficiency curves')
            self.__basic_linear_eff()
            logger.debug(f'Configuring BESS asset ... OK! ({time() - config_t:.3f}s)')
            return False

    def __read_tests(self):
        """
        Function for reading and parsing information regarding the BESS's test sets' data
        :return: None
        :rtype: None
        """
        ############################################################################################################
        #                                      DYNAMIC SOC LIMITS												   #
        ############################################################################################################
        # For each set of tests check if the same c-rate was tested in different trial runs and, if so, averages
        tests_dups_avg = average_c_rates_dups(self.bess_tests, self.key2test_value)

        # If global flag for addOnSoc is set, validate BESS's vNomC, vNomD, cLim and dLim test sets
        if self.add_ons['addOnSoc']:
            # Find nominal charge voltage
            self.__validate_vnomc(tests_dups_avg.get('vNomC'))
            # Find nominal discharge voltage
            self.__validate_vnomd(tests_dups_avg.get('vNomD'))
            # Update max charge power rates at battery's end
            self.__max_charge_power(tests_dups_avg.get('vNomC'))
            # Update max discharge power rates at battery's end
            self.__max_discharge_power(tests_dups_avg.get('vNomD'))
            # Check maximum energy content values per C-rate
            self.__validate_clim(tests_dups_avg.get('cLim'))
            # Check minimum energy content values per C.rate
            self.__validate_dlim(tests_dups_avg.get('dLim'))

        ############################################################################################################
        #                                      		EFFICIENCIES												   #
        ############################################################################################################
        # If local flag for 'betterEffApprox' is set, validate BESS's 'effC' and 'effD' test sets
        if bool(tests_dups_avg.get('betterEffApprox')):
            self.__separate_linear_eff(tests_dups_avg)

        # Otherwise, if local flag for 'roundEffApprox' is set, validate BESS's 'roundEff' test set
        elif bool(tests_dups_avg.get('roundEffApprox')):
            self.__roundtrip_linear_eff(tests_dups_avg)

    def __validate_vnomc(self, test_data):
        """
        Function for validating vNomC (Nominal Charge Voltage) data from the tests
        Nominal voltage is calculated as the average of the average voltage values retrieved for charging
        the BESS at several previously defined C-rates, usually between 0 and the maximum C-rate admissible.
        :param test_data: dataframe of "vNomC" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: None
        :rtype: None
        """
        self.v_nom_charge = test_data.get(self.key2test_value.get('vNomC')).mean()

    def __validate_vnomd(self, test_data):
        """
        Function for validating vNomD (Nominal Discharge Voltage) data from the tests
        Nominal voltage is calculated as the average of the average voltage values retrieved for discharging
        the BESS at several previously defined C-rates, usually between 0 and the maximum C-rate admissible.
        :param test_data: dataframe of "vNomD" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: None
        :rtype: None
        """
        self.v_nom_discharge = test_data.get(self.key2test_value.get('vNomD')).mean()

    def __max_charge_power(self, test_data):
        """
        Function for updating the batteries maximum charge power rate, supported by the tests
        A better approached power rate limit for charging can also be approximated from this data.
        :param test_data: dataframe of "vNomC" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: None
        :rtype: None
        """
        self.p_dc_max_c = power_rate_limits(self.nominal_capacity, self.c_rate_max_ch, test_data, action='charge')

    def __max_discharge_power(self, test_data):
        """
        Function for updating the batteries maximum charge power rate, supported by the tests
        A better approached power rate limit for discharging can also be approximated from this data.
        :param test_data: dataframe of "vNomD" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: None
        :rtype: None
        """
        self.p_dc_max_d = power_rate_limits(self.nominal_capacity, self.c_rate_max_disch, test_data, action='discharge')

    def __validate_clim(self, test_data):
        """
        Function for acquiring the line parameters for applying a dynamic SoC charging limit
        :param test_data: dataframe of "cLim" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: None
        :rtype: None
        """
        self.charge_slope, self.charge_origin = self.__validate_lim(test_data)

    def __validate_dlim(self, test_data):
        """
        Function for acquiring the line parameters for applying a dynamic SoC discharging limit
        :param test_data: dataframe of "dLim" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: None
        :rtype: None
        """
        self.discharge_slope, self.discharge_origin = self.__validate_lim(test_data)

    def __validate_lim(self, test_data):
        """
        Function for acquiring the line parameters for applying any dynamic SoC limit
        :param test_data: dataframe of "dLim" or "cLim" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :return: line parameters
        :rtype: (float, float)
        """
        test_data['cRate'] *= self.nominal_capacity
        test_data['eRemain'] *= self.nominal_energy / 100

        return linearize(test_data)

    def __is_constant_eff_applicable(self):
        """
        Checks if a stepwise linearization is applicable to the BESS data set or if a constant efficiency
        is adequate enough (i. e., no small power rates will ever be required from the BESS)
        :return: None
        :rtype: None
        """

        modelize_c = self.p_ac_min_c_1 < self.p_ac_max_c_1
        modelize_d = self.p_ac_min_d_1 < self.p_ac_max_d_1

        # If for any maneuver, charge or discharge, a constant efficiency is to be assumed, it will be for the other
        self.constant_eff_flag = not (modelize_c and modelize_d)

    def __separate_linear_eff(self, tests):
        """
        Function for calculating the line parameters of BESS's charge and discharge efficiency curves
        when test data is provided
        :param tests: dictionary with all tests performed in dataframe format
        :type tests: dict of pandas.core.frame.DataFrame
        :return: None
        :rtype: None
        """
        # Get auxiliary parameter names
        c_test_name = self.key2test_value.get('effC')
        d_test_name = self.key2test_value.get('effD')

        # Calculate and assign the linearization parameters
        self.sl_eff_ch, self.or_eff_ch, self.const_eff_ch = \
            self.__validate_eff_tests(tests.get('effC'), c_test_name)
        self.sl_eff_disch, self.or_eff_disch, self.const_eff_disch = \
            self.__validate_eff_tests(tests.get('effD'), d_test_name)

    def __roundtrip_linear_eff(self, tests):
        """
        Function for calculating the line parameters of BESS's round trip efficiency curves
        when test data is provided
        :param tests: dictionary with all tests performed in dataframe format
        :type tests: dict of pandas.core.frame.DataFrame
        :return: None
        :rtype: None
        """
        # Square root the test values, assuming the same value for charge and discharge procedures at same C-rate
        sqrt_values = np.sqrt(tests.get('roundEff').get('roundEffAvg'))
        tests['roundEff'].assign(roundEffAvg=sqrt_values)

        # Get auxiliary parameter names
        r_test_name = self.key2test_value.get('roundEff')

        # Calculate the linearization parameters
        self.ch, self.or_eff_disch, self.const_eff_disch = \
            self.__validate_eff_tests(tests.get('roundEff'), r_test_name)

        # Assign parameter values to the respective class variables
        self.sl_eff_ch = self.sl_eff_disch
        self.or_eff_ch = self.or_eff_disch
        self.const_eff_ch = self.const_eff_disch

    def __validate_eff_tests(self, test_data, values_col_name, crates_col_name='cRate'):
        """
        Averages test values of "effC"/"effD" structure and checks if a linearization of the curve is to be made
        :param test_data: dataframe of "effC"/"effD" structure
        :type test_data: pandas.core.frame.DataFrame of float
        :param values_col_name: test values' column name in test_data dataframe
        :type values_col_name: str
        :param crates_col_name: C-rates' column name in test_data dataframe
        :type crates_col_name: str
        :return: parameters of linearization and the constant efficiency value to be assumed after the cut value
        :rtype: (float, float, float)
        """
        # Assign needed data and parameters to less verbose variables
        pruned_test_data = test_data.loc[test_data['cRate'] > 0.1]
        c_rate = pruned_test_data.get(crates_col_name)
        test_values = pruned_test_data.get(values_col_name) / 100
        modelize = not self.constant_eff_flag

        # Update value for constant efficiency as the average of the observed test values
        constant_average = test_values.mean()

        # Calculate the slope and origin of efficiency(power) curve linearization, applicable before the cut value
        # and the constant efficiency value, applicable after the cut value
        slope, origin = None, None
        if modelize:
            slope, origin = self.__linearize_eff_curve(c_rate, test_values, constant_average)

        return slope, origin, constant_average

    def __linearize_eff_curve(self, c_rate, test_values, constant_eff):
        """
        Function to retrieve the parameters of an efficiency curve linearization
        :param c_rate: C-rates tested
        :type c_rate: pd.core.series.Series of float
        :param test_values: corresponding efficiency values registered
        :type test_values: pd.core.series.Series of float
        :param constant_eff: constant efficiency value to be considered after the cut value
        :type constant_eff: float
        :return:
        """
        # Assign needed data and parameters to less verbose variables
        nom_capacity = self.nominal_capacity
        nom_voltage = self.nominal_voltage

        # Transform the data into inputs for linearization (abscissa - power_rates; ordinate - eff_times_power_rates)
        power_rates = c_rate * nom_capacity * nom_voltage
        eff_times_power_rates = power_rates * test_values

        # Transform cut_value defined as a C-rate into a power rate
        action = self.test_value2action.get(test_values.name)
        cut_value = self.__cut_values.get(action) * self.inverter_nominal_power

        # Calculate the slope and origin of efficiency(power) curve linearization, applicable before the cut value
        # and the constant efficiency value, applicable after the cut value
        power_rates.name = 'x'
        eff_times_power_rates.name = 'y'
        df_to_linearize = pd.concat([power_rates, eff_times_power_rates], axis=1)
        slope, origin = efficiencies(df_to_linearize, cut_value, constant_eff)

        # Update cut value so that the constant efficiency is not exceeded for Pinv <= 0.1 Pinv,nom
        new_cut_power = (constant_eff * cut_value - origin) / slope
        if test_values.name == 'effChAvg':
            self.p_ac_max_c_1 = new_cut_power
            self.p_ac_min_c_2 = new_cut_power
        elif test_values.name == 'effDchAvg':
            self.p_ac_max_d_1 = new_cut_power
            self.p_ac_min_d_2 = new_cut_power
        elif test_values.name == 'roundEffAvg':
            self.p_ac_max_c_1 = new_cut_power
            self.p_ac_min_c_2 = new_cut_power
            self.p_ac_max_d_1 = new_cut_power
            self.p_ac_min_d_2 = new_cut_power

        return slope, origin

    def __basic_linear_eff(self):
        """
        Function for calculating the line parameters of BESSs' charge and discharge efficiency curves
        when no test data is provided, except the charge and discharge constant efficiencies
        Note that this basic linearization is later overwritten if a test set with measures efficiencies is available.
        :return: None
        :rtype: None
        """
        if self.add_ons.get('addOnInv'):
            self.or_eff_ch = {}
            self.or_eff_disch = {}

            c_rate = pd.Series(1.0)
            ch_test_value = pd.Series(self.const_eff_ch)
            ch_test_value.name = 'effChAvg'
            disch_test_value = pd.Series(self.const_eff_disch)
            disch_test_value.name = 'effDchAvg'

            # Calculate the slope and origin of efficiency(power) curve linearization applicable before the cut value
            self.sl_eff_ch, self.or_eff_ch = \
                self.__linearize_eff_curve(c_rate, ch_test_value, self.const_eff_ch)

            self.sl_eff_disch, self.or_eff_disch = \
                self.__linearize_eff_curve(c_rate, disch_test_value, self.const_eff_disch)

    # def __calc_trapezium_limits(self):
    # 	"""
    # 	Function to calculate the P and Q upper limits of the trapeziums approach to the S-circle
    # 	:return: None
    # 	:rtype: None
    # 	"""
    #
    # 	fractions_of_nominal_s = np.array([0, 1 / 6, 1 / 3, 1 / 2, 2 / 3, 3 / 4, 5 / 6, 11 / 12, 1])
    # 	self.nr_trapeziums = len(fractions_of_nominal_s) - 1
    #
    # 	# P limits are calculated directly from multiplying the inverter's nominal S by the fractions defined above
    # 	self.trap_left_p = self.inverter_nominal_power * fractions_of_nominal_s[:-1]
    # 	self.trap_right_p = self.inverter_nominal_power * fractions_of_nominal_s[1:]
    #
    # 	# Q limits for the same points are calculated using the Pythagoras Theorem expression
    # 	s_squared = self.inverter_nominal_power ** 2
    #
    # 	left_p_squared = self.trap_left_p ** 2
    # 	right_p_squared = self.trap_right_p ** 2
    #
    # 	left_difference = s_squared - left_p_squared
    # 	right_difference = s_squared - right_p_squared
    #
    # 	self.trap_left_q = np.sqrt(left_difference)
    # 	self.trap_right_q = np.sqrt(right_difference)
