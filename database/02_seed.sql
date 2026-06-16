-- 02_seed.sql

-- 1. IŠVALOME SENUS DUOMENIS (vykdant kelis kartus iš eilės nekils klaidų)
-- Dėl ON DELETE CASCADE, ištrynus 'users', automatiškai išsitrins ir 'providers' bei 'reservations'
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE reservations;
TRUNCATE TABLE providers;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. ĮKELIAME VARTOTOJUS (Klijentus, Teikėjus ir Administratorių)
-- Slaptažodžių maišos tekstai imituoja realų bcrypt formatą
INSERT INTO users (id, name, surname, email, password_hash, role) VALUES
(1, 'Jonas', 'Jonaitis', 'jonas@client.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36X6k8x2T9A675tC5C3S06.', 'CLIENT'),
(2, 'Aistė', 'Petraitė', 'aiste@client.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36X6k8x2T9A675tC5C3S06.', 'CLIENT'),
(3, 'Karolis', 'Barzdotas', 'karolis@provider.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36X6k8x2T9A675tC5C3S06.', 'PROVIDER'),
(4, 'Elena', 'Dantė', 'elena@provider.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36X6k8x2T9A675tC5C3S06.', 'PROVIDER'),
(5, 'Tomas', 'Valdytojas', 'admin@system.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36X6k8x2T9A675tC5C3S06.', 'ADMIN');

-- 3. ĮKELIAME PASLAUGŲ TEIKĖJUS (Providers)
-- Susiejame su vartotojais, kurių id yra 3 ir 4
INSERT INTO providers (id, user_id, location) VALUES
(1, 3, 'Vilniaus g. 10, Vilnius'), -- Karolis veikia Vilniuje
(2, 4, 'Kauno g. 5, Kaunas');       -- Elena veikia Kaune

-- 4. ĮKELIAME REZERVACIJAS (Reservations)
-- client_id rodo į users(id), provider_id rodo į providers(id)
INSERT INTO reservations (client_id, provider_id, reservation_time, reservation_type, duration_minutes) VALUES
-- Jono (client_id = 1) užsakymai pas Karolį (provider_id = 1)
(1, 1, '2026-06-20 10:00:00', 'Barzdos skutimas ir formavimas', 45),
(1, 1, '2026-07-05 11:30:00', 'Plaukų kirpimas', 30),

-- Jono (client_id = 1) užsakymas pas Eleną (provider_id = 2)
(1, 2, '2026-06-22 14:00:00', 'Dantų higiena', 60),

-- Aistės (client_id = 2) užsakymai pas Eleną (provider_id = 2)
(2, 2, '2026-06-23 09:00:00', 'Pirminė odontologo konsultacija', 30),
(2, 2, '2026-06-30 16:00:00', 'Danties plombavimas', 90);