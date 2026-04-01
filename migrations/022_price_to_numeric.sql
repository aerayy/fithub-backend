-- Change coach_packages.price from INT to NUMERIC to support decimal TL values
ALTER TABLE coach_packages ALTER COLUMN price TYPE NUMERIC(10,2) USING price::NUMERIC(10,2);
