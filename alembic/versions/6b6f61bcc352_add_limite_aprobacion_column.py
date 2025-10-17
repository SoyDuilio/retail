"""Add limite_aprobacion column

Revision ID: 6b6f61bcc352
Revises: 195f28da422b
Create Date: 2025-10-17 10:49:21.520277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b6f61bcc352'
down_revision: Union[str, None] = '195f28da422b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Agregar columna limite_aprobacion si no existe
    op.add_column('evaluadores', 
        sa.Column('limite_aprobacion', sa.DECIMAL(10, 2), nullable=True)
    )

def downgrade():
    op.drop_column('evaluadores', 'limite_aprobacion')