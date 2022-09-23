import sqlalchemy
from sqlalchemy.schema import DDL
from .base import Base

class ConvertKM():
	sqlalchemy.event.listen(
		Base.metadata,
		'before_create',
		DDL("CREATE OR REPLACE FUNCTION convert_km(n double precision, unit text) RETURNS double precision AS $$ SELECT CASE WHEN $2 = 'KM' THEN $1 WHEN $2 = 'MI' THEN $1 / 1.60934 END; $$ LANGUAGE SQL IMMUTABLE RETURNS NULL ON NULL INPUT;")
	)