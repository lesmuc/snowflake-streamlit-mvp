-- =============================================================================
-- Tasty Bytes — MENU table setup (self-contained, no S3 required)
-- Run in Snowsight as ACCOUNTADMIN.
-- =============================================================================

USE WAREHOUSE COMPUTE_WH;
USE DATABASE  SNOWFLAKE_LEARNING_DB;
USE SCHEMA    LESMUC_LOAD_SAMPLE_DATA_FROM_S3;

-- ---------------------------------------------------------------------------
-- STEP 1: Create the MENU table
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE menu (
    menu_id                         NUMBER(19,0)    NOT NULL,
    menu_type_id                    NUMBER(38,0),
    menu_type                       VARCHAR(16777216),
    truck_brand_name                VARCHAR(16777216),
    menu_item_id                    NUMBER(38,0),
    menu_item_name                  VARCHAR(16777216),
    item_category                   VARCHAR(16777216),
    item_subcategory                VARCHAR(16777216),
    cost_of_goods_usd               NUMBER(38,4),
    sale_price_usd                  NUMBER(38,4),
    menu_item_health_metrics_obj    VARIANT
);

-- ---------------------------------------------------------------------------
-- STEP 2: Insert sample Tasty Bytes menu data
-- ---------------------------------------------------------------------------
INSERT INTO menu
    (menu_id, menu_type_id, menu_type, truck_brand_name,
     menu_item_id, menu_item_name, item_category, item_subcategory,
     cost_of_goods_usd, sale_price_usd, menu_item_health_metrics_obj)
SELECT
    column1, column2, column3, column4,
    column5, column6, column7, column8,
    column9, column10,
    TRY_PARSE_JSON(column11)
