#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书文档写入工具 - 命令行入口
将本地 Markdown 文件写入飞书文档
"""

import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv

from .writer import FeishuWriter


def main():
    """主函数"""
    # 先加载环境变量
    load_dotenv()

    arg_parser = argparse.ArgumentParser(
        description="将 Markdown 文件写入飞书文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 写入到我的空间
  python feishu_writer.py ./doc.md

  # 写入到指定文件夹
  python feishu_writer.py ./doc.md --target folder --folder-token fldcnxxxxxx

  # 写入到知识库
  python feishu_writer.py ./doc.md --target wiki --wiki-token wikcnxxxxxx

  # 批量写入
  python feishu_writer.py ./docs/ --target folder --folder-token fldcnxxxxxx
        """
    )

    arg_parser.add_argument("path", help="MD 文件或目录路径")
    arg_parser.add_argument(
        "--target", "-t",
        choices=["space", "folder", "wiki"],
        default="space",
        help="目标位置类型 (默认: space)"
    )
    arg_parser.add_argument("--folder-token", "-f", help="文件夹 token")
    arg_parser.add_argument("--wiki-token", "-w", help="知识库 token")
    arg_parser.add_argument("--no-check-duplicate", action="store_true", help="不检查重复文档")
    arg_parser.add_argument(
        "--on-duplicate",
        choices=["ask", "update", "skip", "new"],
        default="ask",
        help="重复文档处理方式 (默认: ask)"
    )

    args = arg_parser.parse_args()

    # 验证参数
    if args.target == "folder" and not args.folder_token:
        print("错误: 目标为 folder 时必须指定 --folder-token")
        sys.exit(1)

    if args.target == "wiki" and not args.wiki_token and not os.getenv("FEISHU_DEFAULT_WIKI_SPACE_ID"):
        print("错误: 目标为 wiki 时必须指定 --wiki-token 或在 .env 中配置 FEISHU_DEFAULT_WIKI_SPACE_ID")
        sys.exit(1)

    # 初始化
    try:
        writer = FeishuWriter()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

    # 获取文件列表
    path = Path(args.path)
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.glob("**/*.md"))
    else:
        print(f"错误: 路径不存在 - {args.path}")
        sys.exit(1)

    if not files:
        print("未找到 MD 文件")
        sys.exit(0)

    # 处理文件
    success_count = 0
    fail_count = 0
    total_images = 0

    for i, file in enumerate(files, 1):
        print(f"正在处理 ({i}/{len(files)}): {file.name}")

        result = writer.write_file(
            str(file),
            target=args.target,
            folder_token=args.folder_token,
            wiki_token=args.wiki_token,
            check_duplicate=not args.no_check_duplicate
        )

        # 处理重复文档
        if result.get("message", "").startswith("duplicate:"):
            parts = result["message"].split(":", 2)
            existing_id = parts[1]
            doc_title = parts[2]

            if args.on_duplicate == "ask":
                print(f"  发现同名文档: {doc_title}")
                print("  请选择处理方式:")
                print("  1. 覆盖更新")
                print("  2. 创建新文档")
                print("  3. 跳过")
                choice = input("  请输入选项 (1/2/3): ").strip()

                if choice == "1":
                    result = writer.update_document(existing_id, str(file))
                elif choice == "2":
                    result = writer.write_file(
                        str(file),
                        target=args.target,
                        folder_token=args.folder_token,
                        wiki_token=args.wiki_token,
                        check_duplicate=False
                    )
                else:
                    print(f"  已跳过: {file.name}")
                    continue
            elif args.on_duplicate == "update":
                result = writer.update_document(existing_id, str(file))
            elif args.on_duplicate == "new":
                result = writer.write_file(
                    str(file),
                    target=args.target,
                    folder_token=args.folder_token,
                    wiki_token=args.wiki_token,
                    check_duplicate=False
                )
            else:  # skip
                print(f"  已跳过: {file.name}")
                continue

        if result.get("success"):
            success_count += 1
            total_images += result.get("uploaded_images", 0)
            print(f"  [OK] {result.get('message')}")
        else:
            fail_count += 1
            print(f"  [FAIL] {result.get('message')}")

    # 输出汇总
    print("\n" + "=" * 40)
    print(f"成功: {success_count} 个文档")
    if fail_count:
        print(f"失败: {fail_count} 个文档")
    print(f"已上传图片: {total_images} 张")


if __name__ == "__main__":
    main()
