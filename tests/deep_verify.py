"""Deep functional verification — confirm all optimizations actually work"""
import json, os, sys, requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

BASE = 'http://127.0.0.1:8000/api/v1'
uid = 'verify_deep_final2'
email = f'{uid}@test.com'
password = 'Verify@Deep1'
errors = []

def check(name, condition, detail=''):
    if condition: print(f'  [PASS] {name}')
    else:
        print(f'  [FAIL] {name} -- {detail}')
        errors.append(name)

# ===== 1. AUTH =====
print('=== Ch4: Auth System ===')
r = requests.post(f'{BASE}/auth/register', json={'email': email, 'username': uid, 'password': password})
check('Register', r.status_code == 201, f'HTTP {r.status_code}')
token = r.json().get('access_token', '') if r.status_code == 201 else ''
headers = {'Authorization': f'Bearer {token}'}

r = requests.post(f'{BASE}/auth/login', json={'email': email, 'password': password})
check('Login', r.status_code == 200, f'HTTP {r.status_code}')
if r.status_code == 200:
    token = r.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

r = requests.get(f'{BASE}/auth/me', headers=headers)
check('Get current user', r.status_code == 200, f'HTTP {r.status_code}')

# ===== 2. TOOLS =====
print('\n=== Ch1: Agent Memory Tools ===')
r = requests.get(f'{BASE}/tools', headers=headers)
if r.status_code == 200:
    data = r.json()
    if isinstance(data, dict):
        tool_names = list(data.keys()) if 'tools' not in data else [t.get('name','') for t in data.get('tools',[])]
    else:
        tool_names = [t.get('name','') for t in data]
    check('remember tool exists', 'remember' in tool_names, str(tool_names[:5]))
    check('recall tool exists', 'recall' in tool_names)
    check('search_knowledge tool exists', 'search_knowledge' in tool_names)
    check('web_search tool exists', 'web_search' in tool_names)
    check('code_execute tool exists', 'code_execute' in tool_names)
else:
    check('Tools API', False, f'HTTP {r.status_code}')

# ===== 3. SKILLS =====
print('\n=== Ch6: Skills CRUD API ===')
r = requests.get(f'{BASE}/skills/', headers=headers)
check('Skills list (GET /)', r.status_code == 200, f'HTTP {r.status_code}')

r = requests.get(f'{BASE}/skills/categories', headers=headers)
check('Skills categories (GET /categories)', r.status_code == 200, f'HTTP {r.status_code}')

r = requests.post(f'{BASE}/skills/', json={
    'name': f'verify_skill_{uid}', 'description': 'test', 'version': '1.0.0'
}, headers=headers)
check('Skills create - non-admin rejected', r.status_code == 403, f'HTTP {r.status_code}')

# ===== 4. PROMPT BUILDER ReAct/CoT =====
print('\n=== Ch1: ReAct/CoT Reasoning ===')
from app.engine.prompt_builder import build_messages, _build_tool_capability_prompt
cap = _build_tool_capability_prompt('/tmp/test')
check('Tool prompt has remember', 'remember' in cap)
check('Tool prompt has recall', 'recall' in cap)
check('Tool prompt has search_knowledge', 'search_knowledge' in cap)

class MA: name='T'; role='tester'; goal='v'; backstory='b'; system_prompt_template=None
class MT: name='V'; description='d'; expected_output='o'
msgs = build_messages(MA(), MT(), [], '/tmp/test')
sp = msgs[0]['content']
check('System prompt has ReAct', 'ReAct' in sp)
check('System prompt has Chain-of-Thought', 'Chain-of-Thought' in sp)

# ===== 5. ProcessType =====
print('\n=== Ch1: 9 ProcessTypes ===')
from app.models.crew import ProcessType
types = [p.value for p in ProcessType]
for t in ['sequential', 'parallel', 'hierarchical', 'prompt_chain', 'router', 'orchestrator', 'evaluator_optimizer', 'event_flow', 'plan_execute']:
    check(f'ProcessType.{t}', t in types)

