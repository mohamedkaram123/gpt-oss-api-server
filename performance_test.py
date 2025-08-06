#!/usr/bin/env python3
"""
Performance testing script for GPT-OSS 120B API Server
Tests latency, throughput, and concurrent requests
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict, Any
import httpx
from concurrent.futures import ThreadPoolExecutor
import argparse

class PerformanceTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []
    
    async def single_request(self, session: httpx.AsyncClient, prompt: str) -> Dict[str, Any]:
        """Send a single request and measure performance"""
        start_time = time.time()
        
        try:
            response = await session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "gpt-oss-120b",
                    "max_tokens": 100,
                    "temperature": 0.7
                },
                timeout=300.0
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                tokens = len(result.get("choices", [{}])[0].get("message", {}).get("content", "").split())
                tokens_per_second = tokens / latency if latency > 0 else 0
                
                return {
                    "success": True,
                    "latency": latency,
                    "tokens": tokens,
                    "tokens_per_second": tokens_per_second,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "latency": latency,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "latency": end_time - start_time,
                "error": str(e)
            }
    
    async def latency_test(self, num_requests: int = 10) -> Dict[str, Any]:
        """Test average latency with sequential requests"""
        print(f"🔍 Running latency test with {num_requests} sequential requests...")
        
        prompts = [
            "What is artificial intelligence?",
            "Explain machine learning in simple terms.",
            "Write a short poem about technology.",
            "What are the benefits of renewable energy?",
            "Describe the process of photosynthesis.",
        ]
        
        async with httpx.AsyncClient() as session:
            results = []
            
            for i in range(num_requests):
                prompt = prompts[i % len(prompts)]
                result = await self.single_request(session, f"{prompt} (Request {i+1})")
                results.append(result)
                
                if result["success"]:
                    print(f"✅ Request {i+1}: {result['latency']:.2f}s, {result['tokens_per_second']:.1f} tokens/s")
                else:
                    print(f"❌ Request {i+1}: Failed - {result.get('error', 'Unknown error')}")
        
        # Calculate statistics
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            latencies = [r["latency"] for r in successful_results]
            tokens_per_sec = [r["tokens_per_second"] for r in successful_results]
            
            return {
                "test_type": "latency",
                "total_requests": num_requests,
                "successful_requests": len(successful_results),
                "success_rate": len(successful_results) / num_requests * 100,
                "avg_latency": statistics.mean(latencies),
                "median_latency": statistics.median(latencies),
                "min_latency": min(latencies),
                "max_latency": max(latencies),
                "avg_tokens_per_second": statistics.mean(tokens_per_sec),
                "total_time": sum(latencies)
            }
        else:
            return {
                "test_type": "latency",
                "total_requests": num_requests,
                "successful_requests": 0,
                "success_rate": 0,
                "error": "All requests failed"
            }
    
    async def concurrent_test(self, num_concurrent: int = 5, requests_per_worker: int = 3) -> Dict[str, Any]:
        """Test concurrent request handling"""
        print(f"🚀 Running concurrent test with {num_concurrent} workers, {requests_per_worker} requests each...")
        
        async def worker(worker_id: int, session: httpx.AsyncClient) -> List[Dict[str, Any]]:
            results = []
            for i in range(requests_per_worker):
                prompt = f"Worker {worker_id}, Request {i+1}: Explain quantum computing."
                result = await self.single_request(session, prompt)
                results.append(result)
            return results
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as session:
            # Create concurrent workers
            tasks = [worker(i, session) for i in range(num_concurrent)]
            worker_results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Flatten results
        all_results = []
        for worker_result in worker_results:
            all_results.extend(worker_result)
        
        successful_results = [r for r in all_results if r["success"]]
        total_requests = num_concurrent * requests_per_worker
        
        if successful_results:
            latencies = [r["latency"] for r in successful_results]
            tokens_per_sec = [r["tokens_per_second"] for r in successful_results]
            
            return {
                "test_type": "concurrent",
                "total_requests": total_requests,
                "successful_requests": len(successful_results),
                "success_rate": len(successful_results) / total_requests * 100,
                "total_time": total_time,
                "requests_per_second": total_requests / total_time,
                "avg_latency": statistics.mean(latencies),
                "avg_tokens_per_second": statistics.mean(tokens_per_sec),
                "concurrent_workers": num_concurrent
            }
        else:
            return {
                "test_type": "concurrent",
                "total_requests": total_requests,
                "successful_requests": 0,
                "success_rate": 0,
                "error": "All requests failed"
            }
    
    async def throughput_test(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Test maximum throughput over a time period"""
        print(f"📊 Running throughput test for {duration_seconds} seconds...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        results = []
        request_count = 0
        
        async with httpx.AsyncClient() as session:
            while time.time() < end_time:
                request_count += 1
                prompt = f"Throughput test request {request_count}: What is the meaning of life?"
                result = await self.single_request(session, prompt)
                results.append(result)
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        actual_duration = time.time() - start_time
        successful_results = [r for r in results if r["success"]]
        
        if successful_results:
            total_tokens = sum(r["tokens"] for r in successful_results)
            avg_latency = statistics.mean([r["latency"] for r in successful_results])
            
            return {
                "test_type": "throughput",
                "duration": actual_duration,
                "total_requests": len(results),
                "successful_requests": len(successful_results),
                "success_rate": len(successful_results) / len(results) * 100,
                "requests_per_second": len(successful_results) / actual_duration,
                "total_tokens": total_tokens,
                "tokens_per_second": total_tokens / actual_duration,
                "avg_latency": avg_latency
            }
        else:
            return {
                "test_type": "throughput",
                "duration": actual_duration,
                "total_requests": len(results),
                "successful_requests": 0,
                "success_rate": 0,
                "error": "All requests failed"
            }
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "="*60)
        print(f"📋 {results['test_type'].upper()} TEST RESULTS")
        print("="*60)
        
        if results.get("error"):
            print(f"❌ Error: {results['error']}")
            return
        
        print(f"📊 Total Requests: {results['total_requests']}")
        print(f"✅ Successful: {results['successful_requests']}")
        print(f"📈 Success Rate: {results['success_rate']:.1f}%")
        
        if "avg_latency" in results:
            print(f"⏱️  Average Latency: {results['avg_latency']:.2f}s")
        
        if "median_latency" in results:
            print(f"⏱️  Median Latency: {results['median_latency']:.2f}s")
            print(f"⏱️  Min Latency: {results['min_latency']:.2f}s")
            print(f"⏱️  Max Latency: {results['max_latency']:.2f}s")
        
        if "avg_tokens_per_second" in results:
            print(f"🚀 Average Tokens/sec: {results['avg_tokens_per_second']:.1f}")
        
        if "requests_per_second" in results:
            print(f"🚀 Requests/sec: {results['requests_per_second']:.2f}")
        
        if "total_time" in results:
            print(f"⏰ Total Time: {results['total_time']:.2f}s")
        
        print("="*60)

async def main():
    parser = argparse.ArgumentParser(description="Performance test for GPT-OSS API Server")
    parser.add_argument("--url", default="http://localhost:8080", help="API server URL")
    parser.add_argument("--test", choices=["latency", "concurrent", "throughput", "all"], 
                       default="all", help="Test type to run")
    parser.add_argument("--requests", type=int, default=10, help="Number of requests for latency test")
    parser.add_argument("--concurrent", type=int, default=5, help="Number of concurrent workers")
    parser.add_argument("--duration", type=int, default=60, help="Duration for throughput test (seconds)")
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.url)
    
    print(f"🎯 Starting performance tests for {args.url}")
    print(f"🕐 Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        if args.test in ["latency", "all"]:
            latency_results = await tester.latency_test(args.requests)
            tester.print_results(latency_results)
        
        if args.test in ["concurrent", "all"]:
            concurrent_results = await tester.concurrent_test(args.concurrent, 3)
            tester.print_results(concurrent_results)
        
        if args.test in ["throughput", "all"]:
            throughput_results = await tester.throughput_test(args.duration)
            tester.print_results(throughput_results)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    print(f"\n🏁 Tests completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())