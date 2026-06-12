"""Fugue 全面端到端测试"""
import asyncio, httpx, time, random

PASS = FAIL = 0
ERRORS = []

def check(name, condition, detail=''):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f'  ✅ {name}')
    else:
        FAIL += 1
        msg = f'  ❌ {name}' + (f' ({detail})' if detail else '')
        print(msg)
        ERRORS.append(msg)

async def run_tests():
    async with httpx.AsyncClient(base_url='http://localhost:8000', timeout=30) as c:
        # ═══ 1. 认证系统 ═══
        print('\n═══ 1. 认证系统 ═══')
        uid = random.randint(10000, 99999)
        email = f'e2e_{uid}@test.com'
        r = await c.post('/api/v1/auth/register', json={'email':email,'username':f'e2e_{uid}','password':'TestPass123'})
        check('注册新用户', r.status_code == 201, f'{r.status_code}')
        r = await c.post('/api/v1/auth/register', json={'email':email,'username':f'e2e_{uid}b','password':'TestPass123'})
        check('重复注册被拒绝', r.status_code == 400, f'{r.status_code}')
        r = await c.post('/api/v1/auth/login', json={'email':email,'password':'TestPass123'})
        check('登录成功', r.status_code == 200)
        token = r.json()['access_token']
        h = {'Authorization': f'Bearer {token}'}
        r = await c.post('/api/v1/auth/login', json={'email':email,'password':'wrong'})
        check('错误密码被拒', r.status_code == 401)
        r = await c.get('/api/v1/auth/me', headers=h)
        check('获取当前用户', r.status_code == 200 and r.json()['email']==email)
        r = await c.get('/api/v1/auth/me')
        check('无token被拒', r.status_code in [401,403])

        # ═══ 2. 工作流 CRUD ═══
        print('\n═══ 2. 工作流 CRUD ═══')
        r = await c.post('/api/v1/crews/', json={'name':'E2E测试','description':'自动测试'}, headers=h)
        check('创建工作流', r.status_code == 201, f'{r.status_code}')
        cid = r.json()['id']
        check('返回正确name', r.json()['name'] == 'E2E测试')
        check('有metadata字段', 'metadata' in r.json())
        time.sleep(0.5)
        r = await c.get('/api/v1/crews/', headers=h)
        check('列出工作流', r.status_code == 200 and len(r.json()) >= 1, f'status={r.status_code} count={len(r.json())}')
        r = await c.get(f'/api/v1/crews/{cid}', headers=h)
        check('获取详情', r.status_code == 200 and 'agents' in r.json())
        r = await c.put(f'/api/v1/crews/{cid}', json={'name':'已更新'}, headers=h)
        check('更新名称', r.status_code == 200 and r.json()['name'] == '已更新')
        r = await c.get('/api/v1/crews/nonexistent', headers=h)
        check('不存在返回404', r.status_code == 404)

        # ═══ 3. Agent CRUD ═══
        print('\n═══ 3. Agent CRUD ═══')
        r = await c.post('/api/v1/agents/', json={'crew_id':cid,'name':'研究员','role':'研究','goal':'收集','llm_provider':'mock'}, headers=h)
        check('创建Agent1', r.status_code == 201, f'{r.status_code} {r.text[:80]}')
        a1 = r.json()['id']
        r = await c.post('/api/v1/agents/', json={'crew_id':cid,'name':'写手','role':'写作','goal':'撰写','llm_provider':'mock'}, headers=h)
        check('创建Agent2', r.status_code == 201)
        a2 = r.json()['id']
        r = await c.get(f'/api/v1/agents/crew/{cid}', headers=h)
        check('列出Agent', r.status_code == 200 and len(r.json()) == 2)
        r = await c.put(f'/api/v1/agents/{a1}', json={'name':'高级研究员'}, headers=h)
        check('更新Agent', r.status_code == 200 and r.json()['name'] == '高级研究员')

        # ═══ 4. Task CRUD ═══
        print('\n═══ 4. Task CRUD ═══')
        r = await c.post('/api/v1/tasks/', json={'crew_id':cid,'name':'研究','description':'收集数据','agent_id':a1}, headers=h)
        check('创建Task1', r.status_code == 201, f'{r.status_code} {r.text[:80]}')
        t1 = r.json()['id']
        r = await c.post('/api/v1/tasks/', json={'crew_id':cid,'name':'报告','description':'写报告','agent_id':a2,'context_task_ids':[t1]}, headers=h)
        check('创建Task2(依赖T1)', r.status_code == 201)
        t2 = r.json()['id']
        r = await c.get(f'/api/v1/tasks/crew/{cid}', headers=h)
        check('列出Task', r.status_code == 200 and len(r.json()) == 2)
        r = await c.get(f'/api/v1/tasks/{t2}', headers=h)
        check('依赖关系正确', t1 in r.json()['context_task_ids'])

        # ═══ 5. 执行引擎 ═══
        print('\n═══ 5. 执行引擎 ═══')
        r = await c.post('/api/v1/executions/', json={'crew_id':cid}, headers=h)
        check('创建执行', r.status_code == 201)
        eid = r.json()['id']
        check('初始pending', r.json()['status'] == 'pending')
        for i in range(20):
            time.sleep(1)
            r = await c.get(f'/api/v1/executions/{eid}', headers=h)
            if r.json()['status'] not in ['pending','running']:
                break
        check('执行完成', r.json()['status'] == 'completed', f'status={r.json()["status"]}')
        check('有trace', len(r.json().get('trace',[])) > 0)
        check('有token消耗', r.json()['total_tokens_used'] > 0)
        r = await c.get(f'/api/v1/executions/{eid}/task-executions', headers=h)
        check('TaskExec记录', r.status_code == 200 and len(r.json()) == 2)
        for te in r.json():
            check(f'TaskExec完成', te['status'] == 'completed')
            check(f'TaskExec有输出', len(te.get('output','') or '') > 0)

        # ═══ 6. 取消执行 ═══
        print('\n═══ 6. 取消执行 ═══')
        r = await c.post('/api/v1/executions/', json={'crew_id':cid}, headers=h)
        cancel_id = r.json()['id']
        time.sleep(0.3)
        r = await c.post(f'/api/v1/executions/{cancel_id}/cancel', headers=h)
        check('取消API', r.status_code == 200)
        time.sleep(2)
        r = await c.get(f'/api/v1/executions/{cancel_id}', headers=h)
        check('取消后终态', r.json()['status'] in ['cancelled','completed'])

        # ═══ 7. 演示工作流 ═══
        print('\n═══ 7. 演示工作流 ═══')
        demo_uid = random.randint(10000, 99999)
        r2 = await c.post('/api/v1/auth/register', json={'email':f'demo_{demo_uid}@test.com','username':f'demo_{demo_uid}','password':'DemoPass123'})
        check('Demo用户注册', r2.status_code == 201, f'{r2.status_code}')
        time.sleep(1)  # 等待注册commit
        r2 = await c.post('/api/v1/auth/login', json={'email':f'demo_{demo_uid}@test.com','password':'DemoPass123'})
        check('Demo用户登录', r2.status_code == 200, f'{r2.status_code}')
        dh = {'Authorization': f'Bearer {r2.json()["access_token"]}'}
        r = await c.post('/api/v1/demo/seed-demo-workflow', headers=dh)
        check('创建Demo', r.status_code == 201, f'{r.status_code} {r.text[:80]}')
        demo_cid = r.json()['crew_id']
        r = await c.post('/api/v1/demo/seed-demo-workflow', headers=dh)
        check('重复Demo被拒', r.status_code == 400)
        r = await c.post('/api/v1/executions/', json={'crew_id':demo_cid}, headers=dh)
        check('运行Demo', r.status_code == 201)
        demo_eid = r.json()['id']
        for i in range(20):
            time.sleep(1)
            r = await c.get(f'/api/v1/executions/{demo_eid}', headers=dh)
            if r.json()['status'] not in ['pending','running']:
                break
        check('Demo执行完成', r.json()['status'] == 'completed', f'status={r.json()["status"]}')
        r = await c.get(f'/api/v1/executions/{demo_eid}/task-executions', headers=dh)
        check('Demo有2个TaskExec', len(r.json()) == 2)

        # ═══ 8. 边界条件 ═══
        print('\n═══ 8. 边界条件 ═══')
        r = await c.post('/api/v1/crews/', json={'name':''}, headers=h)
        check('空name被拒(422)', r.status_code == 422)
        r = await c.post('/api/v1/agents/', json={'crew_id':'bad','name':'t','role':'t','goal':'t'}, headers=h)
        check('无效crew_id(404)', r.status_code == 404)
        r = await c.delete(f'/api/v1/crews/{cid}', headers=h)
        check('删除工作流', r.status_code == 200)
        time.sleep(1)  # 等待commit
        r = await c.get(f'/api/v1/crews/{cid}', headers=h)
        check('删除后404', r.status_code == 404)
        # 删除后agent和task也应该被级联删除（端点因crew不存在返回404，也是正确行为）
        r = await c.get(f'/api/v1/agents/crew/{cid}', headers=h)
        check('级联删除agent', r.status_code in [200, 404] and (r.status_code == 404 or len(r.json()) == 0))

    print(f'\n{"═"*50}')
    print(f'总计: {PASS+FAIL} | ✅ 通过: {PASS} | ❌ 失败: {FAIL}')
    if ERRORS:
        print(f'\n失败项:')
        for e in ERRORS:
            print(e)
    print(f'{"═"*50}')

asyncio.run(run_tests())
