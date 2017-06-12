drop table if exists entries;
create table entries (
  'id' integer primary key autoincrement,
  'title' varchar(99) DEFAULT NULL,
  'text' varchar(999) DEFAULT NULL,
  'imgurl' text not null,
);