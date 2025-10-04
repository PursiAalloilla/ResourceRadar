--
-- File generated with SQLiteStudio v3.4.17 on Sat Oct 4 11:03:03 2025
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: Company
CREATE TABLE IF NOT EXISTS Company(
	leagentityidentifier TEXT PRIMARY KEY NOT NULL,
	name TEXT NOT NULL,
	officelocation INTEGER NOT NULL,
	field TEXT NOT NULL,
	phonenumber INTEGER NOT NULL,
	email TEXT
);
INSERT INTO Company (leagentityidentifier, name, officelocation, field, phonenumber, email) VALUES ('12353231-2', 'Pekan rakennus oy', 'vaasankatu 10', 'Construction', 401212651, NULL);
INSERT INTO Company (leagentityidentifier, name, officelocation, field, phonenumber, email) VALUES ('5432165-4', 'Martan kylä kauppa', 'vaasankatu 15', 'General store', 401562729, NULL);

-- Table: Person
CREATE TABLE IF NOT EXISTS Person(
	socialsecuritynumber CHAR(11) PRIMARY KEY NOT NULL,
	name TEXT NOT NULL,
	location INTEGER NOT NULL,
	phonenumber INTEGER NOT NULL,
	timeoflastlocation DATE NOT NULL,
	address TEXT NOT NULL
);
INSERT INTO Person (socialsecuritynumber, name, location, phonenumber, timeoflastlocation, address) VALUES ('123456A789E', 'Mikko Mallikas', 1000, 501234567, '2025-04-15', 'kotikatu 5');
INSERT INTO Person (socialsecuritynumber, name, location, phonenumber, timeoflastlocation, address) VALUES ('514263A912E', 'Pekka Virtanen', 1100, 401212651, '2025-01-11', 'hämeentie 3');
INSERT INTO Person (socialsecuritynumber, name, location, phonenumber, timeoflastlocation, address) VALUES ('111364A985E', 'Martta Maijanen', 1100, 401562729, '2025-03-11', 'vaasakatu 6');
INSERT INTO Person (socialsecuritynumber, name, location, phonenumber, timeoflastlocation, address) VALUES ('214365A987E', 'Eetu Esimerkillinen', 1200, 401562212, '2025-04-21', 'raatentie 6');

-- Table: Skills
CREATE TABLE IF NOT EXISTS Skills(
	skillid INTEGER NOT NULL,
	socialsecuritynumber CHAR(11) NOT NULL,
	skill TEXT NOT NULL,
	proficiency TEXT,
	type TEXT,
	FOREIGN KEY (socialsecuritynumber) REFERENCES person(socialsecuritynumber) ON UPDATE CASCADE,
	PRIMARY KEY(skillid)
);
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (10, '123456A789E', 'Russian', 'B2', 'Language');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (11, '123456A789E', 'Tracktor driving', NULL, 'Vehicle operating');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (12, '123456A789E', 'Drone Flying', 'Hobbiest', 'Military');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (13, '514263A912E', 'Excavator operating', NULL, 'Vehicle operating');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (14, '214365A987E', 'Medic', NULL, 'Profesion');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (15, '214365A987E', 'Spanish Language', 'B1', 'Language');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (16, '214365A987E', 'Modeling', 'Hobbiest', 'Military');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (17, '514263A912E', 'German Language', 'B1', 'Language');
INSERT INTO Skills (skillid, socialsecuritynumber, skill, proficiency, type) VALUES (18, '123456A789E', 'Nurse', NULL, 'Profession');

-- Table: Vehicle
CREATE TABLE IF NOT EXISTS Vehicle(
	registernumber TEXT NOT NULL,
	fueltype TEXT NOT NULL,
	working TEXT NOT NULL,
	vehicletype TEXT NOT NULL,
	capacity INTEGER NOT NULL,
	location INTEGER NOT NULL,
	timeoflastlocation DATE NOT NULL,
	socialsecuritynumber CHAR(11),
	leagentityidentifier TEXT,
	FOREIGN KEY (socialsecuritynumber) REFERENCES person(socialsecuritynumber) ON UPDATE CASCADE,
	FOREIGN KEY (leagentityidentifier) REFERENCES company(leagentityidentifier) ON UPDATE CASCADE,
	PRIMARY KEY(registernumber)
);
INSERT INTO Vehicle (registernumber, fueltype, working, vehicletype, capacity, location, timeoflastlocation, socialsecuritynumber, leagentityidentifier) VALUES ('123-abc', 'Dieasel', 'True', 'Pickup Truck', 2, '11
00', '2025-04-15', '123456A789E', NULL);
INSERT INTO Vehicle (registernumber, fueltype, working, vehicletype, capacity, location, timeoflastlocation, socialsecuritynumber, leagentityidentifier) VALUES ('321-cba', 'Petrol', 'True', 'Van', 4, '11
00', '2025-05-15', '111364A985E', NULL);
INSERT INTO Vehicle (registernumber, fueltype, working, vehicletype, capacity, location, timeoflastlocation, socialsecuritynumber, leagentityidentifier) VALUES ('213-bac', 'Electricity', 'True', 'Bus', 40, '11
00', '2025-11-04', '214365A987E', NULL);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
