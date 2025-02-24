# Project Installation Instructions

## Project Overview

This repository (**W25_4495_S2_NameshM**) is a mono-repo containing the code for a Python-based application that automates product inquiry processing using machine learning. The project consists of a **Flask**-based frontend and backend, integrated with **Azure Blob Storage** for storing images and **Azure Table Storage** for text-based data.

## Technology Stack
- **Frontend**: Flask + Bootstrap (UI)
- **Backend**: Flask, Azure Blob Storage (image storage), Azure Table Storage (text data storage)
- **ML Model**: Python-based ML model for product similarity matching
- **Programming Language**: Python

## Project Structure
- `back_end/` - Contains the backend application
- `front_end/` - Contains the frontend application
- `ml_model/` - Contains the machine learning model
- `product_upload/` - Handles product guide data uploads - **This is a one-time task needs to be done at the beginning of the project**

![image](https://github.com/namesh89/W25_4495_S2_NameshM/blob/main/Misc/Project%20Repository%20Hierarchy.png)


## Installation Guide

### Prerequisites
Ensure you have the following installed:
- **Python (>=3.9)** - Install from [python.org](https://www.python.org/)
- **pip** - Installed with Python
- **Git** - Install from [git-scm.com](https://git-scm.com/)

### Clone the Repository
```sh
git clone https://github.com/namesh89/W25_4495_S2_NameshM.git
```

### Setup Virtual Environment & Install Dependencies for Each Module
```sh
cd W25_4495_S2_NameshM/Implementation/back_end
python -m venv venv
# Activate virtual environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
pip install -r requirements.txt
```
```sh
cd ../front_end
python -m venv venv
# Activate virtual environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
pip install -r requirements.txt
```
```sh
cd ../ml_model
python -m venv venv
# Activate virtual environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### Set Up Environment Variables for Each Module
**The actual values of these variables are NOT given here due to security concerns**

Create a `.env` file inside the `back_end` directory and configure the following:
```sh
AZURE_STORAGE_ACCOUNT_NAME=azure_storage_account_name
AZURE_STORAGE_ACCOUNT_KEY=azure_storage_account_key
AZURE_STORAGE_CONNECTION_STRING=azure_storage_connection_string
JWT_SECRET_KEY=jwt_secret_key
ML_MODEL_URL=ml_model_url
```
Create a `.env` file inside the `front_end` directory and configure the following:
```sh
SECRET_KEY=secret_key
BACKEND_URL=backend_url
AZURE_STORAGE_ACCOUNT=azure_storage_account
AZURE_STORAGE_KEY=azure_storage_key
AZURE_CONTAINER_NAME=azure_container_name
AZURE_UPLOAD_FOLDER=azure_upload_folder
```
Create a `.env` file inside the `ml_model` directory and configure the following:
```sh
SECRET_KEY=secret_key
BACKEND_URL=backend_url
APIRS_SERVICE_API_URL=apirs_service_api_url
AZURE_STORAGE_ACCOUNT_NAME=azure_storage_account_name
AZURE_STORAGE_ACCOUNT_KEY=azure_storage_account_key
AZURE_STORAGE_CONNECTION_STRING=azure_storage_connection_string
```

## Creating user accounts

### Creating admin account
```sh
cd back_end
python add_user.py
```
Enter `admin@test.com` as email when prompted and a suitable password.

### Creating member accounts
```sh
python add_user.py
```
Enter member's email (e.g. `member1@test.com`) as email when prompted and a suitable password.

## Running the Applications

### Start the Backend in a new terminal
```sh
cd back_end
python app.py
```
The backend should now be running on `http://127.0.0.1:5000`

### Start the Frontend in a new terminal
```sh
cd front_end
python app.py
```
The frontend should now be running on `http://127.0.0.1:5001`

### Start the ML Model API in a new terminal
```sh
cd ml_model
python app.py
```
The ML Model API should now be running on `http://127.0.0.1:5002`

## Running a Demo
1. **Upload a Product Inquiry**
   - Use the frontend UI (`http://127.0.0.1:5001`) to login as a member and submit a product inquiry (name, description, and image). You can also view the submitted product inquries and approved product inquries.
2. **Processing the Inquiry**
   - The backend API (`http://127.0.0.1:5000`) processes the inquiry and store the data in Azure Table Storage (text) and Azure Blob Storage (image) then submits those data to Ml model.
   - The ML model (`http://127.0.0.1:5002`) performs text and image similarity matching to find the most-matched product from existing data and then passes its product category to update the same Azure Table Storage.
3. **Approve the Product Category**
   - Use the frontend UI (`http://127.0.0.1:5001`) to login as the admin and view pending product inquiries submitted by members. You can then review and approve the product category passed by the ML model. Once you approve, you can also view the approved product inquries.

## Deployment
For production deployment, use **Gunicorn** and **Azure App Services**:
```sh
gunicorn --workers=3 --bind 0.0.0.0:5000 run:app
```
For Azure-specific deployment steps, refer to Azure's [Flask deployment guide](https://docs.microsoft.com/en-us/azure/app-service/quickstart-python).

## Contributing
1. Fork the repository.
2. Create a feature branch:
   ```sh
   git checkout -b feature-branch
   ```
3. Commit your changes:
   ```sh
   git commit -m "Added new feature"
   ```
4. Push to the branch:
   ```sh
   git push origin feature-branch
   ```
5. Submit a pull request for review.