FROM VALUES
-- Freezing Point
(1,  1,'Ice Cream','Freezing Point', 101,'Mango Sorbet',       'Dessert','Cold Options',  1.50,  5.00, '{"menu_item_health_metrics":[{"calories":180,"ingredients":["mango","sugar","water"]}]}'),
(2,  1,'Ice Cream','Freezing Point', 102,'Chocolate Ice Cream','Dessert','Cold Options',  1.80,  5.50, '{"menu_item_health_metrics":[{"calories":250,"ingredients":["cream","chocolate","sugar"]}]}'),
(3,  1,'Ice Cream','Freezing Point', 103,'Vanilla Cone',       'Dessert','Cold Options',  1.20,  4.50, '{"menu_item_health_metrics":[{"calories":200,"ingredients":["cream","vanilla","sugar"]}]}'),
(4,  1,'Ice Cream','Freezing Point', 104,'Strawberry Shake',   'Beverage','Shakes',       2.00,  6.00, '{"menu_item_health_metrics":[{"calories":380,"ingredients":["milk","strawberry","ice cream"]}]}'),
-- The Mac Shack
(5,  2,'Mac & Cheese','The Mac Shack', 201,'Classic Mac',      'Main','Mac & Cheese',     2.50,  8.00, '{"menu_item_health_metrics":[{"calories":520,"ingredients":["pasta","cheddar","milk","butter"]}]}'),
(6,  2,'Mac & Cheese','The Mac Shack', 202,'Truffle Mac',      'Main','Mac & Cheese',     3.50, 12.00, '{"menu_item_health_metrics":[{"calories":610,"ingredients":["pasta","gruyere","truffle oil","cream"]}]}'),
(7,  2,'Mac & Cheese','The Mac Shack', 203,'BBQ Bacon Mac',    'Main','Mac & Cheese',     3.20, 11.00, '{"menu_item_health_metrics":[{"calories":680,"ingredients":["pasta","cheddar","bacon","bbq sauce"]}]}'),
(8,  2,'Mac & Cheese','The Mac Shack', 204,'Mac Bites',        'Snack','Sides',           1.50,  5.50, '{"menu_item_health_metrics":[{"calories":290,"ingredients":["pasta","cheddar","breadcrumbs"]}]}'),
-- Guac n Roll
(9,  3,'Mexican','Guac n'' Roll', 301,'Classic Burrito',   'Main','Burritos',             2.80,  9.00, '{"menu_item_health_metrics":[{"calories":650,"ingredients":["tortilla","rice","beans","salsa"]}]}'),
(10, 3,'Mexican','Guac n'' Roll', 302,'Guacamole Bowl',    'Main','Bowls',                3.00, 10.50, '{"menu_item_health_metrics":[{"calories":480,"ingredients":["avocado","cilantro","lime","onion"]}]}'),
(11, 3,'Mexican','Guac n'' Roll', 303,'Chicken Tacos',     'Main','Tacos',                2.50,  8.50, '{"menu_item_health_metrics":[{"calories":420,"ingredients":["tortilla","chicken","salsa","lime"]}]}'),
(12, 3,'Mexican','Guac n'' Roll', 304,'Chips & Guac',      'Snack','Sides',               1.20,  5.00, '{"menu_item_health_metrics":[{"calories":320,"ingredients":["tortilla chips","avocado","lime","salt"]}]}'),
-- Cheeky Greek
(13, 4,'Greek','Cheeky Greek', 401,'Gyro Wrap',            'Main','Wraps',                2.50,  9.00, '{"menu_item_health_metrics":[{"calories":540,"ingredients":["pita","lamb","tzatziki","tomato"]}]}'),
(14, 4,'Greek','Cheeky Greek', 402,'Greek Salad',          'Starter','Salads',            1.80,  7.50, '{"menu_item_health_metrics":[{"calories":280,"ingredients":["cucumber","tomato","feta","olives"]}]}'),
(15, 4,'Greek','Cheeky Greek', 403,'Spanakopita',          'Snack','Pastries',            1.50,  6.00, '{"menu_item_health_metrics":[{"calories":310,"ingredients":["filo pastry","spinach","feta"]}]}'),
(16, 4,'Greek','Cheeky Greek', 404,'Lamb Souvlaki',        'Main','Grills',               3.20, 11.00, '{"menu_item_health_metrics":[{"calories":490,"ingredients":["lamb","lemon","oregano","garlic"]}]}'),
-- Plant Palace
(17, 5,'Vegan','Plant Palace', 501,'Impossible Burger',    'Main','Burgers',              3.50, 11.00, '{"menu_item_health_metrics":[{"calories":430,"ingredients":["plant patty","lettuce","tomato","bun"]}]}'),
(18, 5,'Vegan','Plant Palace', 502,'Vegan Buddha Bowl',    'Main','Bowls',                3.00,  9.50, '{"menu_item_health_metrics":[{"calories":380,"ingredients":["quinoa","chickpeas","avocado","kale"]}]}'),
(19, 5,'Vegan','Plant Palace', 503,'Lentil Soup',          'Starter','Soups',             1.20,  5.00, '{"menu_item_health_metrics":[{"calories":210,"ingredients":["lentils","carrot","cumin","onion"]}]}'),
(20, 5,'Vegan','Plant Palace', 504,'Acai Smoothie',        'Beverage','Smoothies',        2.00,  7.00, '{"menu_item_health_metrics":[{"calories":290,"ingredients":["acai","banana","almond milk"]}]}'),
-- Smoky BBQ
(21, 6,'BBQ','Smoky BBQ', 601,'Pulled Pork Sandwich',      'Main','Sandwiches',           3.00, 10.00, '{"menu_item_health_metrics":[{"calories":620,"ingredients":["brioche","pulled pork","coleslaw","bbq sauce"]}]}'),
(22, 6,'BBQ','Smoky BBQ', 602,'BBQ Ribs Half Rack',        'Main','Grills',               5.00, 16.00, '{"menu_item_health_metrics":[{"calories":820,"ingredients":["pork ribs","bbq sauce","spice rub"]}]}'),
(23, 6,'BBQ','Smoky BBQ', 603,'Smoked Brisket Plate',      'Main','Grills',               5.50, 17.00, '{"menu_item_health_metrics":[{"calories":750,"ingredients":["beef brisket","salt","pepper","smoke"]}]}'),
(24, 6,'BBQ','Smoky BBQ', 604,'Corn on the Cob',           'Snack','Sides',               0.80,  3.50, '{"menu_item_health_metrics":[{"calories":130,"ingredients":["corn","butter","salt"]}]}'),
-- Kitakata Ramen Bar
(25, 7,'Japanese','Kitakata Ramen Bar', 701,'Tonkotsu Ramen',   'Main','Ramen',           3.20, 12.00, '{"menu_item_health_metrics":[{"calories":580,"ingredients":["ramen","pork broth","chashu","egg"]}]}'),
(26, 7,'Japanese','Kitakata Ramen Bar', 702,'Miso Ramen',       'Main','Ramen',           2.80, 11.00, '{"menu_item_health_metrics":[{"calories":520,"ingredients":["ramen","miso","tofu","nori"]}]}'),
(27, 7,'Japanese','Kitakata Ramen Bar', 703,'Gyoza (6 pcs)',    'Starter','Dumplings',    1.50,  6.50, '{"menu_item_health_metrics":[{"calories":240,"ingredients":["pork","cabbage","ginger","wrapper"]}]}'),
(28, 7,'Japanese','Kitakata Ramen Bar', 704,'Matcha Ice Cream', 'Dessert','Cold Options', 1.20,  5.00, '{"menu_item_health_metrics":[{"calories":190,"ingredients":["cream","matcha","sugar"]}]}'),
-- Pani''s Pizza
(29, 8,'Pizza','Pani''s Pizza', 801,'Margherita Pizza',    'Main','Pizza',                3.00, 10.00, '{"menu_item_health_metrics":[{"calories":700,"ingredients":["dough","tomato","mozzarella","basil"]}]}'),
(30, 8,'Pizza','Pani''s Pizza', 802,'Pepperoni Pizza',     'Main','Pizza',                3.50, 11.00, '{"menu_item_health_metrics":[{"calories":800,"ingredients":["dough","tomato","mozzarella","pepperoni"]}]}'),
(31, 8,'Pizza','Pani''s Pizza', 803,'Garlic Bread',        'Snack','Sides',               0.60,  3.50, '{"menu_item_health_metrics":[{"calories":250,"ingredients":["bread","garlic","olive oil"]}]}'),
(32, 8,'Pizza','Pani''s Pizza', 804,'Tiramisu',            'Dessert','Cakes',             1.50,  6.00, '{"menu_item_health_metrics":[{"calories":340,"ingredients":["mascarpone","espresso","ladyfingers","cocoa"]}]}');

-- ---------------------------------------------------------------------------
-- STEP 3: Verify
-- ---------------------------------------------------------------------------
SELECT COUNT(*) AS row_count FROM menu;
SELECT truck_brand_name, COUNT(*) AS items FROM menu GROUP BY 1 ORDER BY 1;
