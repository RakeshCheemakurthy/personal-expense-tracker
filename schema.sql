CREATE DATABASE IF NOT EXISTS expense_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE expense_tracker;
CREATE TABLE IF NOT EXISTS transactions(
 id INT AUTO_INCREMENT PRIMARY KEY,title VARCHAR(120) NOT NULL,
 transaction_type ENUM('income','expense') NOT NULL,category VARCHAR(40) NOT NULL,
 amount DECIMAL(12,2) NOT NULL,transaction_date DATE NOT NULL,
 note VARCHAR(500) DEFAULT '',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
