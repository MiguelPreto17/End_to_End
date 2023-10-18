"""
EDIT HERE your settings for running "run.py"
- final_outputs_file -> name of the .csv file to store the outputs; saved in the same folder as "run.py"
- add_on_inv ---------> set True to consider the two-step approach for estimating overall efficiency; False for constant
- add_on_soc ---------> set True to consider dynamic SoC limits; False for static
- all_days -----------> options: from range (0, 1) to range (0, 365) and between
- plot ---------------> set True to save plot of each days' forecasts and BESS set points
- scale_pv -----------> Installed pv capacity [kW]
- scale_inflex -------> Maximum demand capacity [kW]
- pcc_limit_value ----> a maximum power limit at the connection to the grid, in kW
- init_dt ------------> datetime at the beginning of the optimization horizon ("dd/mm/yyyy  HH:MM:SS")
"""
import random

class GeneralSettings:
    add_on_inv = False
    add_on_soc = False
    all_days = range(0,2)
    plot = False

    # milp_params
    mipgap = 0.001  # solver's tolerance
    timeout = 300  # time limit for solver (! does not consider time required for solving primal, relaxed, problem!)
    # WARNING: when choosing all_days with more than one day, don't change horizon = 24
    horizon = 24  # optimization horizon in hours
    # WARNING: don't choose a step greater than 60 minutes
    step = 60  # optimization step in minutes

    # settings
    scale_pv = 0.0  # kW
    scale_load = 1.0  # kW
    pcc_limit_value = 140.0  # kW
    init_dt = '01/01/2018  00:00:00'  # format: 'dd/mm/yyyy  HH:MM:SS'

    #0.785714
    #0.78571429

    bess_max_c_ch = 0.785714  # maximum C-rate for charging [0, 1]
    bess_max_c_disch = 0.785714  # maximum C-rate for charging [0, 1]
    bess_initial_soc = 0.0  # SoC % at the beginning of the optimization horizon [%]
    bess_e_nom = 140
    bess_eol_criterion = 70.0  # end-of-life criterion (i.e. soc % at end-of-life) [%]
    #bess_ch_eff = 100.0  # fixed charge efficiency [%]
    #bess_disch_eff = 100.0  # fixed discharge efficiency [%]
    bess_inv_max_idc = 1.0  # inverter's maximum DC current [kA]
    bess_inv_s_nom = bess_max_c_ch * bess_e_nom # inverter's nominal power [kVA]
    bess_inv_v_nom = 400.0  # inverter's nominal voltage [V]
    bess_max_soc = 100.0  # maximum SoC [%]
    bess_min_p_ch = 0.0  # minimum power rate admissible for charging [%]
    bess_min_p_disch = 0.0  # minimum power rate admissible for discharging [%]
    bess_min_soc = 0.0  # minimum SoC [%]
    bess_reserve_soc = 0.0    # reserve SoC [%] (becomes minimum SoC if > bess_min_soc)
    bess_v_nom = 720.0  # nominal voltage [V]
    bess_deg_curve = 1


    bess_max_c_ch2 = 0.0 # maximum C-rate for charging [0, 1]
    bess_max_c_disch2 = 0.0 # maximum C-rate for charging [0, 1]
    bess_initial_soc2 = 0.0  # SoC % at the beginning of the optimization horizon [%]
    bess_e_nom2 = 0.000000001 # nominal energy capacity [kWh]
    bess_eol_criterion2 = 70.0  # end-of-life criterion (i.e. soc % at end-of-life) [%]
    #bess_ch_eff2 = 100.0  # fixed charge efficiency [%]
    #bess_disch_eff2 = 100.0  # fixed discharge efficiency [%]
    bess_inv_max_idc2 = 1.0  # inverter's maximum DC current [kA]
    bess_inv_s_nom2 = bess_max_c_ch2 * bess_e_nom2  # inverter's nominal power [kVA]
    bess_inv_v_nom2 = 400.0  # inverter's nominal voltage [V]
    bess_max_soc2 = 100.0  # maximum SoC [%]
    bess_min_p_ch2 = 0.0  # minimum power rate admissible for charging [%]
    bess_min_p_disch2 = 0.0  # minimum power rate admissible for discharging [%]
    bess_min_soc2 = 0.0  # minimum SoC [%]
    bess_reserve_soc2 = 0.0  # reserve SoC [%] (becomes minimum SoC if > bess_min_soc)
    bess_v_nom2 = 720.0  # nominal voltage [V]
    bess_deg_curve2 = 2



    """bess_deg_curve1 = [
                            {"nrCycles": 10000000, "dod": 1.0},
                            {"nrCycles": 900000, "dod": 5.0},
                            {"nrCycles": 650000, "dod": 10.0},
                            {"nrCycles": 400000, "dod": 15.0},
                            {"nrCycles": 145000, "dod": 20.0},
                            {"nrCycles": 82500, "dod": 25.0},
                            {"nrCycles": 68500, "dod": 30.0},
                            {"nrCycles": 45000, "dod": 35.0},
                            {"nrCycles": 35000, "dod": 40.0},
                            {"nrCycles": 30000, "dod": 45.0},
                            {"nrCycles": 22500, "dod": 50.0},
                            {"nrCycles": 19500, "dod": 55.0},
                            {"nrCycles": 16750, "dod": 60.0},
                            {"nrCycles": 14000, "dod": 65.0},
                            {"nrCycles": 11250, "dod": 70.0},
                            {"nrCycles": 10000, "dod": 75.0},
                            {"nrCycles": 9400, "dod": 80.0},
                            {"nrCycles": 8350, "dod": 85.0},
                            {"nrCycles": 8050, "dod": 90.0},
                            {"nrCycles": 7925, "dod": 95.0},
                            {"nrCycles": 7850, "dod": 100.0}
        ]
    """


    bess_deg_curve_lithium = [

                            {"nrCycles": 400000, "dod": 10.0},
                            {"nrCycles": 60000, "dod": 25.0},
                            {"nrCycles": 20000, "dod": 50.0},
                            {"nrCycles": 10000, "dod": 75.0},
                            {"nrCycles": 7000, "dod": 100.0}
                                            ]


    """bess_deg_curve2 = [
                            {"nrCycles": 100000, "dod": 1.0},
                            {"nrCycles": 100000, "dod": 5.0},
                            {"nrCycles": 100000, "dod": 10.0},
                            {"nrCycles": 100000, "dod": 15.0},
                            {"nrCycles": 100000, "dod": 20.0},
                            {"nrCycles": 100000, "dod": 25.0},
                            {"nrCycles": 100000, "dod": 30.0},
                            {"nrCycles": 100000, "dod": 35.0},
                            {"nrCycles": 100000, "dod": 40.0},
                            {"nrCycles": 100000, "dod": 45.0},
                            {"nrCycles": 100000, "dod": 50.0},
                            {"nrCycles": 100000, "dod": 55.0},
                            {"nrCycles": 100000, "dod": 60.0},
                            {"nrCycles": 100000, "dod": 65.0},
                            {"nrCycles": 100000, "dod": 70.0},
                            {"nrCycles": 100000, "dod": 75.0},
                            {"nrCycles": 20000, "dod": 80.0},
                            {"nrCycles": 20000, "dod": 85.0},
                            {"nrCycles": 20000, "dod": 90.0},
                            {"nrCycles": 19600, "dod": 95.0},
                            {"nrCycles": 19500, "dod": 100.0}
                        ]
    """

    bess_deg_curve_Vanadium = [

        {"nrCycles": 100000, "dod": 10.0},
        {"nrCycles": 85000, "dod": 25.0},
        {"nrCycles": 60000, "dod": 50.0},
        {"nrCycles": 35000, "dod": 75.0},
        {"nrCycles": 20000, "dod": 80.0},
        {"nrCycles": 10000, "dod": 100.0}
    ]

    bess_deg_curve_Lead_Acid = [

        {"nrCycles": 10000, "dod": 10.0},
        {"nrCycles": 5000, "dod": 25.0},
        {"nrCycles": 2400, "dod": 50.0},
        {"nrCycles": 1200, "dod": 75.0},
        {"nrCycles": 800, "dod": 100.0}
    ]

    bess_deg_curve_NaS = [

        {"nrCycles": 40000, "dod": 10.0},
        {"nrCycles": 10000, "dod": 25.0},
        {"nrCycles": 7000, "dod": 50.0},
        {"nrCycles": 4500, "dod": 75.0},
        {"nrCycles": 2500, "dod": 100.0}
    ]

    bess_deg_curve_Supercaps = [

        {"nrCycles": 1000000, "dod": 10.0},
        {"nrCycles": 750000, "dod": 25.0},
        {"nrCycles": 600000, "dod": 50.0},
        {"nrCycles": 450000, "dod": 75.0},
        {"nrCycles": 300000, "dod": 100.0}
    ]

    bess_deg_curve_NiCd = [

        {"nrCycles": 40000, "dod": 10.0},
        {"nrCycles": 20000, "dod": 25.0},
        {"nrCycles": 10000, "dod": 50.0},
        {"nrCycles": 7000, "dod": 75.0},
        {"nrCycles": 2000, "dod": 100.0}
    ]


    bess_deg_curve_Flywheel = [

        {"nrCycles": 200000, "dod": 10.0},
        {"nrCycles": 50000, "dod": 25.0},
        {"nrCycles": 40000, "dod": 50.0},
        {"nrCycles": 30000, "dod": 75.0},
        {"nrCycles": 20000, "dod": 100.0}
    ]

    if bess_deg_curve == 1:
        #bess_deg_curve = bess_deg_curve1
        bess_deg_curve = bess_deg_curve_lithium
        bess_ch_eff = 95
        bess_disch_eff = 95
        k1 = 546
        C1 = 297
        #C1 = 0.300


    else:
        if bess_deg_curve == 2:
            bess_deg_curve = bess_deg_curve_Vanadium
            bess_ch_eff = 75
            bess_disch_eff = 75
            k1 = 307
            C1 = 165.5
            #C1 = 0.385


        if bess_deg_curve == 3:
            bess_deg_curve = bess_deg_curve_Lead_Acid
            bess_ch_eff = 75
            bess_disch_eff = 75
            k1 = 437
            C1 = 455

        if bess_deg_curve == 4:
            bess_deg_curve = bess_deg_curve_NiCd
            bess_ch_eff = 60
            bess_disch_eff = 60
            k1 = 699
            C1 = 1

        if bess_deg_curve == 5:
            bess_deg_curve = bess_deg_curve_NaS
            bess_ch_eff = 80
            bess_disch_eff = 80
            K1 = 343
            C1 = 569

        if bess_deg_curve == 6:
            bess_deg_curve = bess_deg_curve_Flywheel
            bess_ch_eff = 93
            bess_disch_eff = 93
            K1 = 4791
            C1 = 159

        if bess_deg_curve == 7:
            bess_deg_curve = bess_deg_curve_Supercaps
            bess_ch_eff = 95
            bess_disch_eff = 95
            k1 = 765
            C1= 416

    if bess_deg_curve2 == 1:
        bess_deg_curve2 = bess_deg_curve_lithium
        bess_ch_eff2 = 85
        bess_disch_eff2 = 85
        k2 = 546
        C2 = 297

    else:
        if bess_deg_curve2 == 2:
            bess_deg_curve2 = bess_deg_curve_Vanadium
            bess_ch_eff2 = 85
            bess_disch_eff2 = 85
            k2 = 307
            C2 = 165.5

        if bess_deg_curve2 == 3:
            bess_deg_curve2 = bess_deg_curve_Lead_Acid
            bess_ch_eff2 = 75
            bess_disch_eff2 = 75
            k2 = 437
            C2 = 455


        if bess_deg_curve2 == 4:
            bess_deg_curve2 = bess_deg_curve_NiCd
            bess_ch_eff2 = 60
            bess_disch_eff2 = 60
            k2 = 699
            C2 = 1

        if bess_deg_curve2 == 5:
            bess_deg_curve2 = bess_deg_curve_NaS
            bess_ch_eff2 = 80
            bess_disch_eff2 = 80
            k2 = 343
            C2 = 569

        if bess_deg_curve2 == 6:
            bess_deg_curve2 = bess_deg_curve_Flywheel
            bess_ch_eff2 = 93
            bess_disch_eff2 = 93
            k2 = 4791
            C2 = 159

        if bess_deg_curve2 == 7:
            bess_deg_curve2 = bess_deg_curve_Supercaps
            bess_ch_eff2 = 95
            bess_disch_eff2 = 95
            k2 = 765
            C2 = 416

    bess_test_data = {
                            "addOnSoc": add_on_soc,
                            'betterEffApprox': add_on_inv,
                            'roundEffApprox': add_on_inv,
                            "effD": [
                                {"trial": 1, "cRate": 0.11, "effDchAvg": 99.14},
                                {"trial": 1, "cRate": 0.19, "effDchAvg": 99.53},
                                {"trial": 1, "cRate": 0.41, "effDchAvg": 98.39},
                                {"trial": 1, "cRate": 0.48, "effDchAvg": 99.56},
                                {"trial": 1, "cRate": 0.61, "effDchAvg": 97.07},
                                {"trial": 1, "cRate": 0.73, "effDchAvg": 99.11},
                                {"trial": 1, "cRate": 0.82, "effDchAvg": 96.83},
                                {"trial": 1, "cRate": 0.93, "effDchAvg": 97.16},
                                {"trial": 2, "cRate": 0.12, "effDchAvg": 99.12},
                                {"trial": 2, "cRate": 0.21, "effDchAvg": 99.09},
                                {"trial": 2, "cRate": 0.41, "effDchAvg": 99.40},
                                {"trial": 2, "cRate": 0.48, "effDchAvg": 99.39},
                                {"trial": 2, "cRate": 0.59, "effDchAvg": 99.30},
                                {"trial": 2, "cRate": 0.72, "effDchAvg": 99.90},
                                {"trial": 2, "cRate": 0.81, "effDchAvg": 99.28},
                                {"trial": 2, "cRate": 0.92, "effDchAvg": 98.76}
                            ],
                            "roundEff": [
                                {"trial": 1, "cRate": 0.1, "roundEffAvg": 98.27},
                                {"trial": 1, "cRate": 0.2, "roundEffAvg": 96.95},
                                {"trial": 1, "cRate": 0.4, "roundEffAvg": 94.48},
                                {"trial": 1, "cRate": 0.5, "roundEffAvg": 95.12},
                                {"trial": 1, "cRate": 0.6, "roundEffAvg": 94.36},
                                {"trial": 1, "cRate": 0.7, "roundEffAvg": 93.58},
                                {"trial": 1, "cRate": 0.8, "roundEffAvg": 93.61},
                                {"trial": 1, "cRate": 0.9, "roundEffAvg": 92.68},
                                {"trial": 2, "cRate": 0.1, "roundEffAvg": 97.07},
                                {"trial": 2, "cRate": 0.2, "roundEffAvg": 95.99},
                                {"trial": 2, "cRate": 0.4, "roundEffAvg": 95.94},
                                {"trial": 2, "cRate": 0.5, "roundEffAvg": 95.58},
                                {"trial": 2, "cRate": 0.6, "roundEffAvg": 92.62},
                                {"trial": 2, "cRate": 0.7, "roundEffAvg": 95.36},
                                {"trial": 2, "cRate": 0.8, "roundEffAvg": 91.90},
                                {"trial": 2, "cRate": 0.9, "roundEffAvg": 94.06}
                            ],
                            "vNomD": [
                                {"trial": 1, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 1, "cRate": 0.11, "vAvg": 723.21},
                                {"trial": 1, "cRate": 0.19, "vAvg": 720.01},
                                {"trial": 1, "cRate": 0.30, "vAvg": 713.03},
                                {"trial": 1, "cRate": 0.41, "vAvg": 713.34},
                                {"trial": 1, "cRate": 0.48, "vAvg": 710.74},
                                {"trial": 1, "cRate": 0.61, "vAvg": 716.41},
                                {"trial": 1, "cRate": 0.73, "vAvg": 710.99},
                                {"trial": 1, "cRate": 0.82, "vAvg": 711.79},
                                {"trial": 1, "cRate": 0.93, "vAvg": 715.84},
                                {"trial": 2, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 2, "cRate": 0.12, "vAvg": 723.21},
                                {"trial": 2, "cRate": 0.21, "vAvg": 717.71},
                                {"trial": 2, "cRate": 0.41, "vAvg": 709.42},
                                {"trial": 2, "cRate": 0.48, "vAvg": 707.13},
                                {"trial": 2, "cRate": 0.59, "vAvg": 720.05},
                                {"trial": 2, "cRate": 0.72, "vAvg": 714.82},
                                {"trial": 2, "cRate": 0.81, "vAvg": 707.93},
                                {"trial": 2, "cRate": 0.92, "vAvg": 712.86}
                            ],
                            "vNomC": [
                                {"trial": 1, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 1, "cRate": 0.11, "vAvg": 742.43},
                                {"trial": 1, "cRate": 0.21, "vAvg": 749.52},
                                {"trial": 1, "cRate": 0.30, "vAvg": 741.82},
                                {"trial": 1, "cRate": 0.40, "vAvg": 750.33},
                                {"trial": 1, "cRate": 0.47, "vAvg": 750.80},
                                {"trial": 1, "cRate": 0.62, "vAvg": 757.67},
                                {"trial": 1, "cRate": 0.72, "vAvg": 750.08},
                                {"trial": 1, "cRate": 0.78, "vAvg": 750.91},
                                {"trial": 1, "cRate": 0.87, "vAvg": 767.71},
                                {"trial": 2, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 2, "cRate": 0.12, "vAvg": 745.57},
                                {"trial": 2, "cRate": 0.21, "vAvg": 742.42},
                                {"trial": 2, "cRate": 0.30, "vAvg": 740.32},
                                {"trial": 2, "cRate": 0.40, "vAvg": 748.53},
                                {"trial": 2, "cRate": 0.46, "vAvg": 749.94},
                                {"trial": 2, "cRate": 0.62, "vAvg": 747.81},
                                {"trial": 2, "cRate": 0.70, "vAvg": 758.26},
                                {"trial": 2, "cRate": 0.80, "vAvg": 749.79},
                                {"trial": 2, "cRate": 0.86, "vAvg": 764.99}
                            ],
                            "cLim": [
                                {"trial": 1, "cRate": 0.11, "eRemain": 99.14},
                                {"trial": 1, "cRate": 0.21, "eRemain": 97.48},
                                {"trial": 1, "cRate": 0.40, "eRemain": 96.24},
                                {"trial": 1, "cRate": 0.47, "eRemain": 95.75},
                                {"trial": 1, "cRate": 0.62, "eRemain": 97.36},
                                {"trial": 1, "cRate": 0.72, "eRemain": 94.76},
                                {"trial": 1, "cRate": 0.78, "eRemain": 96.88},
                                {"trial": 1, "cRate": 0.87, "eRemain": 95.72},
                                {"trial": 2, "cRate": 0.12, "eRemain": 97.98},
                                {"trial": 2, "cRate": 0.21, "eRemain": 96.85},
                                {"trial": 2, "cRate": 0.40, "eRemain": 96.66},
                                {"trial": 2, "cRate": 0.46, "eRemain": 96.33},
                                {"trial": 2, "cRate": 0.62, "eRemain": 93.76},
                                {"trial": 2, "cRate": 0.70, "eRemain": 95.66},
                                {"trial": 2, "cRate": 0.80, "eRemain": 93.13},
                                {"trial": 2, "cRate": 0.86, "eRemain": 95.51}
                            ],
                            "dLim": [
                                {"trial": 1, "cRate": 0.11, "eRemain": 0.86},
                                {"trial": 1, "cRate": 0.19, "eRemain": 0.47},
                                {"trial": 1, "cRate": 0.41, "eRemain": 1.61},
                                {"trial": 1, "cRate": 0.48, "eRemain": 0.44},
                                {"trial": 1, "cRate": 0.61, "eRemain": 2.93},
                                {"trial": 1, "cRate": 0.73, "eRemain": 0.89},
                                {"trial": 1, "cRate": 0.82, "eRemain": 3.17},
                                {"trial": 1, "cRate": 0.93, "eRemain": 2.84},
                                {"trial": 2, "cRate": 0.12, "eRemain": 0.88},
                                {"trial": 2, "cRate": 0.21, "eRemain": 0.91},
                                {"trial": 2, "cRate": 0.41, "eRemain": 0.60},
                                {"trial": 2, "cRate": 0.48, "eRemain": 0.61},
                                {"trial": 2, "cRate": 0.59, "eRemain": 0.70},
                                {"trial": 2, "cRate": 0.72, "eRemain": 0.10},
                                {"trial": 2, "cRate": 0.81, "eRemain": 0.72},
                                {"trial": 2, "cRate": 0.92, "eRemain": 1.24}
                            ],
                            "effC": [
                                {"trial": 1, "cRate": 0.11, "effChAvg": 99.14},
                                {"trial": 1, "cRate": 0.21, "effChAvg": 97.48},
                                {"trial": 1, "cRate": 0.40, "effChAvg": 96.24},
                                {"trial": 1, "cRate": 0.47, "effChAvg": 95.75},
                                {"trial": 1, "cRate": 0.62, "effChAvg": 97.36},
                                {"trial": 1, "cRate": 0.72, "effChAvg": 94.76},
                                {"trial": 1, "cRate": 0.78, "effChAvg": 96.88},
                                {"trial": 1, "cRate": 0.87, "effChAvg": 95.72},
                                {"trial": 2, "cRate": 0.12, "effChAvg": 97.98},
                                {"trial": 2, "cRate": 0.21, "effChAvg": 96.85},
                                {"trial": 2, "cRate": 0.40, "effChAvg": 96.66},
                                {"trial": 2, "cRate": 0.46, "effChAvg": 96.33},
                                {"trial": 2, "cRate": 0.62, "effChAvg": 93.76},
                                {"trial": 2, "cRate": 0.70, "effChAvg": 95.66},
                                {"trial": 2, "cRate": 0.80, "effChAvg": 93.13},
                                {"trial": 2, "cRate": 0.86, "effChAvg": 95.51}
                            ]
                        }

    bess_test_data2 = {
                            "addOnSoc": add_on_soc,
                            'betterEffApprox': add_on_inv,
                            'roundEffApprox': add_on_inv,
                            "effD": [
                                {"trial": 1, "cRate": 0.11, "effDchAvg": 99.14},
                                {"trial": 1, "cRate": 0.19, "effDchAvg": 99.53},
                                {"trial": 1, "cRate": 0.41, "effDchAvg": 98.39},
                                {"trial": 1, "cRate": 0.48, "effDchAvg": 99.56},
                                {"trial": 1, "cRate": 0.61, "effDchAvg": 97.07},
                                {"trial": 1, "cRate": 0.73, "effDchAvg": 99.11},
                                {"trial": 1, "cRate": 0.82, "effDchAvg": 96.83},
                                {"trial": 1, "cRate": 0.93, "effDchAvg": 97.16},
                                {"trial": 2, "cRate": 0.12, "effDchAvg": 99.12},
                                {"trial": 2, "cRate": 0.21, "effDchAvg": 99.09},
                                {"trial": 2, "cRate": 0.41, "effDchAvg": 99.40},
                                {"trial": 2, "cRate": 0.48, "effDchAvg": 99.39},
                                {"trial": 2, "cRate": 0.59, "effDchAvg": 99.30},
                                {"trial": 2, "cRate": 0.72, "effDchAvg": 99.90},
                                {"trial": 2, "cRate": 0.81, "effDchAvg": 99.28},
                                {"trial": 2, "cRate": 0.92, "effDchAvg": 98.76}
                            ],
                            "roundEff": [
                                {"trial": 1, "cRate": 0.1, "roundEffAvg": 98.27},
                                {"trial": 1, "cRate": 0.2, "roundEffAvg": 96.95},
                                {"trial": 1, "cRate": 0.4, "roundEffAvg": 94.48},
                                {"trial": 1, "cRate": 0.5, "roundEffAvg": 95.12},
                                {"trial": 1, "cRate": 0.6, "roundEffAvg": 94.36},
                                {"trial": 1, "cRate": 0.7, "roundEffAvg": 93.58},
                                {"trial": 1, "cRate": 0.8, "roundEffAvg": 93.61},
                                {"trial": 1, "cRate": 0.9, "roundEffAvg": 92.68},
                                {"trial": 2, "cRate": 0.1, "roundEffAvg": 97.07},
                                {"trial": 2, "cRate": 0.2, "roundEffAvg": 95.99},
                                {"trial": 2, "cRate": 0.4, "roundEffAvg": 95.94},
                                {"trial": 2, "cRate": 0.5, "roundEffAvg": 95.58},
                                {"trial": 2, "cRate": 0.6, "roundEffAvg": 92.62},
                                {"trial": 2, "cRate": 0.7, "roundEffAvg": 95.36},
                                {"trial": 2, "cRate": 0.8, "roundEffAvg": 91.90},
                                {"trial": 2, "cRate": 0.9, "roundEffAvg": 94.06}
                            ],
                            "vNomD": [
                                {"trial": 1, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 1, "cRate": 0.11, "vAvg": 723.21},
                                {"trial": 1, "cRate": 0.19, "vAvg": 720.01},
                                {"trial": 1, "cRate": 0.30, "vAvg": 713.03},
                                {"trial": 1, "cRate": 0.41, "vAvg": 713.34},
                                {"trial": 1, "cRate": 0.48, "vAvg": 710.74},
                                {"trial": 1, "cRate": 0.61, "vAvg": 716.41},
                                {"trial": 1, "cRate": 0.73, "vAvg": 710.99},
                                {"trial": 1, "cRate": 0.82, "vAvg": 711.79},
                                {"trial": 1, "cRate": 0.93, "vAvg": 715.84},
                                {"trial": 2, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 2, "cRate": 0.12, "vAvg": 723.21},
                                {"trial": 2, "cRate": 0.21, "vAvg": 717.71},
                                {"trial": 2, "cRate": 0.41, "vAvg": 709.42},
                                {"trial": 2, "cRate": 0.48, "vAvg": 707.13},
                                {"trial": 2, "cRate": 0.59, "vAvg": 720.05},
                                {"trial": 2, "cRate": 0.72, "vAvg": 714.82},
                                {"trial": 2, "cRate": 0.81, "vAvg": 707.93},
                                {"trial": 2, "cRate": 0.92, "vAvg": 712.86}
                            ],
                            "vNomC": [
                                {"trial": 1, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 1, "cRate": 0.11, "vAvg": 742.43},
                                {"trial": 1, "cRate": 0.21, "vAvg": 749.52},
                                {"trial": 1, "cRate": 0.30, "vAvg": 741.82},
                                {"trial": 1, "cRate": 0.40, "vAvg": 750.33},
                                {"trial": 1, "cRate": 0.47, "vAvg": 750.80},
                                {"trial": 1, "cRate": 0.62, "vAvg": 757.67},
                                {"trial": 1, "cRate": 0.72, "vAvg": 750.08},
                                {"trial": 1, "cRate": 0.78, "vAvg": 750.91},
                                {"trial": 1, "cRate": 0.87, "vAvg": 767.71},
                                {"trial": 2, "cRate": 0.00, "vAvg": 736.00},
                                {"trial": 2, "cRate": 0.12, "vAvg": 745.57},
                                {"trial": 2, "cRate": 0.21, "vAvg": 742.42},
                                {"trial": 2, "cRate": 0.30, "vAvg": 740.32},
                                {"trial": 2, "cRate": 0.40, "vAvg": 748.53},
                                {"trial": 2, "cRate": 0.46, "vAvg": 749.94},
                                {"trial": 2, "cRate": 0.62, "vAvg": 747.81},
                                {"trial": 2, "cRate": 0.70, "vAvg": 758.26},
                                {"trial": 2, "cRate": 0.80, "vAvg": 749.79},
                                {"trial": 2, "cRate": 0.86, "vAvg": 764.99}
                            ],
                            "cLim": [
                                {"trial": 1, "cRate": 0.11, "eRemain": 99.14},
                                {"trial": 1, "cRate": 0.21, "eRemain": 97.48},
                                {"trial": 1, "cRate": 0.40, "eRemain": 96.24},
                                {"trial": 1, "cRate": 0.47, "eRemain": 95.75},
                                {"trial": 1, "cRate": 0.62, "eRemain": 97.36},
                                {"trial": 1, "cRate": 0.72, "eRemain": 94.76},
                                {"trial": 1, "cRate": 0.78, "eRemain": 96.88},
                                {"trial": 1, "cRate": 0.87, "eRemain": 95.72},
                                {"trial": 2, "cRate": 0.12, "eRemain": 97.98},
                                {"trial": 2, "cRate": 0.21, "eRemain": 96.85},
                                {"trial": 2, "cRate": 0.40, "eRemain": 96.66},
                                {"trial": 2, "cRate": 0.46, "eRemain": 96.33},
                                {"trial": 2, "cRate": 0.62, "eRemain": 93.76},
                                {"trial": 2, "cRate": 0.70, "eRemain": 95.66},
                                {"trial": 2, "cRate": 0.80, "eRemain": 93.13},
                                {"trial": 2, "cRate": 0.86, "eRemain": 95.51}
                            ],
                            "dLim": [
                                {"trial": 1, "cRate": 0.11, "eRemain": 0.86},
                                {"trial": 1, "cRate": 0.19, "eRemain": 0.47},
                                {"trial": 1, "cRate": 0.41, "eRemain": 1.61},
                                {"trial": 1, "cRate": 0.48, "eRemain": 0.44},
                                {"trial": 1, "cRate": 0.61, "eRemain": 2.93},
                                {"trial": 1, "cRate": 0.73, "eRemain": 0.89},
                                {"trial": 1, "cRate": 0.82, "eRemain": 3.17},
                                {"trial": 1, "cRate": 0.93, "eRemain": 2.84},
                                {"trial": 2, "cRate": 0.12, "eRemain": 0.88},
                                {"trial": 2, "cRate": 0.21, "eRemain": 0.91},
                                {"trial": 2, "cRate": 0.41, "eRemain": 0.60},
                                {"trial": 2, "cRate": 0.48, "eRemain": 0.61},
                                {"trial": 2, "cRate": 0.59, "eRemain": 0.70},
                                {"trial": 2, "cRate": 0.72, "eRemain": 0.10},
                                {"trial": 2, "cRate": 0.81, "eRemain": 0.72},
                                {"trial": 2, "cRate": 0.92, "eRemain": 1.24}
                            ],
                            "effC": [
                                {"trial": 1, "cRate": 0.11, "effChAvg": 99.14},
                                {"trial": 1, "cRate": 0.21, "effChAvg": 97.48},
                                {"trial": 1, "cRate": 0.40, "effChAvg": 96.24},
                                {"trial": 1, "cRate": 0.47, "effChAvg": 95.75},
                                {"trial": 1, "cRate": 0.62, "effChAvg": 97.36},
                                {"trial": 1, "cRate": 0.72, "effChAvg": 94.76},
                                {"trial": 1, "cRate": 0.78, "effChAvg": 96.88},
                                {"trial": 1, "cRate": 0.87, "effChAvg": 95.72},
                                {"trial": 2, "cRate": 0.12, "effChAvg": 97.98},
                                {"trial": 2, "cRate": 0.21, "effChAvg": 96.85},
                                {"trial": 2, "cRate": 0.40, "effChAvg": 96.66},
                                {"trial": 2, "cRate": 0.46, "effChAvg": 96.33},
                                {"trial": 2, "cRate": 0.62, "effChAvg": 93.76},
                                {"trial": 2, "cRate": 0.70, "effChAvg": 95.66},
                                {"trial": 2, "cRate": 0.80, "effChAvg": 93.13},
                                {"trial": 2, "cRate": 0.86, "effChAvg": 95.51}
                            ]
                        }
