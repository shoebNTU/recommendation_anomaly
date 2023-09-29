import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils_recommendation import (get_anomaly_recommendation,
                                  get_defect_recommendation)

st.sidebar.title("Anomaly and defect recommendations")

st.sidebar.title("Set simulation parameters")
min_percentage = st.sidebar.number_input('Anomaly/Defect Range [%]',value=50.0, min_value=0.0, max_value=100.0)/100.0
proximity = st.sidebar.number_input('Defect Proximity [m]',value=10.0, min_value=0.0)
min_severity_improvement = st.sidebar.number_input('SI Improvement [Number]',value=1, min_value=0, max_value=4)
min_overlap_extent = st.sidebar.number_input('Overlap Extent [m]',value=10.0, min_value=0.0)


st.subheader('Defect Simulation (Past Inspection)')
c1_no_of_defects,_,_ = st.columns(3)
with c1_no_of_defects:
    no_of_defects = st.number_input('Enter number of defects', value=1, max_value=5, min_value=0)

defect = pd.DataFrame(
    columns=[
        "defect_id",
        "defect_code_id",
        "line_id",
        "subsys_id",
        "payload_id",
        "measurement_type_id",
        "defect_status_id",
        "start_pos",
        "end_pos",
        "close_date_timestamp",
        "user",
        "modified_dttm",
    ]
)

anomaly = pd.DataFrame(
    columns=[
        "anomaly_id",
        "inspection_id",
        "measurement_type_id",
        "defect_code_id",
        "linked_defect_id",
        "review_status_id",
        "start_pos",
        "end_pos",
        "length",
        "user",
        "modified_dttm",
    ]
)

defect_start_pos = []
defect_end_pos = []
defect_severity = []
c1,c2,c3 = st.columns(3)
for defect_no in range(no_of_defects):
    with c1:
        start_pos = st.number_input('start_pos',value=0.0,min_value=0.0, key=f'defect_start_{defect_no}')
        defect_start_pos.append(start_pos)
    with c2:
        end_pos = st.number_input('end_pos',value=100.0, key=f'defect_end_{defect_no}')
        defect_end_pos.append(end_pos)
    with c3:
        severity = st.number_input('severity',value=2,min_value=1,max_value=4,key=f'defect_sev_{defect_no}')
        defect_severity.append(severity)

defect['start_pos'] = defect_start_pos
defect['end_pos'] = defect_end_pos
defect['defect_code_id'] = defect_severity
defect['defect_id'] = defect.index+1
st.write(defect)

st.subheader('Anomaly Simulation (Current Inspection)')

c1_no_of_anomalies,_, _ = st.columns(3)
with c1_no_of_anomalies:
    no_of_anomalies = st.number_input('Enter number of anomalies', value=1, max_value=5, min_value=0)

anomaly_start_pos = []
anomaly_end_pos = []
anomaly_severity = []
c1,c2,c3 = st.columns(3)
for anomaly_no in range(no_of_anomalies):
    with c1:
        start_pos = st.number_input('start_pos',value=0.0,min_value=0.0, key=f'anomaly_start_{anomaly_no}')
        anomaly_start_pos.append(start_pos)
    with c2:
        end_pos = st.number_input('end_pos',value=100.0,key=f'anomaly_end_{anomaly_no}')
        anomaly_end_pos.append(end_pos)
    with c3:
        severity = st.number_input('severity',value=2,min_value=1,max_value=4,key=f'anomaly_sev_{anomaly_no}')
        anomaly_severity.append(severity)

anomaly['start_pos'] = anomaly_start_pos
anomaly['end_pos'] = anomaly_end_pos
anomaly['defect_code_id'] = anomaly_severity
anomaly['anomaly_id'] = anomaly.index+1
anomaly['length'] = anomaly['end_pos'] - anomaly['start_pos']
st.write(anomaly)

