from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.case import Case
from app.models.source import Source
from app.models.evidence import Evidence
from app.models.actor import Actor, ActorPosition, ActorPowerDimension, ActorInterest, ActorRelationship
from app.models.strategy import PolicyOption, StrategyRun
from app.services.strategy import analyze_policy
from app.services.reporting.engine import generate_report_files, _collect_snapshot


def seeded_report_session():
    eng=create_engine('sqlite+pysqlite:///:memory:'); Base.metadata.create_all(eng); S=sessionmaker(bind=eng); s=S()
    u=User(id='u1',external_auth_id='dev-u1',email='a@example.com')
    c=Case(id='c1',owner_id='u1',title='تحلیل توسعه هوش مصنوعی',description='پرونده آزمایشی',analytical_question='چه بازیگرانی مانع سیاست هستند؟',geographic_scope='ایران',status='active')
    s.add_all([u,c]); s.flush()
    src=Source(id='s1',case_id='c1',added_by='u1',source_type='official',title='سند رسمی آزمایشی',url='https://example.org/source',publisher='نهاد رسمی',reliability='high')
    e1=Evidence(id='e1',case_id='c1',source_id='s1',created_by='u1',claim_text='Actor B controls implementation approval',confidence=.9)
    e2=Evidence(id='e2',case_id='c1',source_id='s1',created_by='u1',claim_text='Actor B opposes transfer of authority',confidence=.85)
    s.add(src); s.flush(); s.add_all([e1,e2])
    a=Actor(id='a',case_id='c1',canonical_name='وزارت الف',normalized_name='وزارت الف',actor_type='government',overall_confidence=.9,strategic_importance='high')
    b=Actor(id='b',case_id='c1',canonical_name='سازمان ب',normalized_name='سازمان ب',actor_type='regulator',overall_confidence=.85,strategic_importance='critical')
    s.add_all([a,b]); s.flush()
    s.add_all([
        ActorPosition(actor_id='a',policy_key='p1',inferred_position='support',confidence=.8,evidence_ids=['e1']),
        ActorPowerDimension(actor_id='a',dimension='formal_authority',level='high',confidence=.8,evidence_ids=['e1']),
        ActorPosition(actor_id='b',policy_key='p1',inferred_position='opposition',confidence=.85,evidence_ids=['e2']),
        ActorPowerDimension(actor_id='b',dimension='veto_capacity',level='high',confidence=.9,evidence_ids=['e1']),
        ActorInterest(actor_id='b',interest='حفظ اختیار اجرایی',interest_type='institutional',importance='high',confidence=.85,evidence_ids=['e2']),
        ActorRelationship(case_id='c1',source_actor_id='a',target_actor_id='b',relationship_type='regulation',strength='high',confidence=.8,evidence_ids=['e1']),
    ])
    p=PolicyOption(id='p',case_id='c1',created_by='u1',policy_key='p1',title='گزینه سیاستی یک',description='آزمایش',goal='بهبود اجرا',instruments=['بازطراحی حکمرانی'],assumptions=[],constraints=[])
    s.add(p); s.flush(); out,conf=analyze_policy(s,'c1',p)
    sr=StrategyRun(id='sr1',case_id='c1',policy_option_id='p',created_by='u1',output_json=out,confidence=conf,validated=out['validator']['needs_review']==0)
    s.add(sr); s.commit(); return s


def test_report_snapshot_contains_traceable_sources():
    s=seeded_report_session(); snap=_collect_snapshot(s,'c1')
    assert len(snap['actors'])==2
    assert snap['references']
    assert snap['references'][0]['title']=='سند رسمی آزمایشی'
    assert snap['strategies']


def test_report_generates_editable_docx_and_pdf():
    s=seeded_report_session(); snap,docx,pdf,val=generate_report_files(s,'c1',[
        'executive_summary','actor_landscape','key_actors','network','policy_options','actor_reactions','strategy','recommendations','uncertainties','sources'
    ],['actor_landscape','position_power'])
    assert Path(docx).exists() and Path(docx).stat().st_size>10000
    assert pdf is not None and Path(pdf).exists() and Path(pdf).stat().st_size>1000
    assert val['docx_exists'] and val['pdf_exists']
    assert val['reference_count']>=1
