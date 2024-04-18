import polyline
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString
from haversine import haversine, Unit
from utils.PreprocessingUtils import polylines_decoder

my_polyline = "_u}vHs_j|AsACjFkBASyWfGyBRsCBgIWaEY{BYuP{Dgh@yLeLcDwGmB{HqBea@{Ky^qKc\iJiPoEeSaG}H{AyBYyAM_GKuC@oCJkD\iEt@yA\cMtDcShGiEtA_QfFcFbAyEh@yCNmEB{CKuJ{@iRyBwDWeBI{EDqDTsEl@eFfAaBb@oBt@aBt@qYbOyq@h^m\|Pif@fWiItEONiAt@iYdOmA|@_A`AaArAeBlCqBnC}AtCsAhCmGfOk@dAQRYv@aAdB}BhD}BjC}@|@qDpC_E`CgCbAsBj@oWdFmOjCaGhAeHhBqDlAcEfBwR~Jaj@tYa@RaAp@cg@rWqNtH}d@pVuq@`^ydAlj@gBlAiBxAcBnBiA|AsA|BkBtEsBrG}AdIgAnHi@fF{BlY}A~W|A_XzBmYh@gFfAoH|AeI^kCpAuHzLiq@rCmOJiAfNqu@~P{_AvJqh@dHc`@fBeKtGk^pFmYxh@auC|\qjB`Gk[nGq\|BgMfCoPhAyJ`@qEb@aG`@cIRsJ\aX^mZj@w`@JiLHaHVuKVgNCqBjHweFFuD@gFCoEKsFMgD]uFc@aFe@mEgAoH{_AcvFoAoI_BaMks@}sGc@wEg@}H[qHMgEEgECcE@aED_FLcFZ_HPcDXwD`@oE`AmIfl@afEp@iGZ}D`@aIP}H@cI?oP@?"
line = polyline.decode(fr'{my_polyline}', geojson=True)

print(LineString(line))

data = pd.read_parquet('../data/routes_2503.parquet')

keys = data['key'].unique()
new_list_dfs = []
linestring_list = []

for key in keys:

    temp_df = data[data['key']==key].copy().reset_index(drop=True)

    for i in temp_df.index[1:]:
        prev_lat = temp_df.loc[i-1, 'lat']
        prev_lon = temp_df.loc[i-1, 'lon']

        curr_lat = temp_df.loc[i, 'lat']
        curr_lon = temp_df.loc[i, 'lon']

        curr_dist = temp_df.loc[i, 'distances']

        if pd.isnull(curr_dist):
            disctance = haversine((prev_lat, prev_lon), (curr_lat, curr_lon), unit=Unit.METERS)
            temp_df.loc[i, 'distances'] = disctance

    
    temp_df, temp_line = polylines_decoder(temp_df)
    linestring_list.append(temp_line)

    new_list_dfs.append(temp_df)

full_data = pd.concat(new_list_dfs, ignore_index=True)

linestr = gpd.GeoDataFrame({
    'route_name': keys,
    'geometry':linestring_list
})

linestr.to_file('../data/routes_linestrings.shp', encoding='utf-8', index=False)

full_data.to_parquet('../data/routes_data_all.parquet', index=False)