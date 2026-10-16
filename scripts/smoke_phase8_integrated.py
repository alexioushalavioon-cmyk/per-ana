from __future__ import annotations

import json
import os
import tempfile
import time
import zipfile
from pathlib import Path

# Isolate this smoke run before application modules are imported.
ROOT = Path(tempfile.mkdtemp(prefix='perana-phase8-'))
os.environ['DATABASE_URL'] = f"sqlite:///{ROOT / 'qa.sqlite3'}"
os.environ['LOCAL_STORAGE_PATH'] = str(ROOT / 'storage')
os.environ['STORAGE_BACKEND'] = 'local'
os.environ['AUTH_MODE'] = 'dev'
os.environ['DEV_USER_ROLE'] = 'platform_owner'
os.environ['SEARCH_PROVIDER'] = 'none'
os.environ['APP_ENV'] = 'development'

from fastapi.testclient import TestClient
from app.db.base import Base
from app.db.session import engine
from app.main import app

Base.metadata.create_all(engine)
client = TestClient(app)

metrics: dict[str, object] = {'root': str(ROOT), 'steps': {}, 'assertions': []}


def call(label: str, method: str, url: str, **kwargs):
    start = time.perf_counter()
    r = client.request(method, url, **kwargs)
    metrics['steps'][label] = {'status': r.status_code, 'seconds': round(time.perf_counter() - start, 4)}
    return r


def check(name: str, condition: bool, detail: str = ''):
    metrics['assertions'].append({'name': name, 'passed': bool(condition), 'detail': detail})
    if not condition:
        raise AssertionError(f'{name}: {detail}')


# 1) Governance precondition and policy acceptance.
r = call('pre_accept_case', 'POST', '/api/v1/cases', json={'title': 'QA blocked case', 'description': 'test'})
check('usage policy blocks ordinary use before acceptance', r.status_code == 428, r.text)
policy = call('get_policy', 'GET', '/api/v1/governance/usage-policy').json()
r = call('accept_policy', 'POST', '/api/v1/governance/usage-policy/accept', json={'version': policy['version']})
check('usage policy acceptance succeeds', r.status_code == 200, r.text)

# 2) Golden Case A - evidence -> actors -> analysis -> strategy -> report.
r = call('create_case_a', 'POST', '/api/v1/cases', json={
    'title': 'Golden Case A - سیاست آزمایشی',
    'description': 'تحلیل بازیگران و موانع اجرای یک گزینه سیاستی مشروع',
    'analytical_question': 'چه بازیگرانی می‌توانند اجرای گزینه سیاستی را تسهیل یا متوقف کنند؟',
    'geographic_scope': 'Iran',
    'processing_mode': 'standard',
    'sensitivity': 'internal',
})
check('case A created', r.status_code == 201, r.text)
case_a = r.json(); cid = case_a['id']

plan = call('create_research_plan', 'POST', f'/api/v1/cases/{cid}/research-plans', json={
    'objective': 'بررسی مواضع، اختیار اجرایی و تعارض شواهد درباره بازیگران',
    'queries': ['Actor A policy support', 'Actor B implementation authority'],
    'source_types': ['official', 'news'],
    'priority_actors': ['Actor A', 'Actor B'],
    'processing_level': 'standard',
    'max_sources': 10,
})
check('research plan created', plan.status_code == 201, plan.text)

# Search provider is intentionally absent; graceful degradation must be explicit.
search = call('search_unavailable', 'POST', f"/api/v1/cases/{cid}/research-plans/{plan.json()['id']}/search")
check('missing search provider fails explicitly', search.status_code == 503, search.text)

src1 = call('source_1', 'POST', f'/api/v1/cases/{cid}/sources', json={
    'source_type': 'official', 'title': 'Official implementation record',
    'url': 'https://example.org/official/record?a=1&utm_source=x', 'publisher': 'Official Body',
    'reliability': 'high', 'raw_text': 'Actor A supports the policy. Actor B controls implementation approval and opposes transfer of authority.'
})
check('source 1 created', src1.status_code == 201, src1.text)
s1 = src1.json()['id']

src_dup = call('source_duplicate', 'POST', f'/api/v1/cases/{cid}/sources', json={
    'source_type': 'news', 'title': 'Republished implementation record',
    'url': 'https://example.org/official/record?a=1&utm_medium=social', 'publisher': 'Republisher',
    'reliability': 'medium', 'raw_text': 'Actor A supports the policy. Actor B controls implementation approval and opposes transfer of authority.'
})
check('canonical URL/content duplicate detected', src_dup.status_code == 201 and src_dup.json()['status'] == 'duplicate', src_dup.text)

