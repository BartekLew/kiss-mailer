#!/bin/sh

mysql -u lew89_kisssub -p $@ <<EOF
create table subreq (
    email varchar(320),
    name varchar(64),
    hash varchar(30) UNIQUE,
    PRIMARY KEY(hash)
);

create table subs (
    email varchar(320),
    name varchar(64)
);
EOF
