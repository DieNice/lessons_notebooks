query_2 = '''SELECT * FROM bookings.aircrafts_data ORDER BY range DESC'''

query_1 = '''SELECT
  bookings.seats.fare_conditions AS fare_conditions,
  bookings.seats.aircraft_code as aircraft_code,
  COUNT(*) AS count1
FROM
  bookings.seats
GROUP by
  aircraft_code,
  bookings.seats.fare_conditions'''

query_tab = '''create TEMPORARY table tt as
select
    f.flight_id,
	f.status,
    f.aircraft_code,
	f.arrival_airport,
	ad.city arrival_city,
	f.departure_airport,
	f.scheduled_arrival,
	f.actual_arrival 	
from bookings.flights f 
 join bookings.airports_data ad on f.arrival_airport = ad.airport_code;


create TEMPORARY table tt2 as
select 
    tt.flight_id,
    tt.aircraft_code,
 	tt.status,
	tt.arrival_airport,
	tt.arrival_city,
	tt.departure_airport,
	ad.city,
	tt.scheduled_arrival,
	tt.actual_arrival 
from tt 
 join bookings.airports_data ad on tt.departure_airport = ad.airport_code;


CREATE TEMPORARY TABLE subset_data_id_code AS
SELECT   f.flight_id id,
         f.aircraft_code code             
FROM bookings.flights f	 
where f.status = 'Arrived';

CREATE TEMPORARY TABLE subset_data_code_max_count AS
select
  bs.aircraft_code code,
  COUNT(*) AS count
FROM
  bookings.seats bs
GROUP BY bs.aircraft_code;

CREATE TEMPORARY TABLE subset_data_id_code_max AS
select
  subset_data_id_code.id id,
  subset_data_id_code.code code,
  subset_data_code_max_count.count max
FROM
   subset_data_id_code 
   full JOIN subset_data_code_max_count ON subset_data_id_code.code = subset_data_code_max_count.code
GROUP by subset_data_id_code.id, subset_data_id_code.code, max;

CREATE TEMPORARY TABLE subset_data_id_code_max_count AS
select
  subset_data_id_code_max.code,
  subset_data_id_code_max.max,
  bp.flight_id,
  COUNT(*) AS count
FROM
  bookings.boarding_passes bp
  JOIN subset_data_id_code_max ON bp.flight_id = subset_data_id_code_max.id
GROUP BY bp.flight_id,subset_data_id_code_max.id,subset_data_id_code_max.max,subset_data_id_code_max.code;

CREATE TEMPORARY TABLE fff AS
select 
    fin.flight_id,
	fin.max,
	fin.count,
	CAST(fin.count AS DEC(12,4))/fin.max*100 as per
from
	subset_data_id_code_max_count fin;

select 
    tt2.flight_id,
 	tt2.status,
    tt2.aircraft_code,
	tt2.arrival_airport,
	tt2.departure_airport,
	tt2.scheduled_arrival,
	tt2.actual_arrival,
	fff.per
from tt2 
 left join fff on fff.flight_id = tt2.flight_id;
'''