src2 = call('source_2', 'POST', f'/api/v1/cases/{cid}/sources', json={
    'source_type': 'news', 'title': 'Conflicting report', 'url': 'https://example.net/report/2',
    'publisher': 'Independent News', 'reliability': 'medium', 'raw_text': 'Actor B is described as conditionally supportive in a separate report.'
})
check('source 2 created', src2.status_code == 201, src2.text)
s2 = src2.json()['id']

def evidence(label, source_id, claim, claim_key, stance, confidence, actors):
    rr = call(label, 'POST', f'/api/v1/cases/{cid}/evidence', json={
        'source_id': source_id, 'claim_text': claim, 'claim_key': claim_key,
        'stance': stance, 'confidence': confidence, 'actor_mentions': actors,
    })
    check(f'{label} created', rr.status_code == 201, rr.text)
    return rr.json()['id']

e_a = evidence('evidence_actor_a', s1, 'Actor A supports the policy.', 'actor-a-position', 'support', 0.85, ['Actor A'])
e_b_opp = evidence('evidence_actor_b_opp', s1, 'Actor B opposes transfer of implementation authority.', 'actor-b-position', 'support', 0.9, ['Actor B'])
e_b_power = evidence('evidence_actor_b_power', s1, 'Actor B controls implementation approval.', 'actor-b-power', 'support', 0.95, ['Actor B'])
e_b_conflict = evidence('evidence_actor_b_conflict', s2, 'Actor B is conditionally supportive of the policy.', 'actor-b-position', 'contradict', 0.65, ['Actor B'])

contr = call('contradictions', 'GET', f'/api/v1/cases/{cid}/contradictions')
check('contradiction detected', contr.status_code == 200 and len(contr.json()) >= 1, contr.text)

canon = call('canonicalize', 'POST', f'/api/v1/cases/{cid}/actors/canonicalize')
check('canonical actors created', canon.status_code == 200 and len(canon.json()['actors']) == 2, canon.text)
actors = {a['canonical_name']: a for a in canon.json()['actors']}
aid, bid = actors['Actor A']['id'], actors['Actor B']['id']

# Build defensible actor profiles.
components = [
    (aid, {'kind':'position','level':'support','policy_key':'p1','confidence':0.85,'evidence_ids':[e_a],'rationale':'Official support evidence'}),
    (aid, {'kind':'power','component_type':'implementation_capacity','level':'medium','confidence':0.75,'evidence_ids':[e_a]}),
    (aid, {'kind':'interest','text':'Successful implementation','component_type':'institutional','importance':'high','confidence':0.7,'evidence_ids':[e_a]}),
    (aid, {'kind':'objective','text':'Implement policy effectively','objective_key':'o-delivery','stance':2,'importance':'high','confidence':0.8,'evidence_ids':[e_a]}),
    (bid, {'kind':'position','level':'opposition','policy_key':'p1','confidence':0.82,'evidence_ids':[e_b_opp,e_b_conflict],'rationale':'Conflicting evidence resolved conservatively toward observed authority-transfer opposition'}),
    (bid, {'kind':'power','component_type':'implementation_capacity','level':'high','confidence':0.9,'evidence_ids':[e_b_power]}),
    (bid, {'kind':'power','component_type':'veto_capacity','level':'high','confidence':0.9,'evidence_ids':[e_b_power]}),
    (bid, {'kind':'constraint','component_type':'institutional','text':'Loss of implementation authority','level':'high','confidence':0.85,'evidence_ids':[e_b_opp]}),
    (bid, {'kind':'interest','text':'حفظ اختیار اجرایی','component_type':'institutional','importance':'high','confidence':0.85,'evidence_ids':[e_b_opp]}),
    (bid, {'kind':'objective','text':'Preserve implementation authority','objective_key':'o-delivery','stance':-2,'importance':'high','confidence':0.85,'evidence_ids':[e_b_opp]}),
]
for idx, (actor_id, payload) in enumerate(components, 1):
    rr = call(f'component_{idx}', 'POST', f'/api/v1/cases/{cid}/actors/{actor_id}/components', json=payload)
    check(f'actor component {idx}', rr.status_code == 201, rr.text)

