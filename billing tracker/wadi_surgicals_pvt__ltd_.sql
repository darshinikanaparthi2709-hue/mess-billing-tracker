-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 20, 2026 at 03:50 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `messdb`
--

-- --------------------------------------------------------

--
-- Table structure for table `wadi surgicals pvt. ltd.`
--

CREATE TABLE `wadi surgicals pvt. ltd.` (
  `SNO` int(11) NOT NULL AUTO_INCREMENT,
  `MEAL_TYPE` varchar(50) NOT NULL,
  `DESCRIPTION` varchar(255) NOT NULL,
  `NO_OF_PERSONS` int(11) NOT NULL,
  `DAYS` int(11) NOT NULL,
  `TOTAL_MEALS` int(11) NOT NULL,
  `RATE` decimal(10,2) NOT NULL,
  `AMOUNT` decimal(10,2) NOT NULL,
  `BILL_MONTH` varchar(50) NOT NULL,
  PRIMARY KEY (`SNO`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `wadi surgicals pvt. ltd.`
--

INSERT INTO `wadi surgicals pvt. ltd.` (`SNO`, `MEAL_TYPE`, `DESCRIPTION`, `NO_OF_PERSONS`, `DAYS`, `TOTAL_MEALS`, `RATE`, `AMOUNT`, `BILL_MONTH`) VALUES
(1, 'VEG MEALS', '19', 6, 1, 6, 70.00, 420.00, 'May 2026'),
(2, 'CHICKEN MEALS', '20', 1, 1, 1, 100.00, 100.00, 'May 2026'),
(3, 'MUTTON', '19', 5, 1, 5, 250.00, 1250.00, 'May 2026');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
