from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from main import optimize,read_data
import main
import datetime as dt
import pandas as pd
from helpers.set_loggers import *
from settings.general_settings import GeneralSettings
from time import time
from fastapi.responses import JSONResponse

app = FastAPI()

# Configuração do CORS
origins = [
    "http://127.0.0.1:8050",
    "http://localhost",
    "http://localhost:8050",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bess_asset = {
        'actualENom': [],
        'chEff': GeneralSettings.bess_ch_eff,
        'degCurve': GeneralSettings.bess_deg_curve,
        'dischEff': GeneralSettings.bess_disch_eff,
        'eNom': [],
        'eolCriterion': GeneralSettings.bess_eol_criterion,
        'invMaxIDC': GeneralSettings.bess_inv_max_idc,
        'invSNom': GeneralSettings.bess_inv_s_nom,
        'invVNom': GeneralSettings.bess_inv_v_nom,
        'maxCCh': GeneralSettings.bess_max_c_ch,
        'maxCDch': GeneralSettings.bess_max_c_disch,
        'maxSoc': [],
        'minPCh': GeneralSettings.bess_min_p_ch,
        'minPDch': GeneralSettings.bess_min_p_disch,
        'minSoc': GeneralSettings.bess_min_soc,
        'reserveSoc': GeneralSettings.bess_reserve_soc,
        'testData': main.original_test_data,
        'vNom': GeneralSettings.bess_v_nom,
    }

@app.post("/api/objective_function")
async def objective_function(selected_option: str = Form(...)):

    a = selected_option
    print(a)

@app.post("/api/settings")
async def settings(input_value: float = Form(...), table_data: list = Form(...)):

    bess_asset['maxSoc'] = input_value
    bess_asset['actualENom'] = input_value
    bess_asset['eNom'] = input_value
    z = table_data
    step = GeneralSettings.step
    read_data(table_data, step)
    print(z)

@app.post("/api/teste")
async def teste(selected_option: str = Form(...), input_value: float = Form(...)):

    a = selected_option
    print(a)



    t0 = time()
    prob_obj = optimize(main.settings, bess_asset, main.bess_asset2, main.milp_params, main.measures, main.measures2, main.forecasts_and_other_arrays, a)
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
    if main.daily_outputs is not None:
        main.daily_outputs = main.daily_outputs.append(df)
    else:
        main.daily_outputs = df

    status = prob_obj.stat
    logger.warning(f'{status}')
    main.expected_revenues += pd.DataFrame(outputs.get('expectRevs')).sum().get('setpoint')
    main.last_soc += pd.DataFrame(outputs['eBess']).loc[prob_obj.time_intervals - 1, 'setpoint']
    main.last_soc2 += pd.DataFrame(outputs['eBess2']).loc[prob_obj.time_intervals - 1, 'setpoint']
    main.degradation += pd.DataFrame(outputs['eDeg']).sum().get('setpoint')
    main.degradation2 += pd.DataFrame(outputs['eDeg2']).sum().get('setpoint')
    main.total_degradation += pd.DataFrame(outputs.get('Totaldeg')).sum().get('setpoint')
    main.total += pd.DataFrame(outputs.get('Total')).sum().get('setpoint')
    main.first_dt_text = dt.datetime.strftime(main.first_dt, '%Y-%m-%d %H:%M:%S')

    with open(f'{prob_obj.common_fname}-pulp.sol', newline='\n') as csvfile:
        init_text = csvfile.read(50)
        status_real = init_text.split(sep=' - ')[0]

    # Clean unnecessary files from "core" folder
    prob_obj.final_folder_cleaning()

    main.final_outputs['datetime'].append(main.first_dt_text)
    main.final_outputs['status'].append(status)
    main.final_outputs['status_real'].append(status_real)
    main.final_outputs['expected_revenues'].append(main.expected_revenues)
    main.final_outputs['degradation'].append(main.degradation)
    main.final_outputs['degradation2'].append(main.degradation2)
    main.final_outputs['total_degradation'].append(main.total_degradation)
    main.final_outputs['total'].append(main.total)
    main.final_outputs['last_soc'].append(main.last_soc)
    main.final_outputs['time'].append(t1)

    logger.info(f' * Day {main.iteration} of {main.total_iter} ... OK! ({main.iter_time - time():.3f}s) * ')

    main.daily_outputs.to_csv(rf'outputs/{prob_obj.common_fname}_setpoints.csv',
                         sep=';', decimal=',', index=True)
    pd.DataFrame(main.final_outputs).to_csv(rf'outputs/{prob_obj.common_fname}_main_outputs.csv',
                                       sep=';', decimal=',', index=True)

    # Remove the log file handler
    remove_logfile_handler(main.logfile_handler_id)

    # Get the needed outputs
    print(a)
    print(main.daily_outputs)


@app.get("/api/get_data_for_chart")
async def get_data_for_chart():
    data = list(main.final_outputs)
    data2 = main.daily_outputs
    return JSONResponse(content={"data": list(data)})"""