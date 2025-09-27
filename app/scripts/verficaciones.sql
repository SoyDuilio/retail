
-- VERIFICACION FINAL
SELECT 'Productos por categoria' as reporte;
SELECT c.nombre as categoria, COUNT(p.producto_id) as productos, 
       MIN(p.precio_unitario) as precio_min, MAX(p.precio_unitario) as precio_max,
       SUM(p.stock_actual) as stock_total
FROM categorias c 
LEFT JOIN productos p ON c.categoria_id = p.categoria_id 
GROUP BY c.categoria_id, c.nombre
ORDER BY c.categoria_id;

SELECT 'Clientes por tipo' as reporte;
SELECT tipo_cliente, COUNT(*) as cantidad FROM clientes GROUP BY tipo_cliente;

SELECT 'Resumen general' as reporte;
SELECT 'Productos' as tabla, COUNT(*) as total FROM productos
UNION ALL
SELECT 'Clientes' as tabla, COUNT(*) as total FROM clientes
UNION ALL  
SELECT 'Categorias' as tabla, COUNT(*) as total FROM categorias;

-- PRODUCTOS DESTACADOS
SELECT 'Productos destacados' as reporte;
SELECT codigo_producto, nombre, precio_unitario FROM productos WHERE destacado = true ORDER BY precio_unitario DESC;