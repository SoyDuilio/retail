-- SCRIPT 2: INSERTAR DATOS DE PRUEBA
-- Insertar vendedores de prueba (password = mismo DNI)
INSERT INTO vendedores (dni, codigo_vendedor, nombre, apellidos, telefono, email, password_hash, verificado) VALUES
('12345678', 'VEN001', 'Juan', 'Pérez García', '987654321', 'juan.perez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$8f5e65c2a1e4b7f9d3c6a8e2b5f8c1d4a7e3b6f9c2e5a8b1d4c7e0a3b6c9e2f5', true),
('87654321', 'VEN002', 'María', 'González López', '987654322', 'maria.gonzalez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', true),
('11223344', 'VEN003', 'Carlos', 'Rodríguez Vega', '987654323', 'carlos.rodriguez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c', true);

-- Insertar evaluadores de prueba
INSERT INTO evaluadores (dni, codigo_evaluador, nombre, apellidos, telefono, email, password_hash, verificado) VALUES
('22334455', 'EVA001', 'Ana', 'Martínez Silva', '987654331', 'ana.martinez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d', true),
('33445566', 'EVA002', 'Luis', 'Fernández Torres', '987654332', 'luis.fernandez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e', true);

-- Insertar supervisores de prueba
INSERT INTO supervisores (dni, codigo_supervisor, nombre, apellidos, telefono, email, password_hash, nivel_acceso, verificado) VALUES
('44556677', 'SUP001', 'Roberto', 'Jiménez Castro', '987654341', 'roberto.jimenez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f', 'gerente', true),
('55667788', 'SUP002', 'Carmen', 'López Herrera', '987654342', 'carmen.lopez@empresa.com', 'scrypt:32768:8:1$KjX4P9L3kRvN2mB8$6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a', 'supervisor', true);