line_width = 10
if st.button('Get recommendations'):

    no_of_scenarios = 1
    fig = make_subplots(
        rows=no_of_scenarios, cols=1,
        subplot_titles=['simulated scenario'])

    for scenario in range(1,no_of_scenarios+1):   
            
        anomaly_recommendation = get_anomaly_recommendation(anomaly, defect, proximity, min_percentage,min_severity_improvement, min_overlap_extent)
        defect_recommendation = get_defect_recommendation(anomaly_recommendation, defect)

        x_min = min(defect.start_pos.min(),anomaly.start_pos.min()) - proximity
        x_max = max(defect.end_pos.max(),anomaly.end_pos.max()) + proximity

    #     fig = go.Figure()
        count_of_traces = 0

        count_list_for_scatter = []
        for i, row in defect.iterrows():

            # Add a horizontal line with start and end points
            fig.add_shape(
                type='line',
                x0=row.start_pos,
                y0=count_of_traces,
                x1=row.end_pos,
                y1=count_of_traces,
                opacity = 0.25,
                line=dict(color='red', width=line_width),
                row=3*(scenario-1)+1,
                col=1
            )

            count_list_for_scatter.append(count_of_traces)
            count_of_traces = count_of_traces + 1

        # Add traces
        fig.add_trace(go.Scatter(x=defect.start_pos, y=count_list_for_scatter,
                            mode='markers',
                            name='defect', marker=dict(size=line_width,color='green',opacity=0)), row=3*(scenario-1)+1, col=1)
        # Add traces
        fig.add_trace(go.Scatter(x=defect.end_pos, y=count_list_for_scatter,
                            mode='markers',
                            name='defect', marker=dict(size=line_width,color='green',opacity=0)),row=3*(scenario-1)+1,col=1)
            # Add traces
        fig.add_trace(go.Scatter(x=defect.start_pos, y=count_list_for_scatter,
                            mode='text',
                            textfont=dict(color="black",size=18,family="Arail",),
                            text = defect.defect_code_id.apply(lambda x:'Sev-'+str(x)),
                            name='defect', marker=dict(size=line_width,color='purple')), row=3*(scenario-1)+1, col=1)

        count_list_for_scatter = []
        for i, row in anomaly.iterrows():

            # Add a horizontal line with start and end points
            fig.add_shape(
                type='line',
                x0=row.start_pos,
                y0=count_of_traces,
                x1=row.end_pos,
                y1=count_of_traces,
                opacity = 0.25,
                line=dict(color='blue', width=line_width),
                row=3*(scenario-1)+1,
                col=1
            )

            count_list_for_scatter.append(count_of_traces)
            count_of_traces = count_of_traces + 1

        # Add traces
        fig.add_trace(go.Scatter(x=anomaly.start_pos, y=count_list_for_scatter,
                            mode='markers',
                            name='anomaly', marker=dict(size=line_width,color='purple',opacity=0)), row=3*(scenario-1)+1, col=1)
        # Add traces
        fig.add_trace(go.Scatter(x=anomaly.end_pos, y=count_list_for_scatter,
                            mode='markers',
                            name='anomaly', marker=dict(size=line_width,color='purple',opacity=0)), row=3*(scenario-1)+1, col=1)
        # Add traces
        fig.add_trace(go.Scatter(x=anomaly.start_pos, y=count_list_for_scatter,
                            mode='text',
                            textfont=dict(color="black",size=18,family="Arail",),
                            text = anomaly.defect_code_id.apply(lambda x:'Sev-'+str(x)),
                            name='anomaly', marker=dict(size=line_width,color='purple')), row=3*(scenario-1)+1, col=1)
        
        #     

    # #     # Automatically adjust the x and y axis range
    # #     fig.update_layout(xaxis_range=[x_min-2*proximity, x_max+proximity], yaxis_range=[-2, count_of_traces+1])
    # # Hide the legends for each trace
        fig.update_traces(showlegend=False, row=3*(scenario-1)+1, col=1)

    # Add a title to the plot
    fig.update_layout(title="Different scenarios, Red Trace: Defect (past inspection), Blue Trace: Anomaly (current inspection)",
                    height=300*no_of_scenarios)
    fig.update_yaxes(showticklabels=False)
    fig.update_yaxes(autorange='reversed')
    st.plotly_chart(fig, use_container_width=True)

    st.info('Anomaly Recommendation')
    st.write(anomaly_recommendation)

    st.info('Defect Recommendation')
    st.write(defect_recommendation)








