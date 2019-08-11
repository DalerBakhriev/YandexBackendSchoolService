CREATE TABLE IF NOT EXISTS public.citizens (
      import_id int8 NOT NULL,
      citizen_id int8 NOT NULL,
      town varchar NOT NULL,
      street varchar NOT NULL,
      building varchar NOT NULL,
      apartment int4 NOT NULL,
      name VARCHAR NOT NULL,
      birth_date date,
      gender varchar,
      CONSTRAINT import_citizen_pkey PRIMARY KEY (import_id, citizen_id)
      );

CREATE TABLE IF NOT EXISTS public.relatives (
      import_id int8 NOT NULL,
      citizen_id int8 NOT NULL,
      relative_id int8 NOT NULL,
      CONSTRAINT import_citizen_fkey FOREIGN KEY (import_id, citizen_id) REFERENCES public.citizens(import_id, citizen_id),
      CONSTRAINT import_relative_fkey FOREIGN KEY (import_id, relative_id) REFERENCES public.citizens(import_id, citizen_id)
      );

CREATE SEQUENCE IF NOT EXISTS imports_seq START 1;