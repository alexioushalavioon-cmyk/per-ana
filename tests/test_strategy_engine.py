from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.case import Case
from app.models.source import Source
from app.models.evidence import Evidence
from app.models.actor import Actor, ActorPosition, ActorPowerDimension, ActorConstraint, ActorInterest, ActorRelationship
from app.models.strategy import PolicyOption
from app.services.strategy import analyze_policy


def seeded_session():
    eng=create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(eng)
    S=sessionmaker(bind=eng); s=S()
    u=User(id='u1',external_auth_id='dev-u1',email='a@example.com'); c=Case(id='c1',owner_id='u1',title='case',description='x',status='active')
    s.add_all([u,c]); s.flush()
    src=Source(id='s1',case_id='c1',added_by='u1',source_type='official',title='Official source',reliability='high')
    e1=Evidence(id='e1',case_id='c1',source_id='s1',created_by='u1',claim_text='Actor B controls implementation approval',confidence=.9)
    e2=Evidence(id='e2',case_id='c1',source_id='s1',created_by='u1',claim_text='Actor B opposes transfer of authority',confidence=.85)
    e3=Evidence(id='e3',case_id='c1',source_id='s1',created_by='u1',claim_text='Actor A supports the policy',confidence=.8)
    s.add(src); s.flush(); s.add_all([e1,e2,e3])
    a=Actor(id='a',case_id='c1',canonical_name='Actor A',normalized_name='actor a',actor_type='organization',overall_confidence=.8)
    b=Actor(id='b',case_id='c1',canonical_name='Actor B',normalized_name='actor b',actor_type='organization',overall_confidence=.85)
    s.add_all([a,b]); s.flush()
    s.add_all([
        ActorPosition(actor_id='a',policy_key='p1',inferred_position='support',confidence=.8,evidence_ids=['e3']),
        ActorPowerDimension(actor_id='a',dimension='implementation_capacity',level='medium',confidence=.8,evidence_ids=['e3']),
        ActorPosition(actor_id='b',policy_key='p1',inferred_position='opposition',confidence=.85,evidence_ids=['e2']),
        ActorPowerDimension(actor_id='b',dimension='implementation_capacity',level='high',confidence=.9,evidence_ids=['e1']),
        ActorPowerDimension(actor_id='b',dimension='veto_capacity',level='high',confidence=.9,evidence_ids=['e1']),
        ActorConstraint(actor_id='b',constraint_type='institutional',description='Loss of implementation authority',severity='high',confidence=.85,evidence_ids=['e2']),
        ActorInterest(actor_id='b',interest='حفظ اختیار اجرایی',interest_type='institutional',importance='high',confidence=.85,evidence_ids=['e2']),
        ActorRelationship(case_id='c1',source_actor_id='a',target_actor_id='b',relationship_type='cooperation',strength='medium',confidence=.7,evidence_ids=['e3']),
    ])
    p=PolicyOption(id='p',case_id='c1',created_by='u1',policy_key='p1',title='Policy One',description='transfer part of implementation authority',goal='improve delivery',instruments=['new governance model'],assumptions=[],constraints=[])
    s.add(p); s.commit(); return s,p


def test_strategy_identifies_opponent_veto_and_leverage():
    s,p=seeded_session(); out,conf=analyze_policy(s,'c1',p)
    assert 'b' in out['strategic_diagnosis']['main_barrier_actor_ids']
    assert any(v['actor_id']=='b' for v in out['strategic_diagnosis']['veto_landscape'])
    assert any(x['actor_id']=='b' and x['type']=='governance_design' for x in out['strategic_leverages'])
    assert conf>0


def test_recommendation_has_real_evidence_chain_and_is_specific():
    s,p=seeded_session(); out,_=analyze_policy(s,'c1',p)
    rec=next(x for x in out['recommendations'] if x['target_actor_id']=='b')
    assert rec['evidence_ids']
    assert set(rec['evidence_ids']).intersection({'e1','e2'})
    assert 'Actor B' in rec['action']
    assert rec['validation_status']=='validated'


def test_validator_reports_unknown_actor_uncertainty():
    s,p=seeded_session()
    c=Actor(id='c',case_id='c1',canonical_name='Actor C',normalized_name='actor c',actor_type='organization',overall_confidence=.4)
    s.add(c); s.commit()
    out,_=analyze_policy(s,'c1',p)
    assert any('Actor C' in x for x in out['critical_uncertainties'])


def test_support_and_opposition_are_separated():
    s,p=seeded_session(); out,_=analyze_policy(s,'c1',p)
    coal=out['strategic_diagnosis']['coalition']
    assert 'a' in coal['supporters']
    assert 'b' in coal['opponents']
