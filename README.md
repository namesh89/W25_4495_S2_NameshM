# W25_4495_S2_NameshM

## Project Name: Automated Product Inquiry Response System for Light Recycling Program

## Team Members:
- **Namesh Mathara Arachchi Vidanalage**
      Student ID: 300359798
      College Email: matharaarachchn@student.douglascollege.ca
      GitHub Email: nameshm89@gmail.com

## Repository Structure:
- `ReportsAndDocuments/` - Contains reports, proposals, and documentation.
- `Implementation/` - Contains all project code.
- `Misc/` - Any other necessary files.

## Instructor Access:
- The instructor (kandhadaip@douglascollege.ca) has been added as a collaborator.

## Link to Work Logs Sheet:
https://docs.google.com/spreadsheets/d/e/2PACX-1vQHzTs37sCeaieNgDgVua_POXXQw7Bqi2WpS2cD0IhkMsDLo6qHOgV9K5LdETz7IfWTbCgdNkFj1DPK/pubhtml

## About the Company:
Product Care Recycling is an industry-led organization working to protect the environment by providing free recycling services for post-consumer paint, household hazardous waste, lights, and alarms. They divert post-consumer products from Canada’s landfills and waterways, ensuring they are managed responsibly at their end-of-life. They are a federally incorporated not-for-profit organization and provide recycling services across nine Canadian provinces. Product Care Recycling encourages individuals and businesses to reduce their waste and reuse when possible, and they provide recycling solutions for post-consumer products.

What they do
- Provide recycling locations for end users to drop off their recyclable products.
- Develop transportation systems to remove recyclable waste safely and efficiently.
- Educate communities about available recycling programs and where to take their recyclable products at end-of-life.
- Work with recycling experts to ensure industry-leading material processing and recycling occurs.


## Project Description

**Automated Product Inquiry Response System for Light Recycling Program (APIRS)** is a **Flask-based application** designed to automate and streamline the product inquiry process using **machine learning** (A typical product inquiry seeks information about the category of a product within the recycling program). The system enables members to submit product inquiries - including product name, description, and image - which are then processed using an **ML model** that performs **text and image similarity matching** against existing products in product guide. The results are stored in **Azure Table Storage** and **Azure Blob Storage**, where administrators can review and approve the suggested product category.

#### Purpose of the Project

PCA handles a significant number of product inquiries daily, requiring significant manual effort to categorize and respond to each one. This project aims to **automate product inquiry processing** by leveraging **machine learning techniques** to match incoming inquiries with existing product data. The system provides:

- A **user-friendly web interface** for members to submit product inquiries.
- **Automated backend processing** to analyze and match the products.
- A **review system** where admins can verify and approve the assigned product categories.

#### Benefits of the System

- **Automation**: Reduces the manual workload of categorizing product inquiries.  
- **Efficiency**: Quickly processes and categorizes inquiries using AI.  
- **Accuracy**: Uses machine learning to ensure precise product matching.  
- **Scalability**: Can handle large volumes of inquiries as the business grows.  
- **User-friendly Interface**: Both members and admins can easily interact with the system.  

