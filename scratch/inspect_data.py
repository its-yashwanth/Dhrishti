import pandas as pd

df = pd.read_csv('Drishti_Cascade_Final_With_EMDAT.csv', usecols=['Year', 'Month', 'Country', 'Trade_Type', 'HS4', 'Commodity', 'Trade_Share', 'Shock_Intensity', 'Effective_Shock'])

sub = df[df['Country'].str.upper() == 'BANGLADESH']
print('Bangladesh commodities count:', sub['Commodity'].nunique())
print('Top Bangladesh commodities by rows:')
print(sub.groupby(['HS4', 'Commodity', 'Trade_Type']).size().sort_values(ascending=False).head(15))




