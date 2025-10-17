"""Add missing columns to clientes

Revision ID: 1bf7abd00725
Revises: 6b6f61bcc352
Create Date: 2025-10-17 11:04:33.289815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1bf7abd00725'
down_revision: Union[str, None] = '6b6f61bcc352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Agregar columnas faltantes a la tabla clientes
    op.add_column('clientes', sa.Column('es_moroso', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('clientes', sa.Column('deuda_actual', sa.DECIMAL(10, 2), nullable=True, server_default='0'))
    op.add_column('clientes', sa.Column('ultima_fecha_pago', sa.DateTime(), nullable=True))
    op.add_column('clientes', sa.Column('dias_mora', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Revertir cambios
    op.drop_column('clientes', 'dias_mora')
    op.drop_column('clientes', 'ultima_fecha_pago')
    op.drop_column('clientes', 'deuda_actual')
    op.drop_column('clientes', 'es_moroso')
