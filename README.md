# DB_Project

## Project Overview

This project involves the design and implementation of a database system for book rental management. Each table manages information related to books, users, rental records, and reservations, providing a structured approach to the core functionalities of the system.

---

## Use
- **Python**, **JavaScript**, **HTML**, **CSS**

## Table Descriptions

### **Book** - Table for Book Information

This table stores basic information about books.

| Column Name        | Data Type   | Description                        |
|--------------------|-------------|------------------------------------|
| `author`           | `TEXT`      | Author's name (**PRIMARY KEY**)    |
| `keyword`          | `TEXT`      | Keywords associated with the book  |
| `title`            | `TEXT`      | Book title                         |
| `published_year`   | `INT`       | Year of publication                |
| `ISBN`             | `TEXT`      | ISBN of the book                   |
| `Available_rent`   | `INT`       | Availability for rent (1: Yes, 0: No) |

---

### **User** - Table for User Information

This table manages user information.

| Column Name        | Data Type   | Description                                   |
|--------------------|-------------|----------------------------------------------|
| `id`               | `TEXT`      | User ID (**PRIMARY KEY**)                    |
| `password`         | `TEXT`      | User password                                |
| `name`             | `TEXT`      | User name                                    |
| `email`            | `TEXT`      | User email (used for password recovery)      |
| `available`        | `INT`       | Rental availability status (1: Yes, 0: No)  |
| `overdue_count`    | `INT`       | Number of overdue days (0 if none)           |

---

### **Rental** - Table for Rental Records

This table manages book rental information.

| Column Name        | Data Type   | Description                                   |
|--------------------|-------------|----------------------------------------------|
| `RentalID`         | `INT`       | Rental record ID (**PRIMARY KEY**)           |
| `RentalDate`       | `TEXT`      | Date when the book was rented                |
| `Rent_ISBN`        | `TEXT`      | ISBN of the rented book (refers to `Book`, **FORIEGN KEY**)   |
| `User_ID`          | `TEXT`      | User ID who rented the book (refers to `User`, **FORIEGN KEY**) |
| `DueDate`          | `TEXT`      | Expected return date                         |

---

### **Reserve** - Table for Reservation Information

This table manages reservation information for unavailable books.

| Column Name        | Data Type   | Description                                   |
|--------------------|-------------|----------------------------------------------|
| `ISBN`             | `TEXT`      | ISBN of the reserved book                    |
| `User_id`          | `TEXT`      | ID of the user who reserved the book         |
| `Reserve_date`     | `TEXT`      | Date when the reservation was made           |

---

## Key Features

- **Book Management**: The `Book` table allows for seamless management of book information, including availability for rental.
- **User Management**: The `User` table keeps track of user credentials, rental eligibility, and overdue records.
- **Rental Management**: The `Rental` table provides detailed logs of borrowed books, their due dates, and the borrowing user.
- **Reservation System**: The `Reserve` table allows users to reserve books that are currently unavailable.
- **Login System**: Implements a secure login system that validates user credentials and updates overdue status upon login.
- **Search Functionality**: Users can search for books by title, with results paginated for improved usability.
- **Dashboard**: Displays user-specific information, including borrowed books, overdue status, and remaining borrowable books.
- **Book Borrowing**: Enforces borrowing rules such as maximum allowed books and checks for overdue status before permitting new rentals.
- **Book Return**: Updates the database to mark books as returned and recalculates user availability status.
- **Account Deletion**: Prevents users with active loans or overdue records from deleting their accounts and clears session data upon successful deletion.
- **Error Handling**: Comprehensive database error handling ensures that transactions are rolled back in case of failures.
- **Dynamic Recommendations**: The home page dynamically recommends 10 random books available for rental.

---

## How to Use

1. **Database Setup**: Configure the database based on the schema provided above.
2. **Feature Implementation**: Implement features such as book rentals, returns, reservations, and overdue management.
3. **System Maintenance**: Regularly update reservation and overdue data to ensure data consistency.

---

