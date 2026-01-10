INSERT INTO categories (name, description) VALUES
    ('Electronics', 'Electronic devices and accessories'),
    ('Clothing', 'Apparel and fashion items'),
    ('Books', 'Physical and digital books'),
    ('Home & Garden', 'Home improvement and garden supplies'),
    ('Sports', 'Sports equipment and fitness gear');

-- Insert Customers
INSERT INTO customers (name, email, address) VALUES
    ('Alice Johnson', 'alice@example.com', '123 Main St, New York, NY 10001'),
    ('Bob Smith', 'bob@example.com', '456 Oak Ave, Los Angeles, CA 90001'),
    ('Charlie Brown', 'charlie@example.com', '789 Pine Rd, Chicago, IL 60601'),
    ('Diana Prince', 'diana@example.com', '321 Elm St, Houston, TX 77001'),
    ('Eve Davis', 'eve@example.com', '654 Maple Dr, Phoenix, AZ 85001'),
    ('Frank Miller', 'frank@example.com', '987 Cedar Ln, Philadelphia, PA 19101'),
    ('Grace Lee', 'grace@example.com', '147 Birch Ct, San Antonio, TX 78201'),
    ('Henry Wilson', 'henry@example.com', '258 Spruce Way, San Diego, CA 92101');


INSERT INTO products (name, category_id, price, stock_quantity, metadata) VALUES
    -- Electronics
    ('Laptop Pro 15"', 1, 1299.99, 50, '{"brand": "TechCorp", "color": "Silver", "ram": "16GB", "storage": "512GB SSD"}'),
    ('Wireless Mouse', 1, 29.99, 200, '{"brand": "ClickMaster", "color": "Black", "wireless": true, "dpi": 1600}'),
    ('USB-C Hub', 1, 49.99, 150, '{"brand": "ConnectPlus", "ports": 7, "color": "Gray"}'),
    ('Bluetooth Headphones', 1, 199.99, 100, '{"brand": "SoundWave", "color": "Black", "noise_cancelling": true, "battery_hours": 30}'),
    ('4K Monitor 27"', 1, 399.99, 75, '{"brand": "ViewMaster", "resolution": "3840x2160", "refresh_rate": "60Hz", "panel_type": "IPS"}'),
    
    -- Clothing
    ('Cotton T-Shirt', 2, 19.99, 500, '{"brand": "ComfyWear", "sizes": ["S", "M", "L", "XL"], "color": "Blue", "material": "100% Cotton"}'),
    ('Denim Jeans', 2, 59.99, 300, '{"brand": "DenimCo", "sizes": ["28", "30", "32", "34", "36"], "color": "Dark Blue", "fit": "Slim"}'),
    ('Running Shoes', 2, 89.99, 150, '{"brand": "SpeedFit", "sizes": ["8", "9", "10", "11"], "color": "Red/White", "type": "Athletic"}'),
    ('Winter Jacket', 2, 129.99, 100, '{"brand": "WarmGear", "sizes": ["S", "M", "L", "XL"], "color": "Black", "insulation": "Down"}'),
    
    -- Books
    ('Python Programming Guide', 3, 39.99, 200, '{"author": "John Doe", "pages": 450, "format": "Paperback", "isbn": "978-1234567890"}'),
    ('Database Design Fundamentals', 3, 49.99, 150, '{"author": "Jane Smith", "pages": 380, "format": "Hardcover", "isbn": "978-0987654321"}'),
    ('Web Development Mastery', 3, 44.99, 180, '{"author": "Mike Johnson", "pages": 520, "format": "Paperback", "isbn": "978-1122334455"}'),
    
    -- Home & Garden
    ('LED Desk Lamp', 4, 34.99, 250, '{"brand": "BrightLight", "color": "White", "adjustable": true, "power": "12W"}'),
    ('Garden Tool Set', 4, 79.99, 120, '{"brand": "GreenThumb", "pieces": 10, "material": "Stainless Steel"}'),
    ('Indoor Plant Pot', 4, 24.99, 300, '{"brand": "PlantHome", "size": "Medium", "color": "Terracotta", "drainage": true}'),
    
    -- Sports
    ('Yoga Mat', 5, 29.99, 200, '{"brand": "FlexFit", "thickness": "6mm", "color": "Purple", "material": "TPE"}'),
    ('Dumbbell Set', 5, 149.99, 80, '{"brand": "IronGrip", "weight": "20kg", "adjustable": true, "pieces": 2}'),
    ('Tennis Racket', 5, 119.99, 90, '{"brand": "AcePro", "weight": "300g", "grip_size": "4", "string_pattern": "16x19"}');
