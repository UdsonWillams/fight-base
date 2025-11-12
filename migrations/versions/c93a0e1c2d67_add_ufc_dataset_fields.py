"""add_ufc_dataset_fields

Revision ID: c93a0e1c2d67
Revises: 56d601f2cbfa
Create Date: 2025-11-12 18:45:32.015386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c93a0e1c2d67'
down_revision: Union[str, None] = '56d601f2cbfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar campos do dataset UFC aos lutadores
    op.add_column('fighters', sa.Column('ufcstats_id', sa.String(50), nullable=True, unique=True))
    op.add_column('fighters', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('fighters', sa.Column('stance', sa.String(50), nullable=True))  # Orthodox, Southpaw, Switch
    op.add_column('fighters', sa.Column('weight_lbs', sa.Float(), nullable=True))
    op.add_column('fighters', sa.Column('reach_inches', sa.Float(), nullable=True))
    op.add_column('fighters', sa.Column('height_inches', sa.Float(), nullable=True))
    
    # Estatísticas detalhadas do ufcstats.com
    op.add_column('fighters', sa.Column('slpm', sa.Float(), nullable=True))  # Significant Strikes Landed per Minute
    op.add_column('fighters', sa.Column('str_acc', sa.Float(), nullable=True))  # Striking Accuracy %
    op.add_column('fighters', sa.Column('sapm', sa.Float(), nullable=True))  # Significant Strikes Absorbed per Minute
    op.add_column('fighters', sa.Column('str_def', sa.Float(), nullable=True))  # Striking Defense %
    op.add_column('fighters', sa.Column('td_avg', sa.Float(), nullable=True))  # Average Takedowns per 15 min
    op.add_column('fighters', sa.Column('td_acc', sa.Float(), nullable=True))  # Takedown Accuracy %
    op.add_column('fighters', sa.Column('td_def', sa.Float(), nullable=True))  # Takedown Defense %
    op.add_column('fighters', sa.Column('sub_avg', sa.Float(), nullable=True))  # Average Submissions per 15 min
    
    # Adicionar campos do dataset UFC aos eventos
    op.add_column('events', sa.Column('ufcstats_id', sa.String(50), nullable=True, unique=True))
    
    # Adicionar campos do dataset UFC às lutas
    op.add_column('fights', sa.Column('ufcstats_id', sa.String(50), nullable=True, unique=True))
    op.add_column('fights', sa.Column('match_time_seconds', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('referee', sa.String(150), nullable=True))
    
    # Estatísticas detalhadas da luta (Red Corner - fighter1)
    op.add_column('fights', sa.Column('r_kd', sa.Integer(), nullable=True))  # Knockdowns
    op.add_column('fights', sa.Column('r_sig_str_landed', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_sig_str_attempted', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_total_str_landed', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_total_str_attempted', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_td_landed', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_td_attempted', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_sub_att', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('r_ctrl_seconds', sa.Integer(), nullable=True))
    
    # Estatísticas detalhadas da luta (Blue Corner - fighter2)
    op.add_column('fights', sa.Column('b_kd', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_sig_str_landed', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_sig_str_attempted', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_total_str_landed', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_total_str_attempted', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_td_landed', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_td_attempted', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_sub_att', sa.Integer(), nullable=True))
    op.add_column('fights', sa.Column('b_ctrl_seconds', sa.Integer(), nullable=True))
    
    # Criar índices para otimizar consultas
    op.create_index('ix_fighters_ufcstats_id', 'fighters', ['ufcstats_id'])
    op.create_index('ix_events_ufcstats_id', 'events', ['ufcstats_id'])
    op.create_index('ix_fights_ufcstats_id', 'fights', ['ufcstats_id'])


def downgrade() -> None:
    # Remover índices
    op.drop_index('ix_fights_ufcstats_id', 'fights')
    op.drop_index('ix_events_ufcstats_id', 'events')
    op.drop_index('ix_fighters_ufcstats_id', 'fighters')
    
    # Remover colunas das lutas
    op.drop_column('fights', 'b_ctrl_seconds')
    op.drop_column('fights', 'b_sub_att')
    op.drop_column('fights', 'b_td_attempted')
    op.drop_column('fights', 'b_td_landed')
    op.drop_column('fights', 'b_total_str_attempted')
    op.drop_column('fights', 'b_total_str_landed')
    op.drop_column('fights', 'b_sig_str_attempted')
    op.drop_column('fights', 'b_sig_str_landed')
    op.drop_column('fights', 'b_kd')
    op.drop_column('fights', 'r_ctrl_seconds')
    op.drop_column('fights', 'r_sub_att')
    op.drop_column('fights', 'r_td_attempted')
    op.drop_column('fights', 'r_td_landed')
    op.drop_column('fights', 'r_total_str_attempted')
    op.drop_column('fights', 'r_total_str_landed')
    op.drop_column('fights', 'r_sig_str_attempted')
    op.drop_column('fights', 'r_sig_str_landed')
    op.drop_column('fights', 'r_kd')
    op.drop_column('fights', 'referee')
    op.drop_column('fights', 'match_time_seconds')
    op.drop_column('fights', 'ufcstats_id')
    
    # Remover colunas dos eventos
    op.drop_column('events', 'ufcstats_id')
    
    # Remover colunas dos lutadores
    op.drop_column('fighters', 'sub_avg')
    op.drop_column('fighters', 'td_def')
    op.drop_column('fighters', 'td_acc')
    op.drop_column('fighters', 'td_avg')
    op.drop_column('fighters', 'str_def')
    op.drop_column('fighters', 'sapm')
    op.drop_column('fighters', 'str_acc')
    op.drop_column('fighters', 'slpm')
    op.drop_column('fighters', 'height_inches')
    op.drop_column('fighters', 'reach_inches')
    op.drop_column('fighters', 'weight_lbs')
    op.drop_column('fighters', 'stance')
    op.drop_column('fighters', 'date_of_birth')
    op.drop_column('fighters', 'ufcstats_id')
