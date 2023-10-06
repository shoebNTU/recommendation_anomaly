import pandas as pd
import streamlit as st
import numpy as np
import io

st.sidebar.title('Anomaly simulation')

# read template file
template = pd.read_excel('template.xlsx',header=None)
measurement_types = template.iloc[15,:].to_list()

# remove battery volts
measurements_considered = measurement_types[:]
measurements_considered.remove('Battery Volts')

no_of_points = st.sidebar.number_input(value=1000,label='No. of measurement points')
measurement_type = st.sidebar.selectbox('Select measurement type',measurements_considered[1:-2])

distance = np.arange(no_of_points)
measurement = np.zeros((no_of_points,len(measurement_types[:-2]))) #ignore last two columns
measurement[:,0] = distance

c1, c2, _ = st.columns(3)
with c1:
    no_of_anomalies = st.number_input(label='Enter number of anomalies',value=1)

with c2:
    file_name = st.text_input(value='scenario.xlsx',label='Please enter filename ending in xlsx')

c1, c2, c3 = st.columns(3)
anomaly_start_pos = []
anomaly_end_pos = []
anomaly_value = []

for anomaly_no in range(no_of_anomalies):
    with c1:
        start_pos = st.number_input('start_pos',value=0.0,min_value=0.0, key=f'anomaly_start_{anomaly_no}')
        anomaly_start_pos.append(start_pos)
    with c2:
        end_pos = st.number_input('end_pos',value=1.0*np.max(distance), step=1.0,key=f'anomaly_end_{anomaly_no}')
        anomaly_end_pos.append(end_pos)
    with c3:
        value = st.number_input('value',value=0.0,min_value=0.0,key=f'anomaly_val_{anomaly_no}')
        anomaly_value.append(value)


if st.button('Get Data'):
    measurement_index = measurement_types.index(measurement_type)

    for i in range(no_of_anomalies):
        indices = np.where((distance >= anomaly_start_pos[i]) & (distance <= anomaly_end_pos[i]))
        measurement[indices,measurement_index] = anomaly_value[i]   
    

    alarms = pd.DataFrame(measurement,columns=measurement_types[:-2])
    col_names  = ['distance','Switch Blade LH','Switch Blade RH',
 'Top Left',
 'Top Right',
 'Versine Left',
 'Versine Right']
    alarms_col = alarms[col_names]
    alarms_to_save = alarms_col.melt(id_vars=['distance'],var_name='Channel')
    alarms_to_save.rename(columns={'distance':'Meters'},inplace=True)
    alarms_to_save['High/Low'] = 'Low'
    alarms_to_save = alarms_to_save[['Channel','Meters','High/Low','value']]

    simulated_data = pd.concat([template.iloc[:16,:],pd.DataFrame(measurement),
                                template.iloc[16:,:],pd.DataFrame(np.array(alarms_to_save))],ignore_index=True)
    st.write(simulated_data)

    buffer = io.BytesIO()
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        simulated_data.to_excel(writer, sheet_name='in', index=None, header=None)
   
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.close()

        st.download_button(
            label="Download Excel worksheets",
            data=buffer,
            file_name=file_name,
            mime="application/vnd.ms-excel"
        )