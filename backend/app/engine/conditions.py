"""条件分支执行逻辑"""

import logging
from typing import Dict, List, Any

from simpleeval import simple_eval, InvalidExpression

logger = logging.getLogger(__name__)


def evaluate_condition(condition, task_outputs: Dict[str, str]) -> List[str]:
    """评估条件表达式，返回应执行的 task ID 列表。

    Args:
        condition: ConditionBranch 模型实例
        task_outputs: 已完成任务的输出字典

    Returns:
        true_branch_task_ids 或 false_branch_task_ids
    """
    # 构建安全的命名空间（变量）
    safe_names = {"context": task_outputs}
    for task_id, output in task_outputs.items():
        safe_names[f"task_{task_id[:8]}"] = output

    # 构建安全的函数命名空间
    safe_functions = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "contains": lambda text, sub: sub in str(text),
        "equals": lambda a, b: str(a).strip() == str(b).strip(),
        "gt": lambda a, b: float(a) > float(b),
        "lt": lambda a, b: float(a) < float(b),
    }

    try:
        result = simple_eval(condition.expression, names=safe_names, functions=safe_functions)
        if result:
            return condition.true_branch_task_ids or []
        else:
            return condition.false_branch_task_ids or []
    except InvalidExpression as e:
        logger.error(f"条件表达式无效 [{condition.name}]: {e}")
        raise ValueError(f"条件表达式无效 [{condition.name}]: {str(e)}")
    except Exception as e:
        logger.error(f"条件表达式执行失败 [{condition.name}]: {e}")
        raise ValueError(f"条件表达式执行失败 [{condition.name}]: {str(e)}")


def filter_tasks_by_conditions(
    conditions,
    task_outputs: Dict[str, str],
    all_task_ids: set,
) -> tuple:
    """根据所有条件分支过滤任务。

    Returns:
        (executable_task_ids, skipped_task_ids)
    """
    skip_ids = set()

    for condition in conditions:
        try:
            branch_ids = evaluate_condition(condition, task_outputs)
            # 不在当前分支中的任务标记为跳过
            opposite_ids = set()
            if condition.true_branch_task_ids:
                opposite_ids.update(condition.true_branch_task_ids)
            if condition.false_branch_task_ids:
                opposite_ids.update(condition.false_branch_task_ids)
            skip_ids.update(opposite_ids - set(branch_ids))
        except ValueError:
            # 条件评估失败，跳过该条件
            continue

    executable = all_task_ids - skip_ids
    return executable, skip_ids
