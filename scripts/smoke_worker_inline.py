"""Local checkpoint/worker smoke test using the inline backend and real Job persistence."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401
from app.models.case import Case
from app.models.job import Job
from app.models.strategy import PolicyOption
from app.models.user import User
from app.services.job_handlers import register_handlers
from app.services.jobs import enqueue_job, execute_job

engine=create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
S=sessionmaker(bind=engine)
with S() as s:
    u=User(external_auth_id='worker-test',platform_role='user'); s.add(u); s.flush()
    c=Case(owner_id=u.id,title='worker test',description='worker test',analytical_question='test'); s.add(c); s.flush()
    p=PolicyOption(case_id=c.id,created_by=u.id,policy_key='p1',title='P1',description='desc',goal='goal',instruments=[]); s.add(p); s.commit()
    j=Job(case_id=c.id,requested_by=u.id,task_type='policy_strategy',processing_level='standard',status='queued',output={'policy_id':p.id,'checkpoint':'queued'})
    enqueue_job(s,j); register_handlers(); execute_job(s,j.id)
    assert j.status=='completed'; assert j.output['checkpoint']=='completed'
    print({'job_id':j.id,'status':j.status,'checkpoint':j.output['checkpoint']})
