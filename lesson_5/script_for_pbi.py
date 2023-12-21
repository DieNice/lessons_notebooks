import pandas as pd
import psycopg2
from psycopg2 import OperationalError
import numpy as np


try:
    # пытаемся подключиться к базе данных
    conn = psycopg2.connect(dbname='demo', user='proskurin.da3', password='neM3B5EO+xrH', host='adm-it-std-pg1.dns-shop.ru')
except:
    # в случае сбоя подключения будет выведено сообщение в STDOUT
    print('Can`t establish connection to database')


cursor = conn.cursor()
query = '''CREATE TEMPORARY TABLE subset_data_id_code AS /* создание временной таблицы*/
SELECT   f.flight_id id,    /* Выбираем id рейса со статусом "Arrived" и код самолёта*/
                f.aircraft_code code             
FROM bookings.flights f	 
where f.status = 'Arrived';

CREATE TEMPORARY TABLE subset_data_code_max_count AS
select    /* Подсчитываем максимальную вместимость в самолёт*/
  bs.aircraft_code code,
  COUNT(*) AS count
FROM
  bookings.seats bs
GROUP BY bs.aircraft_code;

CREATE TEMPORARY TABLE subset_data_id_code_max AS
select /*Соединяем две предыдущие таблицы*/
  subset_data_id_code.id id,
  subset_data_id_code.code code,
  subset_data_code_max_count.count max
FROM
   subset_data_id_code 
   full JOIN subset_data_code_max_count ON subset_data_id_code.code = subset_data_code_max_count.code
GROUP by subset_data_id_code.id, subset_data_id_code.code, max;

select  /*Подсчитываем количество посадочных талонов и объединяем с предыдущей таблицей*/
  subset_data_id_code_max.code,
  subset_data_id_code_max.max,
  bp.flight_id,
  COUNT(*) AS count
FROM
  bookings.boarding_passes bp
  JOIN subset_data_id_code_max ON bp.flight_id = subset_data_id_code_max.id
GROUP BY bp.flight_id,subset_data_id_code_max.id,subset_data_id_code_max.max,subset_data_id_code_max.code;
 '''

df = pd.read_sql(query,conn)

cursor.close() # закрываем курсор
conn.close() # закрываем соединение


df['percent'] = df['count']/df['max']*100   #высчитываем процент заполненности

df['flight_id'] = df['flight_id'].astype(int) #приводим к нужным титам данных
df['code'] = df['code'].astype(str)
df['max'] = df['max'].astype(int)
df['count'] = df['count'].astype(int)
df['percent'] = df['percent'].round(4)
df['percent'] = df['percent'].astype(float)
