-- Users
insert into auth.users values ('94edc173-a4e6-42af-8b81-889f2d67d45f');

-- Source
insert into organism_data.source  values (
'7e21c66b-d10d-4418-a634-6df0a1796366',
'NCBI'
);

insert into organism_data.source  values (
'120aa5b6-e1ec-4dd1-a34a-51b81fd276c4',
'Universidad de Los Andes - Colombia'
);

-- Organism
insert into core.organism  values (
'faf81399-7d0b-4cb1-8392-b02eb697d206',
'UN0010',
'94edc173-a4e6-42af-8b81-889f2d67d45f',
'5660',
'{"collection_date": "2013", "host":"Homo Sapiens"}',
now(),
'Leishmania braziliensis'
);
insert into core.organism  values (
'4ba32111-dced-4cf0-9837-3d85dd8321fc',
'LL0772',
'94edc173-a4e6-42af-8b81-889f2d67d45f',
'5679',
'{"collection_date": "2013", "host":"Homo Sapiens"}',
now(),
'Leishmania panamensis'
);

-- Genome
insert into organism_data.genome values (
'a63959ba-255b-44a9-a3cd-a71cc66dc756',
'faf81399-7d0b-4cb1-8392-b02eb697d206',
now(),
'v1',
'Genome assembly generated with NGSEP using ONT reads and polished using Illumina reads',
true,
'GCA_041682335.1',
'7e21c66b-d10d-4418-a634-6df0a1796366'
);

insert into organism_data.genome values (
'6e638b6b-6023-4bde-a76d-08350dd09955',
'4ba32111-dced-4cf0-9837-3d85dd8321fc',
now(),
'v1',
'Genome assembly generated with NGSEP using ONT reads and polished using Illumina reads',
true,
'GCA_041682335.1',
'7e21c66b-d10d-4418-a634-6df0a1796366'
);

-- Annotation
insert into organism_data.annotations values (
'e6916574-e3bd-4529-9a69-64338551be04',
'a63959ba-255b-44a9-a3cd-a71cc66dc756',
now(),
'v1',
'Genome annotation generated with Companion'
'120aa5b6-e1ec-4dd1-a34a-51b81fd276c4'
);


insert into organism_data.annotations values (
'5dbce307-2974-4841-a08b-bdf6bb37b58c',
'6e638b6b-6023-4bde-a76d-08350dd09955',
now(),
'v1',
'Genome annotation generated with Companion'
'120aa5b6-e1ec-4dd1-a34a-51b81fd276c4'
);