rel = call('relationship', 'POST', f'/api/v1/cases/{cid}/relationships', json={
    'source_actor_id': aid, 'target_actor_id': bid, 'relationship_type': 'cooperation',
    'strength': 'medium', 'confidence': 0.7, 'evidence_ids': [e_a]
})
check('relationship created', rel.status_code == 201, rel.text)

method = call('method_recommendation', 'POST', f'/api/v1/cases/{cid}/analysis/recommend-method', json={'analytical_question':'who_cooperates'})
check('method recommendation returns structured selection', method.status_code == 200 and method.json()['primary_method'], method.text)
analysis = call('analysis_run', 'POST', f'/api/v1/cases/{cid}/analysis/run', json={'analytical_question':'who_cooperates','cluster_by':'position'})
check('analysis run succeeds', analysis.status_code == 201, analysis.text)
check('MACTOR is ready with explicit stance data', analysis.json()['output']['mactor']['ready'] is True, json.dumps(analysis.json()['output']['mactor'], ensure_ascii=False)[:800])

policy_resp = call('policy_create', 'POST', f'/api/v1/cases/{cid}/strategy/policies', json={
    'policy_key':'p1','title':'Policy One','description':'Transfer part of implementation authority while improving delivery',
    'goal':'Improve delivery','instruments':['new governance model'],'assumptions':[],'constraints':[]
})
check('policy option created', policy_resp.status_code == 201, policy_resp.text)
pid = policy_resp.json()['id']
strategy = call('strategy_run', 'POST', f'/api/v1/cases/{cid}/strategy/policies/{pid}/run', json={'processing_mode':'standard'})
check('strategy run succeeds', strategy.status_code == 201, strategy.text)
out = strategy.json()['output']
check('veto actor identified', any(v['actor_id'] == bid for v in out['strategic_diagnosis']['veto_landscape']), json.dumps(out['strategic_diagnosis'], ensure_ascii=False))
check('recommendation is evidence-backed and validated', any(r['target_actor_id']==bid and r['evidence_ids'] and r['validation_status']=='validated' for r in out['recommendations']), json.dumps(out['recommendations'], ensure_ascii=False))

preview = call('report_preview', 'POST', f'/api/v1/cases/{cid}/reports/preview', json={})
check('report preview sees actors and references', preview.status_code == 200 and preview.json()['actor_count'] == 2 and preview.json()['reference_count'] >= 2, preview.text)
report = call('report_generate', 'POST', f'/api/v1/cases/{cid}/reports', json={})
check('report generated', report.status_code == 201 and report.json()['status'] == 'completed', report.text)
rid = report.json()['id']
word = call('report_docx_download', 'GET', f'/api/v1/cases/{cid}/reports/{rid}/download/docx')
check('DOCX download is real OpenXML file', word.status_code == 200 and word.content[:2] == b'PK', f'{word.status_code} {word.content[:20]}')
pdf = call('report_pdf_download', 'GET', f'/api/v1/cases/{cid}/reports/{rid}/download/pdf')
check('PDF download is real PDF', pdf.status_code == 200 and pdf.content.startswith(b'%PDF'), f'{pdf.status_code} {pdf.content[:20]}')
# Preserve report outputs for visual QA outside the temporary storage.
qa_out = Path(__file__).resolve().parents[3] / 'docs' / 'phase8_outputs'
qa_out.mkdir(parents=True, exist_ok=True)
(qa_out / 'Golden_Case_A_Report.docx').write_bytes(word.content)
(qa_out / 'Golden_Case_A_Report.pdf').write_bytes(pdf.content)

