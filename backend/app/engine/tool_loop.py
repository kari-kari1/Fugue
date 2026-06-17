"""工具调用循环 — 从 executor.py 拆分

负责: LLM 流式调用、工具执行、审批检查、消息历史更新。
报告 P0-4 要求拆分 executor.py 为独立模块。
"""

import asyncio
import json
import logging
import re
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.llm_provider import LLMResponse, update_provider_health
from app.engine.message_builder import append_tool_messages
from app.models.agent import Agent
from app.models.execution import Execution, ExecutionStatus
from app.models.task import Task
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)


async def run_tool_call_loop(
    engine,
    db: AsyncSession,
    execution: Execution,
    task: Task,
    agent: Agent,
    llm,
    messages: list,
    tool_schemas: list,
    is_anthropic: bool,
    timeout: int,
    effective_model: str,
) -> tuple[str, list, int, float]:
    """运行多轮工具调用循环。

    Returns: (final_content, all_tool_calls, total_tokens, total_cost)
    """
    all_tool_calls = []
    max_tool_rounds = 10
    total_tokens = 0
    total_cost = 0.0
    final_content = ""
    # 去重检测：同一工具+参数连续3次则强制终止
    recent_calls: list = []

    for tool_round in range(max_tool_rounds):
        llm_response: LLMResponse = None
        stream_buffer = ""

        try:
            stream_gen = llm.chat_stream(
                messages=messages, model=effective_model,
                temperature=agent.temperature, max_tokens=agent.max_tokens,
                tools=tool_schemas if tool_schemas else None,
            )
            async for event in stream_gen:
                if event is None:
                    continue
                etype = getattr(event, 'event_type', None)
                if etype == "text_delta":
                    text_chunk = event.data or ""
                    if text_chunk:
                        stream_buffer += text_chunk
                        if len(stream_buffer) % 200 < len(text_chunk):
                            await event_publisher.publish_agent_thinking(
                                execution_id=engine.execution_id,
                                agent_name=agent.name,
                                thought=stream_buffer[-500:],
                                step=f"生成中 (轮次 {tool_round+1})",
                            )
                elif etype == "tool_call_start":
                    tc_info = event.data or {}
                    await event_publisher.publish_agent_thinking(
                        execution_id=engine.execution_id,
                        agent_name=agent.name,
                        thought=f"正在调用工具: {tc_info.get('name', '?')}",
                        step="tool_call",
                    )
                elif etype == "done":
                    llm_response = event.data

        except TimeoutError:
            logger.warning("[EXECUTOR] LLM streaming timeout (%ds)", timeout)
            raise
        except Exception as stream_err:
            logger.warning("[EXECUTOR] Streaming error: %s, falling back to non-streaming", stream_err)
            llm_response = await asyncio.wait_for(
                llm.chat(
                    messages=messages, model=effective_model,
                    temperature=agent.temperature, max_tokens=agent.max_tokens,
                    tools=tool_schemas if tool_schemas else None,
                ),
                timeout=timeout,
            )

        if llm_response is None:
            raise Exception("LLM 调用未返回响应")

        await update_provider_health(agent.llm_provider, success=True)
        total_tokens += llm_response.tokens_used
        total_cost += llm_response.cost_usd

        # 推送推理文本
        model_text = stream_buffer or (llm_response.content or "")
        model_text = re.sub(r'```tool_call\s*\n.*?\n```', '', model_text, flags=re.DOTALL).strip()
        if model_text:
            await event_publisher.publish_agent_thinking(
                execution_id=engine.execution_id,
                agent_name=agent.name,
                thought=model_text[:2000], step="reasoning",
            )

        if llm_response.tool_calls:
            for tc in llm_response.tool_calls:
                await event_publisher.publish_agent_thinking(
                    execution_id=engine.execution_id,
                    agent_name=agent.name,
                    thought=engine._describe_tool_call(tc.name, tc.arguments),
                    step="reasoning",
                )

        # 无工具调用 → 检查文本工具调用协议
        if not llm_response.tool_calls:
            text_tool_calls = engine._parse_text_tool_calls(llm_response.content or "")
            if text_tool_calls:
                logger.info("[EXECUTOR] Parsed %d text-based tool calls", len(text_tool_calls))
                llm_response.tool_calls = text_tool_calls
                clean_content = re.sub(r'```tool_call\s*\n.*?\n```', '', llm_response.content, flags=re.DOTALL).strip()
                if clean_content:
                    llm_response.content = clean_content
            else:
                final_content = llm_response.content
                break

        engine._add_trace(execution, "agent.thinking", agent_name=agent.name, data={
            "step": f"工具调用轮次 {tool_round + 1}: {', '.join(tc.name for tc in llm_response.tool_calls)}",
        })

        # 执行工具
        for tc in llm_response.tool_calls:
            await event_publisher.publish_agent_tool_call(
                execution_id=engine.execution_id,
                agent_name=agent.name,
                tool_name=tc.name, tool_input=tc.arguments,
            )

            tool_result = await check_approval_and_execute(engine, db, execution, tc, all_tool_calls)
            if tool_result is None:
                continue
            tc.result = tool_result.output

            all_tool_calls.append({
                "timestamp": datetime.utcnow().isoformat(),
                "tool_name": tc.name, "input": tc.arguments,
                "output": tool_result.output,
                "duration_ms": tool_result.duration_ms,
                "error": tool_result.error,
            })

            tool_summary = (tool_result.output or "")[:300]
            if tool_result.error:
                tool_summary = f"错误: {tool_result.error[:200]}"
            await event_publisher.publish_agent_thinking(
                execution_id=engine.execution_id,
                agent_name=agent.name,
                thought=f"[{tc.name}] {tool_summary}", step="tool_result",
            )
            engine._add_trace(execution, "agent.tool_call", agent_name=agent.name, task_name=task.name, data={
                "tool": tc.name, "success": tool_result.success, "duration_ms": tool_result.duration_ms,
            })

        append_tool_messages(messages, llm_response, is_anthropic)

        # 去重检测：同一工具+参数连续调用 3 次 → 自动生成代码兜底
        for tc in llm_response.tool_calls:
            call_key = f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True)}"
            recent_calls.append(call_key)
        if len(recent_calls) >= 3 and len(set(recent_calls[-3:])) == 1:
            failed_tc = llm_response.tool_calls[0]
            logger.warning("[TOOL_LOOP] Detected repeated identical tool call: %s, auto-generating code fallback", failed_tc.name)
            await event_publisher.publish_agent_thinking(
                execution_id=engine.execution_id,
                agent_name=agent.name,
                thought=f"工具 {failed_tc.name} 连续调用失败，自动切换为代码模式完成任务",
                step="auto_fallback",
            )
            fallback_result = await _auto_code_fallback(
                engine, db, execution, task, agent, failed_tc, messages, llm,
                effective_model, is_anthropic, timeout, all_tool_calls,
            )
            if fallback_result:
                final_content = fallback_result
                break
            # 如果代码回退也失败，发消息让 agent 自行处理
            messages.append({"role": "user", "content": (
                "你已连续3次调用相同的工具但未成功完成任务。请改用 code_execute 工具，"
                "编写 Python 代码来直接完成此任务。不要再重复调用之前失败的工具。"
            )})
            recent_calls = []

        # 强制推理
        if tool_round < max_tool_rounds - 1 and llm_response.tool_calls:
            try:
                explain_messages = messages + [{
                    "role": "user",
                    "content": "请用2-3句中文自然语言，简要说明你刚才做了什么、结果如何、接下来打算做什么。",
                }]
                explain_resp = await asyncio.wait_for(
                    llm.chat(messages=explain_messages, model=effective_model,
                             temperature=0.7, max_tokens=200, tools=None),
                    timeout=30,
                )
                explain_text = (explain_resp.content or "").strip()
                if explain_text:
                    total_tokens += explain_resp.tokens_used
                    total_cost += explain_resp.cost_usd
                    await event_publisher.publish_agent_thinking(
                        execution_id=engine.execution_id,
                        agent_name=agent.name,
                        thought=explain_text, step="reasoning",
                    )
                    messages.append({"role": "assistant", "content": explain_text})
            except Exception as explain_err:
                logger.debug("[EXECUTOR] Reasoning call failed (non-critical): %s", explain_err)
    else:
        logger.warning("[EXECUTOR] Agent '%s' hit max tool rounds (%d)", agent.name, max_tool_rounds)
        try:
            messages.append({"role": "user", "content": "请立即基于以上所有工具调用的结果，给出完整的最终答案。不要再调用任何工具。"})
            final_resp = await asyncio.wait_for(
                llm.chat(messages=messages, model=effective_model,
                         temperature=agent.temperature, max_tokens=agent.max_tokens, tools=None),
                timeout=timeout,
            )
            final_content = final_resp.content or ""
            total_tokens += final_resp.tokens_used
            total_cost += final_resp.cost_usd
        except Exception as final_err:
            logger.error("[EXECUTOR] Final answer request failed: %s", final_err)
            final_content = ""

        if not final_content:
            tool_summary = []
            for tc_entry in all_tool_calls[-5:]:
                tn = tc_entry.get("tool_name", "?")
                to = str(tc_entry.get("output", ""))[:300]
                tool_summary.append(f"[{tn}] {to}")
            final_content = (
                "[工具调用已达上限，以下为最近的工具结果]\n\n" + "\n\n".join(tool_summary)
                if tool_summary else "(工具调用轮次超限，未获得有效结果)"
            )

    return final_content, all_tool_calls, total_tokens, total_cost


