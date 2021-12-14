CREATE TYPE inst AS ENUM (
    'Caltech',
    'UVA',
    'Rome'
);

-- Table to keep track of the light yield of the BTL modules.
CREATE TABLE btl_qa (
    key                 bigserial PRIMARY KEY,
    timestamp           timestamp with time zone default now(),
    ch0_511             real,
    ch1_511             real,
    ch2_511             real,
    ch3_511             real,
    ch4_511             real,
    ch5_511             real,
    ch6_511             real,
    ch7_511             real,
    ch8_511             real,
    ch9_511             real,
    ch10_511            real,
    ch11_511            real,
    ch12_511            real,
    ch13_511            real,
    ch14_511            real,
    ch15_511            real,
    ch16_511            real,
    ch17_511            real,
    ch18_511            real,
    ch19_511            real,
    ch20_511            real,
    ch21_511            real,
    ch22_511            real,
    ch23_511            real,
    ch24_511            real,
    ch25_511            real,
    ch26_511            real,
    ch27_511            real,
    ch28_511            real,
    ch29_511            real,
    ch30_511            real,
    ch31_511            real,
    institution         inst DEFAULT 'Caltech'::inst NOT NULL
);
