#!/usr/bin/env python3
"""
验证 CustomFactorService 的测试覆盖率脚本

这个脚本验证所有方法是否都有对应的测试。
"""

import re
import sys
from pathlib import Path


def extract_methods_from_source(source_file):
    """从源文件中提取所有public方法"""
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 async def 和 def 方法
    pattern = r'^\s*(async\s+)?def\s+(\w+)\s*\('
    methods = set()

    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match:
            method_name = match.group(2)
            # 排除private方法（以下划线开头的方法）
            if not method_name.startswith('__'):
                methods.add(method_name)

    return methods


def extract_test_methods_from_test_file(test_file):
    """从测试文件中提取所有测试方法"""
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 async def test_xxx 方法
    pattern = r'^\s+async\s+def\s+(test_\w+)\s*\('
    test_methods = set()

    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match:
            test_methods.add(match.group(1))

    return test_methods


def extract_test_classes(test_file):
    """从测试文件中提取所有测试类"""
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'^class\s+(Test\w+)'
    classes = set()

    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match:
            classes.add(match.group(1))

    return classes


def map_tests_to_methods(test_file):
    """建立测试方法与被测试方法的映射"""
    test_methods = extract_test_methods_from_test_file(test_file)

    mapping = {}

    for test_method in test_methods:
        # 从test_create_factor_xxx中提取create_factor
        # 规则: test_[method_name]_[scenario]
        parts = test_method.replace('test_', '').split('_')

        # 常见的方法命名模式
        methods_patterns = [
            'create_factor',
            'get_user_factors',
            'get_factor_detail',
            'update_factor',
            'publish_factor',
            'make_public',
            'clone_factor',
            'search_public_factors',
            'get_popular_factors',
            'delete_factor',
            'to_dict'
        ]

        for method_pattern in methods_patterns:
            if method_pattern.replace('_', '') in test_method.replace('_', ''):
                if method_pattern not in mapping:
                    mapping[method_pattern] = []
                mapping[method_pattern].append(test_method)
                break

    return mapping


def print_coverage_report(source_file, test_file):
    """打印覆盖率报告"""
    print("=" * 80)
    print("CustomFactorService 测试覆盖率验证报告")
    print("=" * 80)

    # 提取方法和测试
    source_methods = extract_methods_from_source(source_file)
    test_methods = extract_test_methods_from_test_file(test_file)
    test_classes = extract_test_classes(test_file)
    test_mapping = map_tests_to_methods(test_file)

    print(f"\n源文件: {source_file}")
    print(f"测试文件: {test_file}")

    print(f"\n【源代码统计】")
    print(f"  Total methods: {len(source_methods)}")
    print(f"  Public methods: {len([m for m in source_methods if not m.startswith('_')])}")
    print(f"  Methods: {sorted(source_methods)}")

    print(f"\n【测试代码统计】")
    print(f"  Test methods: {len(test_methods)}")
    print(f"  Test classes: {len(test_classes)}")
    print(f"  Test classes: {sorted(test_classes)}")

    print(f"\n【方法与测试映射】")
    for method in sorted(source_methods):
        # 特殊处理_to_dict -> to_dict
        search_key = method if method != '__init__' else '__init__'
        if search_key == '_to_dict':
            search_key = 'to_dict'

        tests = test_mapping.get(search_key, [])
        status = "✓" if tests else "✗"

        print(f"\n  {status} {method}")
        if tests:
            print(f"    Tests ({len(tests)}):")
            for test in sorted(tests)[:5]:  # 只显示前5个
                print(f"      - {test}")
            if len(tests) > 5:
                print(f"      ... and {len(tests) - 5} more")
        else:
            print(f"    [未找到对应测试]")

    # 总结
    print("\n" + "=" * 80)
    print("【覆盖率总结】")
    print("=" * 80)

    # 定义关键方法
    key_methods = {
        '__init__': '初始化方法',
        'create_factor': '创建因子',
        'get_user_factors': '获取用户因子',
        'get_factor_detail': '获取因子详情',
        'update_factor': '更新因子',
        'publish_factor': '发布因子',
        'make_public': '公开因子',
        'clone_factor': '克隆因子',
        'search_public_factors': '搜索公开因子',
        'get_popular_factors': '获取热门因子',
        'delete_factor': '删除因子',
        '_to_dict': '转换为字典'
    }

    covered_methods = []
    uncovered_methods = []

    for method, description in key_methods.items():
        search_key = method if method != '_to_dict' else 'to_dict'
        if search_key in test_mapping or test_mapping.get(search_key, []):
            covered_methods.append((method, description))
        else:
            uncovered_methods.append((method, description))

    print(f"\nKey Methods Coverage: {len(covered_methods)}/{len(key_methods)}")
    print(f"Coverage Rate: {len(covered_methods) / len(key_methods) * 100:.1f}%\n")

    if uncovered_methods:
        print("未覆盖的方法:")
        for method, description in uncovered_methods:
            print(f"  ✗ {method:30} - {description}")
    else:
        print("✓ 所有关键方法都已有对应测试!")

    if covered_methods:
        print("\n已覆盖的方法:")
        for method, description in covered_methods:
            search_key = method if method != '_to_dict' else 'to_dict'
            tests_count = len(test_mapping.get(search_key, []))
            print(f"  ✓ {method:30} - {description:20} ({tests_count} tests)")

    print("\n" + "=" * 80)
    return len(uncovered_methods) == 0


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent.parent.parent.parent

    source_file = project_root / "app" / "modules" / "indicator" / "services" / "custom_factor_service.py"
    test_file = project_root / "tests" / "modules" / "indicator" / "services" / "test_custom_factor_service.py"

    if not source_file.exists():
        print(f"错误: 找不到源文件 {source_file}")
        sys.exit(1)

    if not test_file.exists():
        print(f"错误: 找不到测试文件 {test_file}")
        sys.exit(1)

    success = print_coverage_report(str(source_file), str(test_file))

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
