import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import urllib.request as request

# data proprocess
# r = request.urlopen("https://raw.githubusercontent.com/founting/votes/master/votings.csv")
data = pd.read_csv("MotiesLast31Days.csv")
topics = np.unique(data['topic'])
parties = np.unique(data['ActorFractie'])
moties = np.unique(data['Id'])

tdist = []
propose = []
pvotes = []
proposers = []
correlation = [parties.tolist()]
temp = []

for p in parties:
    for m in moties:
        temp.append([m, p])
    proposers.append([p, 0])

for i in range(data.shape[0]):
    if [data.loc[i]['Id'], parties[0]] in temp:
        correlation.append([])
        # tdist
        t = data.loc[i]['topic']
        d = data.loc[i]['decision']
        if d == 1:
            tdist.append([t, 1, 0])
        else:
            tdist.append([t, 0, 1])
        # propose
        proposer = data.loc[i]['IndienerFractie']
        propose.append([proposer, t, 1])

        proposeParty = data.loc[i]['IndienerFractie']
        proposersIndex = [i for i, x in enumerate(proposers) if x[0] == proposeParty][0]
        proposers[proposersIndex][1] += 1
    af = data.loc[i]['ActorFractie']
    # pvotes
    if [data.loc[i]['Id'], af] in temp:
        sv = data.loc[i]['StemmenVoor']
        st = data.loc[i]['StemmenTegen']
        if sv > 0 and sv > st:
            pvotes.append([af, t, 'support', 1])
            correlation[-1].append(1)
        elif st > 0 and st > sv:
            pvotes.append([af, t, 'against', 1])
            correlation[-1].append(0)
        temp.pop(temp.index([data.loc[i]['Id'], af]))

for t in topics:
    pvotes.append([parties[0], t, 'support', 0])
    pvotes.append([parties[0], t, 'against', 0])

# topic distribution
tdist = pd.DataFrame(tdist, columns=['topic', 'adopted', 'rejected'])
tdist = tdist.groupby('topic').sum().reset_index()

fig_td = go.Figure(
    data=[
        go.Bar(name='adopted', x=tdist['topic'], y=tdist['adopted'], base=0, marker_color='#87CE70'),
        go.Bar(name='rejected', x=tdist['topic'], y=-tdist['rejected'], base=0, marker_color='#d36e70')
    ],
    layout=go.Layout(
        title=dict(text='Topic distribution', x=0.5),
        xaxis=dict(),
        yaxis=dict(title='number of motions', gridcolor='#EEEEEE', zerolinecolor='#EEEEEE', tickformat='d'),
        bargap=0.5,
        barmode='stack',
        plot_bgcolor='#FFFFFF'
    )
)

# propose
propose = pd.DataFrame(propose, columns=['IndienerFractie', 'topic', 'pnum'])
propose = propose.groupby(['IndienerFractie', 'topic']).sum().reset_index()
propose = propose.pivot(index='IndienerFractie', columns='topic', values='pnum').fillna(0)

traces = []
for p in propose.index:
    traces.append(go.Scatterpolar(r=propose.loc[p], theta=propose.columns, fill='toself', name=p))
fig_pro = go.Figure(
    data=traces,
    layout=go.Layout(
        title=dict(text='Topic distribution of proposals of parties', x=0.5),
        polar=dict(radialaxis=dict(range=[0, 6.1], gridcolor='#C6C6C6', tickformat='d'),
                   angularaxis=dict(gridcolor='#C6C6C6'), bgcolor='#FFFFFF'),
        height=487
    ))

# pvotes
pvotes = pd.DataFrame(pvotes, columns=['party', 'topic', 'attitude', 'vnum'])
pvotes = pvotes.groupby(['party', 'topic', 'attitude'])['vnum'].sum().unstack('party').fillna(0)

fig_PVs = {}
for t in topics:
    fig_PVs[t] = go.Figure(
        data=[
            go.Bar(y=pvotes.columns, x=pvotes.loc[t, 'support'].values, name='in favour of', orientation='h',
                   marker_color='#A6C4FE'),
            go.Bar(y=pvotes.columns, x=pvotes.loc[t, 'against'].values, name='against', orientation='h',
                   marker_color='#DDDDDD')],
        layout=go.Layout(
            title=dict(text='Voting result regarding ' + str(t) + ' topic', x=0.5),
            xaxis=dict(title='number of motions', tickformat='d'),
            yaxis=dict(),
            # bargap=0.5,
            barmode='stack',
            plot_bgcolor='#FFFFFF',
            height=450
        )
    )

# correlations
headers = correlation.pop(0)
corr = pd.DataFrame(correlation, columns=headers).corr()
fig_corr = go.Figure(
    data=(
        go.Heatmap(
            zmin=-1,
            zmax=1,
            z=corr,
            x=parties,
            y=parties,
            colorscale='tealrose'
        )
    ),
    layout=go.Layout(
        title=dict(text='Correlation analysis between parties', x=0.5),
    )
)

# proposals per party
ps_x = []
ps_y = []
for i in proposers:
    ps_x.append(i[0])
    ps_y.append(i[1])
# plot fig5
fig_ps = go.Figure(
    data=[
        go.Bar(x=ps_x, y=ps_y, marker_color='#82CDBD')],
    layout=go.Layout(
        title=dict(text='Number of proposals per party', x=0.5),
        yaxis=dict(gridcolor='#EEEEEE', zerolinecolor='#EEEEEE', tickformat='d', dtick=200),
        plot_bgcolor='#FFFFFF',
        bargap=0.6,
    )
)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# html
app.layout = html.Div(children=[
    html.H1(children='Votes inside the Dutch Parliament',
            style={'width': '99%', 'height': 30, 'fontSize': 20, 'color': '#FFFFFF',
                   'paddingLeft': '1.5%', 'paddingTop': 5, 'backgroundColor': '#363880'}),

    html.Div([
        dcc.Graph(id='fig_td', figure=fig_td)],
        style={'width': '47%', 'marginTop': 10, 'marginLeft': '2%', 'display': 'inline-block',
               'vertical-align': 'top'}),

    html.Div([
        dcc.Graph(id='fig_corr', figure=fig_corr)],
        style={'width': '47%', 'marginTop': 10, 'marginLeft': '2%', 'marginRight': '2%', 'display': 'inline-block',
               'vertical-align': 'top'}),

    html.Div([
        dcc.Dropdown(
            id='figPV_dropdown',
            options=[{'label': i, 'value': i} for i in topics],
            value='Bestrijding internationaal terrorisme',
            style={'height': 37}),
        dcc.Graph(id='fig_pv')],
        style={'width': '47%', 'marginTop': 25, 'marginLeft': '2%', 'display': 'inline-block',
               'vertical-align': 'top'}),

    html.Div([
        dcc.Graph(id='fig_pro', figure=fig_pro)],
        style={'width': '47%', 'marginTop': 25, 'marginLeft': '2%', 'marginRight': '2%', 'display': 'inline-block',
               'vertical-align': 'top'}),

    html.Div([
        dcc.Graph(id='fig_ps', figure=fig_ps)],
        style={'width': '96%', 'height': 470, 'marginTop': 25, 'marginBottom': 15, 'marginLeft': '2%',
               'marginRight': '2%'})
],
    style={'backgroundColor': '#F6F6F6'})


@app.callback(
    Output('fig_pv', 'figure'),
    [Input('figPV_dropdown', 'value')])
def update_graph(t):
    return fig_PVs[t]


if __name__ == '__main__':
    app.run_server()
