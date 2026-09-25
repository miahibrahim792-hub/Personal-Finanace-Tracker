# Personal Finance Tracker

A full-stack personal finance tracking web application built using Python, Flask, SQLite, HTML, CSS and JavaScript.

The application allows users to securely create an account, record their income and expenses, analyse spending habits and download their transaction history.

I built this project to develop my understanding of backend development, databases, authentication and full-stack web development.

## Live Demo

[View the live application](https://mohammedmiah.pythonanywhere.com/)

## Features

- User registration and login
- Secure password hashing
- Separate transaction data for each user
- Add income and expense transactions
- Edit existing transactions
- Delete transactions
- Automatic balance calculation
- Total income and expense summaries
- Search transactions by category or description
- Filter by:
  - Income or expense
  - Category
  - Start date
  - End date
- Pagination for transaction history
- Spending by category chart
- Monthly income vs expenses chart
- Download transaction statements as CSV files
- Light and dark mode
- Responsive layout for desktop and mobile devices

## Technologies Used

### Backend

- Python
- Flask
- SQLite
- Werkzeug password hashing

### Frontend

- HTML
- CSS
- JavaScript
- Chart.js

### Development Tools

- Visual Studio Code
- Git
- GitHub

## How It Works

Each user can create their own account and log into the application.

Passwords are hashed before being stored in the SQLite database.

Transactions are linked to the currently logged-in user using a user ID. This ensures that users can only view, edit and delete their own transactions.

The dashboard calculates total income, total expenses and the current balance using SQL queries.

Chart.js is used to display spending data visually.

Users can also filter their transactions and download the matching transaction history as a CSV statement.

## Database

The application uses SQLite with two main tables.

### Users

Stores:

- User ID
- Username
- Hashed password

### Transactions

Stores:

- Transaction ID
- User ID
- Transaction type
- Amount
- Category
- Description
- Timestamp

The `user_id` connects each transaction to the account that created it.

## Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/miahibrahim792-hub/Personal-Finance-Tracker.git