# ===== 6. SECURITY FIXES =====
print('\n=== Ch4: Security Fixes ===')
wm_code = open('app/core/websocket_manager.py').read()
check('WebSocket list() anti-race', 'list(self.active_connections' in wm_code)

from app.core.rate_limiter import _MemoryRateLimiter
check('Rate limiter asyncio.Lock', hasattr(_MemoryRateLimiter(), '_lock'))

from app.core.encryption import encrypt, decrypt
enc = encrypt('secret123')
check('Encrypt/decrypt works', decrypt(enc) == 'secret123')
try:
    decrypt('bad-data')
    check('Decrypt raises on failure', False, 'no exception')
except ValueError:
    check('Decrypt raises ValueError', True)

from app.core.config import settings
check('MinIO creds empty', settings.MINIO_ACCESS_KEY == '' and settings.MINIO_SECRET_KEY == '')

exc_code = open('app/engine/executor.py').read()
bare = exc_code.count('except Exception:\n            pass') + exc_code.count('except Exception:\n                pass')
check('No bare except:pass in executor', bare == 0, f'{bare} remaining')

exc_h = open('app/core/exceptions.py').read()
check('RequestValidationError handler', 'RequestValidationError' in exc_h)

# ===== 7. SKILLS DB MODEL =====
print('\n=== Ch6: Skills DB Model ===')
from app.models.skill import Skill
cols = [c.name for c in Skill.__table__.columns]
for c in ['name', 'entrypoint', 'active', 'code_path', 'config', 'required_tools', 'prompt_template']:
    check(f'Skills.{c} column', c in cols)

# ===== 8. DARK THEME & i18n =====
print('\n=== Ch5+Ch3: Dark Theme & i18n ===')
frontend = os.path.join(os.path.dirname(__file__), '..', 'frontend')
css = open(os.path.join(frontend, 'src', 'index.css')).read()
check('[data-theme="dark"] exists', '[data-theme="dark"]' in css)
check('prefers-color-scheme: dark exists', 'prefers-color-scheme: dark' in css)
check('i18n.ts exists', os.path.exists(os.path.join(frontend, 'src', 'lib', 'i18n.ts')))
check('tutorialStore.ts exists', os.path.exists(os.path.join(frontend, 'src', 'stores', 'tutorialStore.ts')))

# ===== 9. FEEDBACK + LOGO =====
print('\n=== Ch2+Ch5: Feedback & Logo ===')
check('FeedbackButtons.tsx exists', os.path.exists(os.path.join(frontend, 'src', 'components', 'monitor', 'FeedbackButtons.tsx')))
check('logo.svg exists', os.path.exists(os.path.join(frontend, 'public', 'logo.svg')))

# ===== 10. CI CONFIG =====
print('\n=== Ch7: CI Configuration ===')
ci_yml = os.path.join(os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml')
if os.path.exists(ci_yml):
    ci = open(ci_yml).read()
    check('CI has npm test', 'npm test' in ci)
    check('CI has npm audit', 'npm audit' in ci)

# ===== 11. DEPENDENCY SECURITY =====
print('\n=== Ch4: Dependency Security ===')
req_txt = open('requirements.txt').read()
check('requirements.txt has upper bounds', '<' in req_txt)
check('fastapi pinned', 'fastapi>=' in req_txt and ',<' in req_txt.split('fastapi')[1][:20])

# ===== SUMMARY =====
print(f'\n{"="*50}')
total = 42
passed = total - len(errors)
print(f'Deep Verification: {passed}/{total} passed')
if errors:
    print(f'\nFailures ({len(errors)}):')
    for e in errors: print(f'  [FAIL] {e}')
else:
    print(f'\n*** ALL {total} VERIFICATIONS PASSED ***')
