USE product_inquiry;
GO

CREATE TABLE lights_product_inquiry (
    id INT IDENTITY(1,1) PRIMARY KEY,
    image_url NVARCHAR(MAX),
    source NVARCHAR(255),
    product_category_id NVARCHAR(255),
    product_category NVARCHAR(255),
    product_description NVARCHAR(MAX),
    british_columbia NVARCHAR(255),
    manitoba NVARCHAR(255),
    ontario NVARCHAR(255),
    prince_edward_island NVARCHAR(255),
    quebec NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);
GO