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
