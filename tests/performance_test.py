"""Fugue 性能测试脚本"""

import asyncio
import httpx
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict


class PerformanceTester:
    """性能测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []

    async def test_concurrent_requests(
        self,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrency: int = 10,
        headers: Dict = None,
        json_data: Dict = None,
    ) -> Dict:
        """测试并发请求性能"""
        print(f"\n🔄 Testing {method} {endpoint}")
        print(f"   Requests: {num_requests}, Concurrency: {concurrency}")

        response_times = []
        status_codes = []
        errors = []

        async def make_request(client: httpx.AsyncClient, index: int):
            start_time = time.time()
            try:
                if method.upper() == "GET":
                    response = await client.get(endpoint, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(endpoint, headers=headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                elapsed = time.time() - start_time
                response_times.append(elapsed)
                status_codes.append(response.status_code)

                if response.status_code >= 400:
                    errors.append(f"Request {index}: {response.status_code}")

            except Exception as e:
                elapsed = time.time() - start_time
                response_times.append(elapsed)
                errors.append(f"Request {index}: {str(e)}")

        # 执行并发请求
        start_total = time.time()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(concurrency)

            async def limited_request(index: int):
                async with semaphore:
                    await make_request(client, index)

            tasks = [limited_request(i) for i in range(num_requests)]
            await asyncio.gather(*tasks)

        total_time = time.time() - start_total

        # 计算统计信息
        result = {
            "endpoint": endpoint,
            "method": method,
            "total_requests": num_requests,
            "concurrency": concurrency,
            "total_time": round(total_time, 2),
            "requests_per_second": round(num_requests / total_time, 2),
            "avg_response_time": round(statistics.mean(response_times) * 1000, 2),  # ms
            "median_response_time": round(statistics.median(response_times) * 1000, 2),  # ms
            "p95_response_time": round(sorted(response_times)[int(len(response_times) * 0.95)] * 1000, 2),  # ms
            "p99_response_time": round(sorted(response_times)[int(len(response_times) * 0.99)] * 1000, 2),  # ms
            "min_response_time": round(min(response_times) * 1000, 2),  # ms
            "max_response_time": round(max(response_times) * 1000, 2),  # ms
            "success_rate": round((num_requests - len(errors)) / num_requests * 100, 2),
            "errors": len(errors),
            "error_samples": errors[:5],  # 只记录前5个错误
        }

        self.results.append(result)
        self._print_result(result)

        return result

    def _print_result(self, result: Dict):
        """打印测试结果"""
        print(f"   ✅ Completed in {result['total_time']}s")
        print(f"   📊 Requests/sec: {result['requests_per_second']}")
        print(f"   ⏱️  Avg response: {result['avg_response_time']}ms")
        print(f"   ⏱️  P95 response: {result['p95_response_time']}ms")
        print(f"   ⏱️  P99 response: {result['p99_response_time']}ms")
        print(f"   ✅ Success rate: {result['success_rate']}%")

        if result['errors'] > 0:
            print(f"   ⚠️  Errors: {result['errors']}")
            for error in result['error_samples']:
                print(f"      - {error}")

    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("# Fugue 性能测试报告")
        report.append(f"\n测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"目标服务器: {self.base_url}\n")

        report.append("## 测试结果汇总\n")
        report.append("| 端点 | 方法 | 请求数 | 并发 | RPS | 平均响应 | P95 | P99 | 成功率 |")
        report.append("|------|------|--------|------|-----|----------|-----|-----|--------|")

        for result in self.results:
            report.append(
                f"| {result['endpoint']} "
                f"| {result['method']} "
                f"| {result['total_requests']} "
                f"| {result['concurrency']} "
                f"| {result['requests_per_second']} "
                f"| {result['avg_response_time']}ms "
                f"| {result['p95_response_time']}ms "
                f"| {result['p99_response_time']}ms "
                f"| {result['success_rate']}% |"
            )

        report.append("\n## 性能指标说明\n")
        report.append("- **RPS**: 每秒请求数（越高越好）")
        report.append("- **平均响应**: 平均响应时间（越低越好）")
        report.append("- **P95**: 95%的请求在此时间内完成")
        report.append("- **P99**: 99%的请求在此时间内完成")
        report.append("- **成功率**: 成功请求的百分比")

        # 性能建议
        report.append("\n## 性能优化建议\n")

        for result in self.results:
            if result['avg_response_time'] > 1000:
                report.append(f"- ⚠️ {result['endpoint']} 平均响应时间超过1秒，建议优化")

            if result['success_rate'] < 99:
                report.append(f"- ⚠️ {result['endpoint']} 成功率低于99%，需要检查错误")

            if result['requests_per_second'] < 50:
                report.append(f"- 💡 {result['endpoint']} RPS较低，考虑增加缓存或优化查询")

        return "\n".join(report)


async def run_performance_tests():
    """运行完整性能测试"""
    print("🚀 Fugue Performance Test Suite")
    print("=" * 60)

    tester = PerformanceTester()

    # 获取认证Token
    print("\n🔐 Authenticating...")
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "demo@fugue.com",
                    "password": "Demo123456",
                },
            )

            if response.status_code != 200:
                print(f"❌ Authentication failed: {response.status_code}")
                print("   Please ensure the demo user exists")
                return

            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Authenticated successfully")

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("   Please ensure the backend is running")
            return

    # 测试场景
    print("\n" + "=" * 60)
    print("📊 Running performance tests...")
    print("=" * 60)

    # 1. 健康检查（基准测试）
    await tester.test_concurrent_requests(
        endpoint="/health",
        method="GET",
        num_requests=1000,
        concurrency=50,
    )

    # 2. 认证接口
    await tester.test_concurrent_requests(
        endpoint="/api/v1/auth/me",
        method="GET",
        num_requests=500,
        concurrency=20,
        headers=headers,
    )

    # 3. 工作流列表
    await tester.test_concurrent_requests(
        endpoint="/api/v1/crews/",
        method="GET",
        num_requests=500,
        concurrency=20,
        headers=headers,
    )

    # 4. 模板列表
    await tester.test_concurrent_requests(
        endpoint="/api/v1/templates/",
        method="GET",
        num_requests=500,
        concurrency=20,
        headers=headers,
    )

    # 5. 创建工作流
    await tester.test_concurrent_requests(
        endpoint="/api/v1/crews/",
        method="POST",
        num_requests=100,
        concurrency=10,
        headers=headers,
        json_data={
            "name": "性能测试工作流",
            "description": "自动创建的测试工作流",
        },
    )

    # 生成报告
    report = tester.generate_report()

    # 保存报告
    with open("performance_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 60)
    print("📄 Performance report saved to: performance_report.md")
    print("=" * 60)

    # 打印摘要
    print("\n📊 Summary:")
    for result in tester.results:
        status = "✅" if result['success_rate'] >= 99 else "⚠️"
        print(f"   {status} {result['endpoint']}: {result['requests_per_second']} req/s, {result['avg_response_time']}ms avg")


if __name__ == "__main__":
    asyncio.run(run_performance_tests())
