#!/usr/bin/env python3
"""
邀请码管理工具

用法:
    python invite_admin.py generate [--max-uses N] [--expires-days N] [--note TEXT]
    python invite_admin.py list
    python invite_admin.py delete CODE
"""

import argparse
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import auth_service


def cmd_generate(args):
    """生成邀请码。"""
    invite = auth_service.generate_invite_code(
        max_uses=args.max_uses,
        expires_days=args.expires_days,
        note=args.note
    )
    
    print("\n✅ 邀请码生成成功!")
    print("=" * 40)
    print(f"📝 邀请码: {invite['code']}")
    print(f"🔢 最大使用次数: {invite['max_uses']}")
    if invite['expires_at']:
        print(f"⏰ 过期时间: {invite['expires_at']}")
    else:
        print("⏰ 过期时间: 永不过期")
    if invite['note']:
        print(f"📋 备注: {invite['note']}")
    print("=" * 40)
    print()


def cmd_list(args):
    """列出所有邀请码。"""
    codes = auth_service.list_invite_codes()
    
    if not codes:
        print("\n📭 暂无邀请码\n")
        return
    
    print(f"\n📋 共 {len(codes)} 个邀请码:")
    print("=" * 80)
    
    for code in codes:
        status = "✅ 可用" if code['use_count'] < code['max_uses'] else "❌ 已用完"
        
        # 检查是否过期
        if code['expires_at']:
            from datetime import datetime
            expires = datetime.fromisoformat(code['expires_at'].replace("Z", "+00:00"))
            if datetime.utcnow().replace(tzinfo=expires.tzinfo) > expires:
                status = "⏰ 已过期"
        
        print(f"📝 {code['code']} | {status} | 使用 {code['use_count']}/{code['max_uses']}")
        if code['note']:
            print(f"   备注: {code['note']}")
        if code['used_by']:
            print(f"   最后使用: {code['used_by']} @ {code['used_at']}")
        print("-" * 80)
    
    print()


def cmd_delete(args):
    """删除邀请码。"""
    success = auth_service.delete_invite_code(args.code)
    
    if success:
        print(f"\n✅ 邀请码 {args.code.upper()} 已删除\n")
    else:
        print(f"\n❌ 邀请码 {args.code.upper()} 不存在\n")


def main():
    parser = argparse.ArgumentParser(description="邀请码管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # generate 命令
    gen_parser = subparsers.add_parser("generate", aliases=["gen", "g"], help="生成邀请码")
    gen_parser.add_argument("--max-uses", "-m", type=int, default=1, help="最大使用次数 (默认: 1)")
    gen_parser.add_argument("--expires-days", "-e", type=int, help="过期天数 (默认: 永不过期)")
    gen_parser.add_argument("--note", "-n", type=str, help="备注信息")
    gen_parser.set_defaults(func=cmd_generate)
    
    # list 命令
    list_parser = subparsers.add_parser("list", aliases=["ls", "l"], help="列出所有邀请码")
    list_parser.set_defaults(func=cmd_list)
    
    # delete 命令
    del_parser = subparsers.add_parser("delete", aliases=["del", "d"], help="删除邀请码")
    del_parser.add_argument("code", type=str, help="要删除的邀请码")
    del_parser.set_defaults(func=cmd_delete)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == "__main__":
    main()
