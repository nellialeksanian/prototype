import pandas as pd

data2 = pd.read_parquet('data/paintings_data_tables/data_with_images.parquet')
data1 = pd.read_parquet('data/paintings_data_tables/embeddings_dataset_bge.parquet')
df1 = pd.DataFrame(data1)
df2 = pd.DataFrame(data2)

df = pd.merge(df1, df2[['title', 'image']], on='title', how='left')

print(df)
print(df.info())
df.to_parquet('data/paintings_data_tables/full_data.parquet')