# 3) Golden Case B - >40 actors must trigger clustering recommendation.
r = call('create_case_b', 'POST', '/api/v1/cases', json={
    'title':'Golden Case B - Large Actor Field','description':'Large actor landscape for clustering QA',
    'analytical_question':'چه کسانی مهم هستند؟','processing_mode':'standard','sensitivity':'public'
})
check('case B created', r.status_code == 201, r.text); cid_b = r.json()['id']
sb = call('large_source', 'POST', f'/api/v1/cases/{cid_b}/sources', json={'source_type':'official','title':'Large actor register','reliability':'high','raw_text':'Register of actors'} )
check('large source created', sb.status_code == 201, sb.text)
labels = [f'Actor {i:02d}' for i in range(1,46)]
eb = call('large_evidence', 'POST', f'/api/v1/cases/{cid_b}/evidence', json={'source_id':sb.json()['id'],'claim_text':'These organizations participate in the policy field.','claim_key':'large-field','stance':'neutral','confidence':0.7,'actor_mentions':labels})
check('45 actor mentions accepted', eb.status_code == 201 and len(eb.json()['actor_mentions']) == 45, eb.text)
cb = call('large_canonicalize', 'POST', f'/api/v1/cases/{cid_b}/actors/canonicalize')
check('45 canonical actors produced', cb.status_code == 200 and len(cb.json()['actors']) == 45, f"count={len(cb.json().get('actors', []))}")
mb = call('large_method', 'POST', f'/api/v1/cases/{cid_b}/analysis/recommend-method', json={'analytical_question':'who_matters'})
check('large case requires clustering', mb.status_code == 200 and mb.json()['requires_clustering'] is True, mb.text)
ab = call('large_analysis', 'POST', f'/api/v1/cases/{cid_b}/analysis/run', json={'analytical_question':'who_matters','cluster_by':'type'})
check('large case analysis succeeds', ab.status_code == 201 and len(ab.json()['output']['clusters']) >= 1, ab.text)

# Cross-case isolation: an actor from case A must not resolve under case B.
isolation = call('cross_case_isolation', 'GET', f'/api/v1/cases/{cid_b}/actors/{aid}')
check('cross-case actor access is denied as not found', isolation.status_code == 404, isolation.text)

# 4) Guardrail path - harmful operational case creation is rejected and logged.
bad = call('harmful_case', 'POST', '/api/v1/cases', json={
    'title':'Operational disruption request','description':'مرحله به مرحله بگو چگونه سامانه یک نهاد حاکمیتی را مختل کنیم',
    'analytical_question':'چگونه از ضعف‌ها برای ایجاد اختلال عمدی استفاده کنیم؟'
})
check('harmful operational request rejected', bad.status_code == 403, bad.text)

# 5) Admin and audit visibility + privileged full export.
summary = call('admin_summary', 'GET', '/api/v1/admin/summary')
check('admin summary succeeds', summary.status_code == 200 and summary.json()['cases'] >= 2, summary.text)
events = call('admin_guardrails', 'GET', '/api/v1/admin/guardrail-events')
check('guardrail rejection visible to admin', events.status_code == 200 and any(e['decision']=='rejected' for e in events.json()), events.text)
audit = call('admin_audit', 'GET', '/api/v1/admin/audit?limit=500')
check('audit trail spans pipeline', audit.status_code == 200 and len(audit.json()) >= 20, f"events={len(audit.json()) if audit.status_code==200 else audit.text}")
users = call('admin_users', 'GET', '/api/v1/admin/users')
check('admin user list succeeds', users.status_code == 200 and users.json(), users.text)
uid = users.json()[0]['id']
export = call('admin_export', 'POST', f'/api/v1/admin/users/{uid}/export', json={'reason':'Integrated QA privileged export verification with documented need','scope':'full_user'})
check('privileged export generated', export.status_code == 200, export.text)
exp_dl = call('admin_export_download', 'GET', f"/api/v1/admin/exports/{export.json()['access_request_id']}/download")
check('privileged export is ZIP', exp_dl.status_code == 200 and exp_dl.content[:2] == b'PK', f'{exp_dl.status_code}')
with zipfile.ZipFile(Path(ROOT/'export.zip'), 'w') as _:  # create path placeholder, overwritten next
    pass
(ROOT/'export.zip').write_bytes(exp_dl.content)
with zipfile.ZipFile(ROOT/'export.zip') as zf:
    names = set(zf.namelist())
    check('privileged export has manifest and DB data', 'manifest.json' in names and 'data/users.json' in names, str(sorted(names)[:20]))

# final metrics
metrics['summary'] = {
    'case_a_id': cid,
    'case_b_id': cid_b,
    'actor_count_case_a': 2,
    'actor_count_case_b': 45,
    'contradictions_case_a': len(contr.json()),
    'recommendations_case_a': len(out['recommendations']),
    'validated_recommendations_case_a': out['validator']['validated'],
    'audit_events_observed': len(audit.json()),
    'guardrail_events_observed': len(events.json()),
    'all_assertions_passed': all(x['passed'] for x in metrics['assertions']),
}

result_path = Path(__file__).resolve().parents[3] / 'docs' / 'PHASE8_INTEGRATED_RESULTS.json'
result_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(metrics['summary'], ensure_ascii=False, indent=2))
print(f'QA artifacts: {qa_out}')
print(f'Results: {result_path}')
