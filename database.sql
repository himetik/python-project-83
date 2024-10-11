DROP TABLE IF EXISTS urls CASCADE;
DROP TABLE IF EXISTS url_checks;


CREATE TABLE urls (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) UNIQUE NOT NULL,
    created_at date NOT NULL
);


CREATE TABLE url_checks (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id bigint REFERENCES urls (id),
    status_code varchar(3),
	h1 varchar,
	title varchar,
	description varchar,
	created_at date NOT NULL
);
