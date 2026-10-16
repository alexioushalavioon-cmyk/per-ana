from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.case import Case
from app.models.source import Source
from app.models.evidence import Evidence, EvidenceActorMention
from app.models.actor import Actor, ActorObjective, ActorPosition, ActorPowerDimension, ActorConstraint, ActorInterest, ActorRelationship
from app.models.strategy import PolicyOption
from app.services.actors import canonicalize_mentions
from app.services.analysis import recommend_methods, run_analysis
from app.services.strategy import analyze_policy


def _session():
    eng = create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(eng)
    return sessionmaker(bind=eng)()


def test_large_actor_field_requires_clustering_and_preserves_all_actors():
    s = _session()
    s.add_all([User(id='u', external_auth_id='u'), Case(id='c', owner_id='u', title='large', status='active')])
    src = Source(id='src', case_id='c', added_by='u', source_type='official', title='register', reliability='high')
    ev = Evidence(id='ev', case_id='c', source_id='src', created_by='u', claim_text='registered actors', confidence=.7)
    s.add(src); s.flush(); s.add(ev); s.flush()
    for i in range(45):
        s.add(EvidenceActorMention(evidence_id='ev', actor_label=f'Actor {i:02d}', confidence=.8))
    s.commit()
    created, _, _, _ = canonicalize_mentions(s, 'c')
    s.commit()
    assert created == 45
    rec = recommend_methods(s, 'c', 'who_matters')
    assert rec['requires_clustering'] is True
    out, _ = run_analysis(s, 'c', 'who_matters', cluster_by='type')
    assert sum(c['count'] for c in out['clusters']) == 45


def test_strategy_gate_requires_evidence_backed_actor_logic_after_analysis():
    s = _session()
    s.add_all([User(id='u', external_auth_id='u'), Case(id='c', owner_id='u', title='case', status='active')])
    src = Source(id='src', case_id='c', added_by='u', source_type='official', title='official', reliability='high')
    e1 = Evidence(id='e1', case_id='c', source_id='src', created_by='u', claim_text='B controls implementation approval', confidence=.9)
    e2 = Evidence(id='e2', case_id='c', source_id='src', created_by='u', claim_text='B opposes authority transfer', confidence=.85)
    s.add(src); s.flush(); s.add_all([e1,e2])
    a=Actor(id='a',case_id='c',canonical_name='A',normalized_name='a',actor_type='organization',overall_confidence=.8)
    b=Actor(id='b',case_id='c',canonical_name='B',normalized_name='b',actor_type='organization',overall_confidence=.85)
    s.add_all([a,b]); s.flush()
    s.add_all([
        ActorObjective(actor_id='a',objective='delivery',objective_key='o1',stance=2,importance='high',stated_or_inferred='inferred',confidence=.8,evidence_ids=['e1']),
        ActorObjective(actor_id='b',objective='authority',objective_key='o1',stance=-2,importance='high',stated_or_inferred='inferred',confidence=.8,evidence_ids=['e2']),
        ActorPosition(actor_id='b',policy_key='p1',inferred_position='opposition',confidence=.85,evidence_ids=['e2']),
        ActorPowerDimension(actor_id='b',dimension='implementation_capacity',level='high',confidence=.9,evidence_ids=['e1']),
        ActorPowerDimension(actor_id='b',dimension='veto_capacity',level='high',confidence=.9,evidence_ids=['e1']),
        ActorConstraint(actor_id='b',constraint_type='institutional',description='Loss of authority',severity='high',confidence=.8,evidence_ids=['e2']),
        ActorInterest(actor_id='b',interest='اختیار',interest_type='institutional',importance='high',confidence=.8,evidence_ids=['e2']),
        ActorRelationship(case_id='c',source_actor_id='a',target_actor_id='b',relationship_type='cooperation',strength='medium',confidence=.7,evidence_ids=['e1'])
    ])
    p=PolicyOption(id='p',case_id='c',created_by='u',policy_key='p1',title='Policy',description='change authority',goal='delivery',instruments=['governance'],assumptions=[],constraints=[])
    s.add(p); s.commit()
    analysis,_=run_analysis(s,'c','who_cooperates')
    assert analysis['mactor']['ready'] is True
    strategy,_=analyze_policy(s,'c',p)
    assert strategy['validator']['validated'] >= 1
    rec = strategy['recommendations'][0]
    assert rec['target_actor_id'] == 'b'
    assert rec['evidence_ids']
    assert rec['validation_status'] == 'validated'
