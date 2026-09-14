# Constantes y mapeos compartidos del pipeline
PROVINCIAS_INE = {
 "01":("Araba/Álava","País Vasco"),"02":("Albacete","Castilla-La Mancha"),"03":("Alicante","Comunitat Valenciana"),
 "04":("Almería","Andalucía"),"05":("Ávila","Castilla y León"),"06":("Badajoz","Extremadura"),
 "07":("Illes Balears","Illes Balears"),"08":("Barcelona","Cataluña"),"09":("Burgos","Castilla y León"),
 "10":("Cáceres","Extremadura"),"11":("Cádiz","Andalucía"),"12":("Castellón","Comunitat Valenciana"),
 "13":("Ciudad Real","Castilla-La Mancha"),"14":("Córdoba","Andalucía"),"15":("A Coruña","Galicia"),
 "16":("Cuenca","Castilla-La Mancha"),"17":("Girona","Cataluña"),"18":("Granada","Andalucía"),
 "19":("Guadalajara","Castilla-La Mancha"),"20":("Gipuzkoa","País Vasco"),"21":("Huelva","Andalucía"),
 "22":("Huesca","Aragón"),"23":("Jaén","Andalucía"),"24":("León","Castilla y León"),
 "25":("Lleida","Cataluña"),"26":("La Rioja","La Rioja"),"27":("Lugo","Galicia"),
 "28":("Madrid","Comunidad de Madrid"),"29":("Málaga","Andalucía"),"30":("Murcia","Región de Murcia"),
 "31":("Navarra","Navarra"),"32":("Ourense","Galicia"),"33":("Asturias","Asturias"),
 "34":("Palencia","Castilla y León"),"35":("Las Palmas","Canarias"),"36":("Pontevedra","Galicia"),
 "37":("Salamanca","Castilla y León"),"38":("Santa Cruz de Tenerife","Canarias"),"39":("Cantabria","Cantabria"),
 "40":("Segovia","Castilla y León"),"41":("Sevilla","Andalucía"),"42":("Soria","Castilla y León"),
 "43":("Tarragona","Cataluña"),"44":("Teruel","Aragón"),"45":("Toledo","Castilla-La Mancha"),
 "46":("Valencia","Comunitat Valenciana"),"47":("Valladolid","Castilla y León"),"48":("Bizkaia","País Vasco"),
 "49":("Zamora","Castilla y León"),"50":("Zaragoza","Aragón"),"51":("Ceuta","Ceuta"),"52":("Melilla","Melilla"),
}
SLUG_PROVINCIA = {
 "alava":"Araba/Álava","araba":"Araba/Álava","albacete":"Albacete","alicante":"Alicante","alacant":"Alicante",
 "almeria":"Almería","avila":"Ávila","badajoz":"Badajoz","baleares":"Illes Balears","illes-balears":"Illes Balears",
 "islas-baleares":"Illes Balears","mallorca":"Illes Balears","menorca":"Illes Balears","ibiza":"Illes Balears",
 "barcelona":"Barcelona","burgos":"Burgos","caceres":"Cáceres","cadiz":"Cádiz","castellon":"Castellón",
 "castello":"Castellón","ciudad-real":"Ciudad Real","cordoba":"Córdoba","a-coruna":"A Coruña","coruna":"A Coruña",
 "la-coruna":"A Coruña","cuenca":"Cuenca","girona":"Girona","gerona":"Girona","granada":"Granada",
 "guadalajara":"Guadalajara","gipuzkoa":"Gipuzkoa","guipuzcoa":"Gipuzkoa","huelva":"Huelva","huesca":"Huesca",
 "jaen":"Jaén","leon":"León","lleida":"Lleida","lerida":"Lleida","la-rioja":"La Rioja","rioja":"La Rioja",
 "lugo":"Lugo","madrid":"Madrid","malaga":"Málaga","murcia":"Murcia","navarra":"Navarra","ourense":"Ourense",
 "orense":"Ourense","asturias":"Asturias","palencia":"Palencia","las-palmas":"Las Palmas","gran-canaria":"Las Palmas",
 "lanzarote":"Las Palmas","fuerteventura":"Las Palmas","pontevedra":"Pontevedra","salamanca":"Salamanca",
 "santa-cruz-de-tenerife":"Santa Cruz de Tenerife","tenerife":"Santa Cruz de Tenerife","la-gomera":"Santa Cruz de Tenerife",
 "el-hierro":"Santa Cruz de Tenerife","la-palma":"Santa Cruz de Tenerife","cantabria":"Cantabria","segovia":"Segovia",
 "sevilla":"Sevilla","soria":"Soria","tarragona":"Tarragona","teruel":"Teruel","toledo":"Toledo",
 "valencia":"Valencia","valladolid":"Valladolid","bizkaia":"Bizkaia","vizcaya":"Bizkaia","zamora":"Zamora",
 "zaragoza":"Zaragoza","ceuta":"Ceuta","melilla":"Melilla",
}
PROVINCIA_A_CCAA = {v[0]: v[1] for v in PROVINCIAS_INE.values()}
SLUG_REGION = {
 "andalucia":"Andalucía","aragon":"Aragón","asturias":"Asturias","principado-de-asturias":"Asturias",
 "baleares":"Illes Balears","islas-baleares":"Illes Balears","illes-balears":"Illes Balears","canarias":"Canarias",
 "cantabria":"Cantabria","castilla-leon":"Castilla y León","castilla-y-leon":"Castilla y León",
 "castilla-la-mancha":"Castilla-La Mancha","cataluna":"Cataluña","catalunya":"Cataluña",
 "comunidad-valenciana":"Comunitat Valenciana","valencia":"Comunitat Valenciana","comunitat-valenciana":"Comunitat Valenciana",
 "extremadura":"Extremadura","galicia":"Galicia","madrid":"Comunidad de Madrid","comunidad-de-madrid":"Comunidad de Madrid",
 "murcia":"Región de Murcia","region-de-murcia":"Región de Murcia","navarra":"Navarra","pais-vasco":"País Vasco",
 "euskadi":"País Vasco","la-rioja":"La Rioja","ceuta":"Ceuta","melilla":"Melilla",
}
MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
MESES_EN = ["january","february","march","april","may","june","july","august","september","october","november","december"]
MESES_CA = ["gener","febrer","març","abril","maig","juny","juliol","agost","setembre","octubre","novembre","desembre"]
ISO_PROVINCIA = {
 "ES-VI":"Araba/Álava","ES-AB":"Albacete","ES-A":"Alicante","ES-AL":"Almería","ES-AV":"Ávila","ES-BA":"Badajoz",
 "ES-PM":"Illes Balears","ES-B":"Barcelona","ES-BU":"Burgos","ES-CC":"Cáceres","ES-CA":"Cádiz","ES-CS":"Castellón",
 "ES-CR":"Ciudad Real","ES-CO":"Córdoba","ES-C":"A Coruña","ES-CU":"Cuenca","ES-GI":"Girona","ES-GR":"Granada",
 "ES-GU":"Guadalajara","ES-SS":"Gipuzkoa","ES-H":"Huelva","ES-HU":"Huesca","ES-J":"Jaén","ES-LE":"León",
 "ES-L":"Lleida","ES-LO":"La Rioja","ES-LU":"Lugo","ES-M":"Madrid","ES-MA":"Málaga","ES-MU":"Murcia",
 "ES-NA":"Navarra","ES-OR":"Ourense","ES-O":"Asturias","ES-P":"Palencia","ES-GC":"Las Palmas","ES-PO":"Pontevedra",
 "ES-SA":"Salamanca","ES-TF":"Santa Cruz de Tenerife","ES-S":"Cantabria","ES-SG":"Segovia","ES-SE":"Sevilla",
 "ES-SO":"Soria","ES-T":"Tarragona","ES-TE":"Teruel","ES-TO":"Toledo","ES-V":"Valencia","ES-VA":"Valladolid",
 "ES-BI":"Bizkaia","ES-ZA":"Zamora","ES-Z":"Zaragoza","ES-CE":"Ceuta","ES-ML":"Melilla",
}
ISO_CCAA = {
 "ES-AN":"Andalucía","ES-AR":"Aragón","ES-AS":"Asturias","ES-CN":"Canarias","ES-CB":"Cantabria",
 "ES-CL":"Castilla y León","ES-CM":"Castilla-La Mancha","ES-CT":"Cataluña","ES-EX":"Extremadura","ES-GA":"Galicia",
 "ES-IB":"Illes Balears","ES-RI":"La Rioja","ES-MD":"Comunidad de Madrid","ES-MC":"Región de Murcia",
 "ES-NC":"Navarra","ES-PV":"País Vasco","ES-VC":"Comunitat Valenciana","ES-CE":"Ceuta","ES-ML":"Melilla",
}
