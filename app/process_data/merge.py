import pandas as pd

# Пример данных
# data2 = pd.read_csv('data/paintings_data_tables/data_with_images.csv')
# data2.to_parquet('data/paintings_data_tables/data_with_images.parquet')
data2 = pd.read_parquet('data/paintings_data_tables/data_with_images.parquet')
# data2 = pd.read_parquet('app/data/dataset_with_images_full.parquet')
# print(data2.head(5))
data1 = pd.read_parquet('data/paintings_data_tables/embeddings_dataset_bge.parquet')
# print(data1.head(5))
df1 = pd.DataFrame(data1)
df2 = pd.DataFrame(data2)

# Объединяем данные по колонке 'title', добавляем колонку 'description' из df2 в df1
df = pd.merge(df1, df2[['title', 'image']], on='title', how='left')

# Выводим результат
print(df)
print(df.info())
# print(df.info)
df.to_parquet('data/paintings_data_tables/full_data.parquet')
# import pandas as pd
# import numpy as np
# data = pd.read_parquet('app/data/images.parquet')
# data['image_vector'] = data['image_vector'].apply(
#     lambda x: np.zeros(512) if (x is None or len(x) == 0 or np.isnan(x).any()) else x
# )
# data.to_parquet('app/data/images1.parquet')
