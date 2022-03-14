import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.transforms import Bbox

from __const__ import tz

dat = pd.read_csv('samp_stations_cut.csv')

def dat_format(ds, site_lon, site_lat):
    _site_df = ds.sel(lon=site_lon, lat=site_lat, method='nearest').groupby('time').mean('ens', skipna=True).to_dataframe()
    _site_df = _site_df.tz_localize('utc').tz_convert(tz).between_time('7:00','18:00').reset_index()

    _data_reset = xr.Dataset.from_dataframe(_site_df.set_index('time'))
    _data_reset['time'] = _site_df['time'].dt.tz_localize(None).values

    _days = _data_reset.time.groupby('time.day').mean('time').day.values.tolist()
    dat_formatted = []
    for i in _days:
        if i == _days[0]:
            select  = np.insert(_data_reset.hi.sel(time=_data_reset.time.dt.day==i),0,0).fillna(0)
        else:
            select = _data_reset.hi.sel(time=_data_reset.time.dt.day==i).fillna(0)
        dat_formatted.append(select)

    return(dat_formatted)

def color(ds):
    _cols = []
    for i in ds.values:
        if 41 < i <= 54.0:
            _cols.append('red')
        elif i > 54.0:
            _cols.append('purple')
        elif i < 41.0:
            _cols.append('#EEEEEE')

    if len(_cols) == 12:
        _cols.append('white')
    else:
        new_col = ['#EEEEEE']*(12-len(_cols))+['white']
        _cols = _cols+new_col

    return _cols

def plot_gauge(ds,outdir):
    for i in range(len(dat['NAME'])):
        station_name = dat['NAME'][i]
        site_lat = dat['Latitude'][i]
        site_lon = dat['Longitude'][i]

        _sub_ds = dat_format(ds, site_lon, site_lat)

        
        _fname = ([_sub_ds[i].time.dt.strftime('%Y-%m-%d').isel(time=0).values.tolist() for i in range(len(_sub_ds[:3]))])
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))
        fig.suptitle(station_name+' Heat Index \n ('+_fname[0]+' to '+ _fname[2]+')', ha='center', y=0.95, fontsize=20)

        _dat = np.ones(12).tolist()
        _time = (pd.Series(pd.date_range('6:00', '18:00', freq='H')).dt.strftime("%-I %p").replace('12 PM','12 NOON')).tolist()
        _dat.append(12), _time.append("")
        
        _outer_colors = ['white']*13 
        _inner_colors = [color(_sub_ds[i]) for i in range(len(_sub_ds[:3]))]
        _size = 0.16

        _wedges, _text = ax.pie(_dat, radius = 0.95, colors=_outer_colors, counterclock=False, startangle=180, wedgeprops=dict(width= 0.45, edgecolor='w',  linewidth=0.6))

        ax.pie(_dat, radius=0.95, colors=_inner_colors[2],counterclock=False,startangle=180, wedgeprops=dict(width=0.15, edgecolor='w', linewidth=0.6))

        ax.pie(_dat, radius=0.95-_size, colors=_inner_colors[1],counterclock=False,startangle=180, wedgeprops=dict(width=0.16, edgecolor='w', linewidth=0.6))

        ax.pie(_dat, radius=(0.95-_size)-0.17, colors=_inner_colors[0],counterclock=False,startangle=180, wedgeprops=dict(width=0.15, edgecolor='w', linewidth=0.6))

        for i, p in enumerate(_wedges):
            y = np.sin(np.deg2rad(p.theta2))
            x = np.cos(np.deg2rad(p.theta2))

            if p.theta1 > 75:
                ax.annotate(_time[i], xy=(x,y), xytext=(0,0),textcoords='offset points', ha='right', va='center')

            elif round(p.theta1) == 75:
                ax.annotate(_time[i], xy=(x,y), xytext=(0,0),textcoords='offset points', ha='center', va='bottom')

            elif p.theta1 < 74:
                ax.annotate(_time[i], xy=(x,y), xytext=(0,0),textcoords='offset points', ha='left', va='center')

        day = ([_sub_ds[i].time.dt.strftime('%m-%d').isel(time=0).values.tolist() for i in np.arange(len(_sub_ds[:3]))])
        ax.text(x-0.37,y-0.3,"Day", fontweight = 'semibold')        
        ax.text(x-0.47,y-0.15,day[0], rotation='vertical')
        ax.text(x-0.32,y-0.15,day[1], rotation='vertical')
        ax.text(x-0.17,y-0.15,day[2], rotation='vertical')

        red, purple = mpatches.Patch(color='red', label='Danger'), mpatches.Patch(color='purple', label='Extreme Danger')
        plt.legend(handles=[red,purple],loc=10, bbox_to_anchor=(0.25, 0.1, 0.5, 0.5), ncol=2)

        fig.savefig(outdir+station_name+' WRF_HI_'+_fname[0]+'-'+_fname[2]+'.png', dpi=300, facecolor = None, bbox_inches = Bbox([[0,2.5],[8,8]]))

        plt.close()