async def check_approval_and_execute(engine, db, execution, tc, all_tool_calls: list):
    """审批检查 + 工具执行"""
    from app.engine.tools import ToolResult, execute_tool
    from app.models.crew import Crew

    _crew = await db.get(Crew, execution.crew_id)
    crew_approval_mode = getattr(_crew, 'approval_mode', 'semi_auto') or 'semi_auto'

    if crew_approval_mode != 'full_auto':
        from app.services.approval_manager import ApprovalMode, get_approval_manager
        approval_mgr = get_approval_manager()
        mode = ApprovalMode(crew_approval_mode)
        if approval_mgr.requires_approval(mode=mode, tool_name=tc.name):
            approval_req = await approval_mgr.create_approval_request(
                execution_id=engine.execution_id,
                tool_name=tc.name, tool_args=tc.arguments,
            )
            _tool_cn = {
                "file_write": "写入文件", "file_read": "读取文件",
                "code_execute": "执行代码", "shell_execute": "执行命令",
                "database_query": "数据库查询", "api_call": "调用接口",
                "web_search": "网络搜索", "image_generation": "生成图片",
            }
            _cn_name = _tool_cn.get(tc.name, tc.name)
            _mode_cn = {"safe": "限制权限", "semi_auto": "默认权限", "full_auto": "完全权限"}
            await event_publisher.publish_warning(
                execution_id=engine.execution_id,
                message=f"{_cn_name}操作需要您审批（{_mode_cn.get(crew_approval_mode, crew_approval_mode)}模式）",
                extra={
                    "approval_request_id": approval_req["request_id"],
                    "tool_name": tc.name,
                    "risk_level": approval_req["risk_level"],
                    "tool_args": tc.arguments,
                },
            )
            execution.status = ExecutionStatus.WAITING_REVIEW
            await db.commit()

            approval_result = await approval_mgr.wait_for_approval(
                approval_req["request_id"], timeout=600,
            )
            if approval_result["status"] != "approved":
                tool_result = ToolResult(
                    tool_call_id=tc.id, tool_name=tc.name,
                    success=False, output="",
                    error=f"工具调用被拒绝: {approval_result.get('reject_reason', '用户拒绝')}",
                )
                tc.result = tool_result.output
                all_tool_calls.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "tool_name": tc.name, "input": tc.arguments,
                    "output": "", "duration_ms": 0, "error": tool_result.error,
                })
                return None
            execution.status = ExecutionStatus.RUNNING
            await db.commit()

    from app.engine.mcp_adapter import get_mcp_adapter
    mcp_adapter = get_mcp_adapter()
    if mcp_adapter.is_mcp_tool(tc.name):
        server_id, original_name = mcp_adapter.parse_mcp_tool_name(tc.name)
        mcp_result = await mcp_adapter.call_tool(server_id, original_name, tc.arguments)
        return ToolResult(
            tool_call_id=tc.id, tool_name=tc.name,
            success=mcp_result.get("success", False),
            output=mcp_result.get("output", ""),
            error=mcp_result.get("error"),
        )

    return await execute_tool(tc.name, tc.arguments, tc.id)


