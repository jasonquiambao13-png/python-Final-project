CREATE DATABASE livestock_management;
USE livestock_management;

-- --------------------------------------------
-- Table 1: livestock
-- --------------------------------------------
CREATE TABLE livestock (
    livestock_id    INT AUTO_INCREMENT PRIMARY KEY,
    id_number       VARCHAR(30)  NOT NULL UNIQUE,
    name            VARCHAR(50)  NOT NULL,
    type            ENUM('Cattle', 'Pig', 'Goat', 'Chicken', 'Other') NOT NULL,
    breed           VARCHAR(50),
    sex             ENUM('Male', 'Female') NOT NULL,
    birth_date      DATE,
    weight          DECIMAL(8,2) DEFAULT 0.00,
    health_status   ENUM('Healthy', 'Sick', 'Under Treatment', 'Recovering') NOT NULL DEFAULT 'Healthy',
    date_acquired   DATE
);

-- --------------------------------------------
-- Table 2: health_records
-- --------------------------------------------
CREATE TABLE health_records (
    health_id       INT AUTO_INCREMENT PRIMARY KEY,
    livestock_id    INT NOT NULL,
    record_date     DATE NOT NULL,
    illness         VARCHAR(100),
    treatment       VARCHAR(150),
    vaccination     VARCHAR(100),
    notes           TEXT,
    FOREIGN KEY (livestock_id) REFERENCES livestock(livestock_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- --------------------------------------------
-- Table 3: breeding_records
-- --------------------------------------------
CREATE TABLE breeding_records (
    breeding_id             INT AUTO_INCREMENT PRIMARY KEY,
    livestock_id            INT NOT NULL,
    breeding_date           DATE NOT NULL,
    breeding_status         ENUM('Bred', 'Pregnant', 'Delivered', 'Failed') NOT NULL DEFAULT 'Bred',
    expected_delivery_date  DATE,
    notes                   TEXT,
    FOREIGN KEY (livestock_id) REFERENCES livestock(livestock_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- --------------------------------------------
-- Table 4: expenses
-- (total_amount = quantity * unit_cost, calculated by the program)
-- --------------------------------------------
CREATE TABLE expenses (
    expense_id      INT AUTO_INCREMENT PRIMARY KEY,
    expense_date    DATE NOT NULL,
    category        ENUM('Feed', 'Medicine', 'Vaccination', 'Other') NOT NULL,
    description     VARCHAR(150) NOT NULL,
    quantity        DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    unit_cost       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    notes           TEXT
);

-- --------------------------------------------
-- Optional sample data (for testing)
-- --------------------------------------------
INSERT INTO livestock (id_number, name, type, breed, sex, birth_date, weight, health_status, date_acquired)
VALUES
('CT-001', 'Bessie', 'Cattle',  'Holstein',  'Female', '2023-03-15', 450.50, 'Healthy', '2023-06-01'),
('PG-001', 'Porky',  'Pig',     'Duroc',     'Male',   '2024-01-10', 95.00,  'Healthy', '2024-02-01'),
('GT-001', 'Billy',  'Goat',    'Boer',      'Male',   '2024-05-20', 40.25,  'Sick',    '2024-06-15');

INSERT INTO health_records (livestock_id, record_date, illness, treatment, vaccination, notes)
VALUES (3, '2026-10-01', 'Cough', 'Antibiotics', NULL, 'Monitor for one week');

INSERT INTO breeding_records (livestock_id, breeding_date, breeding_status, expected_delivery_date, notes)
VALUES (1, '2026-08-01', 'Pregnant', '2027-05-10', 'First breeding');

INSERT INTO expenses (expense_date, category, description, quantity, unit_cost, total_amount, notes)
VALUES ('2026-10-05', 'Feed', 'Cattle feed sacks', 10, 1200.00, 12000.00, 'Monthly supply');
