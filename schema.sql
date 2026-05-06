-- ============================================================
--  RaidLink_DB  –  Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS RaidLink_DB
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE RaidLink_DB;

-- ------------------------------------------------------------
--  Rider_Details
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Rider_Details (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(100) NOT NULL,
    mobile         VARCHAR(15)  NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    account_status ENUM('Active','Suspended') NOT NULL DEFAULT 'Active',
    registered_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
--  Driver_Details
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Driver_Details (
    id             INT          AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(100) NOT NULL,
    mobile         VARCHAR(15)  NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    car_make       VARCHAR(100) NOT NULL,
    car_model      VARCHAR(100) NOT NULL,
    reg_number     VARCHAR(50)  NOT NULL UNIQUE,
    aadhaar_number CHAR(12)     NOT NULL,
    account_status ENUM('Active','Suspended') NOT NULL DEFAULT 'Active',
    registered_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    profile_photo_b64 MEDIUMTEXT DEFAULT NULL
);

-- ------------------------------------------------------------
--  Trip_Details
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS Trip_Details (
    id               INT           AUTO_INCREMENT PRIMARY KEY,
    pickup_location  VARCHAR(255)  NOT NULL,
    drop_location    VARCHAR(255)  NOT NULL,
    distance_km      DECIMAL(8,2)  NOT NULL,
    fare             DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    ride_date        DATE          NOT NULL,
    ride_time        TIME          NOT NULL,
    status           ENUM('Confirmed','Completed') NOT NULL DEFAULT 'Confirmed',
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
