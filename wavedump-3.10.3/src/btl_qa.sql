CREATE TYPE inst AS ENUM (
    'Caltech',
    'UVA',
    'Rome'
);

-- Table to keep track of the light yield of the BTL modules.
CREATE TABLE btl_qa (
    key                 bigserial PRIMARY KEY,
    timestamp           timestamp with time zone default now(),
    barcode             bigint NOT NULL,
    voltage             real NOT NULL,
    ch_511              real[],
    institution         inst DEFAULT 'Caltech'::inst NOT NULL
);

-- create btl admin user
CREATE ROLE btl_admin WITH LOGIN;

-- btl admin user has all rights to everything in the database
GRANT ALL ON btl_qa TO btl_admin;
GRANT ALL ON SEQUENCE btl_qa_key_seq TO btl_admin;

-- create btl read user
CREATE ROLE btl_read;

-- btl read user has select rights on everything in the btl schema
GRANT SELECT ON btl_qa TO btl_read;
GRANT SELECT ON SEQUENCE btl_qa_key_seq TO btl_read;

-- create btl write user
CREATE ROLE btl_write;

-- btl write user has select rights on everything in the btl schema
GRANT SELECT, INSERT ON btl_qa TO btl_write;
GRANT SELECT, USAGE ON SEQUENCE btl_qa_key_seq TO btl_write;

-- create btl user
CREATE ROLE btl WITH LOGIN;

-- this is the role used by the assembly centers to upload data
GRANT btl_read, btl_write TO btl;

-- create cms user
CREATE ROLE cms WITH LOGIN;

-- this is the role used by the website, should only have read access
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cms;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO cms;

-----------------------------
-- Set up ownership of tables
-----------------------------

ALTER TABLE btl_qa OWNER TO btl_admin;
