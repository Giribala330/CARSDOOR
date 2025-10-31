
CREATE DATABASE IF NOT EXISTS carsdoor_db;
USE carsdoor_db;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role VARCHAR(20) NOT NULL,
  name VARCHAR(255),
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(512),
  address TEXT,
  phone VARCHAR(100),
  is_approved TINYINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cars (
  id INT AUTO_INCREMENT PRIMARY KEY,
  seller_id INT NULL,
  brand VARCHAR(255),
  model VARCHAR(255),
  model_year INT,
  milage VARCHAR(255),
  fuel_type VARCHAR(255),
  engine VARCHAR(255),
  transmission VARCHAR(255),
  ext_col VARCHAR(255),
  int_col VARCHAR(255),
  accident VARCHAR(255),
  clean_title VARCHAR(50),
  price VARCHAR(100),
  is_approved TINYINT DEFAULT 0,
  FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  buyer_id INT NOT NULL,
  car_id INT NOT NULL,
  seller_id INT NULL,
  status ENUM('pending','confirmed','cancelled') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  buyer_name VARCHAR(255) NULL,
  buyer_phone VARCHAR(100) NULL,
  buyer_address TEXT NULL,
  delivery_date DATE NULL,
  FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);

-- Seed admin user (email: admin@carsdoor.com, password: admin123)
INSERT IGNORE INTO users (role, name, email, password_hash, is_approved) VALUES
('admin', 'Administrator', 'admin@carsdoor.com', 'scrypt:32768:8:1$pgXrU0yHLahh126p$8aab6b978b48039fef4a0d3ac3e70f51ead0aceb7b2e52f04f0dd0edfc539a43c3dab8d0c2423aee2f6cf5fb3ff880441797e0052e61564ea7768625b09f82a0', 1);
