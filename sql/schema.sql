CREATE DATABASE IF NOT EXISTS ecopulse;
USE ecopulse;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'building_manager', 'occupant') NOT NULL DEFAULT 'occupant'
) ENGINE=InnoDB;

CREATE TABLE buildings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(150),
    area_sqm FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id INT NOT NULL,
    occupant_id INT NULL,
    room_name VARCHAR(100),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (occupant_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE energy_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    `timestamp` DATETIME NOT NULL,
    energy_consumed_kwh FLOAT NOT NULL,
    indoor_temp FLOAT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_logs_room_time ON energy_logs(room_id, `timestamp`);