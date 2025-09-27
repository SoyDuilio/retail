# database.py
from sqlalchemy import create_engine, MetaData, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool
import os
from typing import Generator
from datetime import datetime, timedelta, timezone

# =============================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================

# URL de conexión (Railway PostgreSQL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:duilia@localhost:5432/pedidos?client_encoding=utf8"
)

# Configuración del engine
engine = create_engine(
    DATABASE_URL,
    poolclass=pool.NullPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Cambiar a True para debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos SQLAlchemy
Base = declarative_base()

# =============================================
# DEPENDENCY INJECTION
# =============================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database error: {e}")
        if db:
            try:
                db.rollback()
            except:
                pass
        raise
    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                print(f"Error closing DB: {e}")

# =============================================
# UTILIDADES DE BASE DE DATOS
# =============================================

def create_tables():
    """Crear todas las tablas"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Eliminar todas las tablas"""
    Base.metadata.drop_all(bind=engine)

def get_db_info():
    """Obtener información de la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            return {
                "status": "connected",
                "version": version,
                "url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "localhost"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