async def _auto_code_fallback(
    engine, db, execution, task, agent, failed_tc, messages, llm,
    effective_model, is_anthropic, timeout, all_tool_calls,
) -> str | None:
    """工具连续失败后，自动生成等效 Python 代码并执行。

    利用 LLM 根据失败的工具调用和任务上下文生成 Python 代码，
    然后通过 code_execute 工具执行，返回结果或 None。
    """
    from app.engine.tools import execute_tool

    # 收集最近的工具调用结果作为上下文
    recent_results = []
    for tc_entry in all_tool_calls[-5:]:
        tn = tc_entry.get("tool_name", "?")
        to = str(tc_entry.get("output", ""))[:300]
        err = tc_entry.get("error", "")
        if err:
            recent_results.append(f"[{tn}] 错误: {err[:200]}")
        elif to:
            recent_results.append(f"[{tn}] {to}")

    # 构建让 LLM 生成代码的提示
    code_prompt = f"""你之前尝试调用工具 `{failed_tc.name}` 但连续3次失败。

任务描述：{(task.description or '')[:500]}
期望输出：{(task.expected_output or '')[:300]}
失败工具参数：{json.dumps(failed_tc.arguments, ensure_ascii=False)[:500]}
最近工具结果：
{chr(10).join(recent_results) if recent_results else '无'}

请编写一段 Python 代码来完成此任务。要求：
1. 代码必须是自包含的，可直接执行
2. 如果需要创建文件，使用绝对路径保存到用户桌面
3. 使用标准库或常见第三方库（reportlab, openpyxl, python-docx 等）
4. 最后 print 输出结果摘要

只输出代码，不要解释。用 ```python 包裹代码。"""

    try:
        # 让 LLM 生成代码
        code_messages = [
            {"role": "system", "content": "你是一个代码生成助手。只输出可执行的 Python 代码，不要解释。"},
            {"role": "user", "content": code_prompt},
        ]
        code_resp = await asyncio.wait_for(
            llm.chat(messages=code_messages, model=effective_model,
                     temperature=0.3, max_tokens=2000, tools=None),
            timeout=60,
        )
        code_text = code_resp.content or ""

        # 提取代码块
        import re
        code_match = re.search(r'```python\s*\n(.*?)```', code_text, re.DOTALL)
        if not code_match:
            # 尝试直接提取（可能没有 markdown 包裹）
            code_match = re.search(r'```\s*\n(.*?)```', code_text, re.DOTALL)
        if not code_match:
            # 整段当作代码
            code = code_text.strip()
            # 去掉可能的说明文字
            lines = code.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith(('import ', 'from ', 'def ', 'class ', 'if ', 'for ', 'while ', 'print(', 'with ', 'try:', 'except', '#', 'os.', 'path', 'f"', "f'", 'c.', 'canvas', 'wb ', 'ws ', 'doc ')):
                    in_code = True
                if in_code or line.startswith((' ', '\t')):
                    code_lines.append(line)
            code = '\n'.join(code_lines) if code_lines else code
        else:
            code = code_match.group(1).strip()

        if not code or len(code) < 20:
            logger.warning("[AUTO_FALLBACK] Generated code too short, skipping")
            return None

        logger.info("[AUTO_FALLBACK] Executing auto-generated code (%d chars) for task: %s", len(code), task.name[:50])
        await event_publisher.publish_agent_thinking(
            execution_id=engine.execution_id,
            agent_name=agent.name,
            thought=f"自动生成了 {len(code)} 字符的 Python 代码来完成任务，正在执行...",
            step="auto_code_execute",
        )

        # 执行生成的代码
        code_result = await execute_tool("code_execute", {"language": "python", "code": code}, "auto_fallback")

        if code_result.success:
            output = code_result.output or ""
            logger.info("[AUTO_FALLBACK] Code execution succeeded: %s", output[:200])
            await event_publisher.publish_agent_thinking(
                execution_id=engine.execution_id,
                agent_name=agent.name,
                thought=f"代码自动执行成功: {output[:300]}",
                step="auto_code_result",
            )
            all_tool_calls.append({
                "timestamp": datetime.utcnow().isoformat(),
                "tool_name": "code_execute",
                "input": {"language": "python", "code": code[:500]},
                "output": output,
                "duration_ms": code_result.duration_ms,
                "error": None,
            })
            return f"[自动代码回退] 工具 {failed_tc.name} 连续失败，已自动生成代码完成任务。\n\n{output}"
        else:
            logger.warning("[AUTO_FALLBACK] Code execution failed: %s", code_result.error)
            return None

    except Exception as e:
        logger.error("[AUTO_FALLBACK] Auto code fallback failed: %s", e)
        return None
