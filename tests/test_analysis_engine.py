from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User
from app.models.case import Case
from app.models.actor import Actor, ActorPowerDimension, ActorInterest, ActorObjective, ActorRelationship, ActorPosition
from app.services.analysis import recommend_methods, run_analysis, mactor, network_metrics


def seeded_session():
    eng=create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(eng)
    S=sessionmaker(bind=eng); s=S()
    u=User(id='u1', external_auth_id='dev-u1', email='a@example.com'); s.add(u)
    c=Case(id='c1', owner_id='u1', title='case', description='x', status='active'); s.add(c)
    a=Actor(id='a',case_id='c1',canonical_name='Actor A',normalized_name='actor a',actor_type='organization',overall_confidence=.8)
    b=Actor(id='b',case_id='c1',canonical_name='Actor B',normalized_name='actor b',actor_type='organization',overall_confidence=.7)
    c2=Actor(id='c',case_id='c1',canonical_name='Actor C',normalized_name='actor c',actor_type='organization',overall_confidence=.6)
    s.add_all([a,b,c2]); s.flush()
    s.add_all([
      ActorPowerDimension(actor_id='a',dimension='formal_authority',level='high',confidence=.8,evidence_ids=[]),
      ActorPowerDimension(actor_id='b',dimension='formal_authority',level='medium',confidence=.7,evidence_ids=[]),
      ActorInterest(actor_id='a',interest='goal',importance='high',confidence=.8,evidence_ids=[]),
      ActorInterest(actor_id='b',interest='goal',importance='medium',confidence=.7,evidence_ids=[]),
      ActorPosition(actor_id='a',policy_key='case_primary',inferred_position='support',confidence=.8,evidence_ids=[]),
      ActorPosition(actor_id='b',policy_key='case_primary',inferred_position='opposition',confidence=.7,evidence_ids=[]),
      ActorObjective(actor_id='a',objective='Expand',objective_key='o1',stance=2,confidence=.8,evidence_ids=[]),
      ActorObjective(actor_id='b',objective='Expand',objective_key='o1',stance=-2,confidence=.8,evidence_ids=[]),
      ActorObjective(actor_id='c',objective='Expand',objective_key='o1',stance=1,confidence=.7,evidence_ids=[]),
      ActorRelationship(case_id='c1',source_actor_id='a',target_actor_id='b',relationship_type='influence',strength='high',confidence=.8,evidence_ids=[]),
      ActorRelationship(case_id='c1',source_actor_id='b',target_actor_id='c',relationship_type='dependency',strength='medium',confidence=.7,evidence_ids=[]),
    ]); s.commit(); return s


def test_mactor_is_computational_and_ready():
    s=seeded_session(); out=mactor(s,'c1')
    assert out['ready'] is True
    assert out['direct_influence']['a']['b']==3
    assert any(x['score']>0 for x in out['divergence'])


def test_network_metrics_find_broker():
    s=seeded_session(); out=network_metrics(s,'c1')
    b=next(x for x in out['nodes'] if x['id']=='b')
    assert b['degree']==2
    assert b['betweenness']>0


def test_method_selection_uses_question_and_data():
    s=seeded_session(); rec=recommend_methods(s,'c1','who_cooperates')
    assert rec['primary_method'] in {'mactor','coalition_analysis'}


def test_analysis_contains_required_views():
    s=seeded_session(); out,conf=run_analysis(s,'c1','who_matters',cluster_by='position')
    assert out['power_interest']
    assert out['network']['nodes']
    assert out['clusters']
    assert out['actor_objective']['objectives']==['o1']
    assert conf>0
