import polyline
from shapely.geometry import LineString

my_polyline = "_u}vHs_j|AsACjFkBASyWfGyBRsCBgIWaEY{BYuP{Dgh@yLeLcDwGmB{HqBea@{Ky^qKc\iJiPoEeSaG}H{AyBYyAM_GKuC@oCJkD\iEt@yA\cMtDcShGiEtA_QfFcFbAyEh@yCNmEB{CKuJ{@iRyBwDWeBI{EDqDTsEl@eFfAaBb@oBt@aBt@qYbOyq@h^m\|Pif@fWiItEONiAt@iYdOmA|@_A`AaArAeBlCqBnC}AtCsAhCmGfOk@dAQRYv@aAdB}BhD}BjC}@|@qDpC_E`CgCbAsBj@oWdFmOjCaGhAeHhBqDlAcEfBwR~Jaj@tYa@RaAp@cg@rWqNtH}d@pVuq@`^ydAlj@gBlAiBxAcBnBiA|AsA|BkBtEsBrG}AdIgAnHi@fF{BlY}A~W|A_XzBmYh@gFfAoH|AeI^kCpAuHzLiq@rCmOJiAfNqu@~P{_AvJqh@dHc`@fBeKtGk^pFmYxh@auC|\qjB`Gk[nGq\|BgMfCoPhAyJ`@qEb@aG`@cIRsJ\aX^mZj@w`@JiLHaHVuKVgNCqBjHweFFuD@gFCoEKsFMgD]uFc@aFe@mEgAoH{_AcvFoAoI_BaMks@}sGc@wEg@}H[qHMgEEgECcE@aED_FLcFZ_HPcDXwD`@oE`AmIfl@afEp@iGZ}D`@aIP}H@cI?oP@?"
line = polyline.decode(fr'{my_polyline}', geojson=True)

print(LineString(line))