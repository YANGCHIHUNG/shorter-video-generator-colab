#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧹 專案清理工具
識別並列出可以刪除的非必要文件
"""

import os
import glob

def identify_files_to_delete():
    """識別可以刪除的文件"""
    
    # 定義可以刪除的文件類型
    files_to_delete = {
        'test_files': [],           # 測試文件
        'debug_files': [],          # 調試文件  
        'documentation': [],        # 說明文件
        'example_files': [],        # 示例文件
        'temp_files': [],          # 臨時文件
        'verification_files': []    # 驗證文件
    }
    
    print("🔍 掃描可刪除的文件...")
    print("=" * 60)
    
    # 獲取所有文件
    all_files = []
    for root, dirs, files in os.walk('.'):
        # 跳過虛擬環境和git目錄
        dirs[:] = [d for d in dirs if d not in ['myenv', 'new_venv', 'venv', '.git', '__pycache__']]
        
        for file in files:
            filepath = os.path.join(root, file).replace('\\', '/')
            all_files.append(filepath)
    
    # 分類文件
    for filepath in all_files:
        filename = os.path.basename(filepath)
        
        # 測試文件
        if (filename.startswith('test_') or 
            'test' in filename.lower() or
            filename.endswith('_test.py')):
            files_to_delete['test_files'].append(filepath)
        
        # 調試文件
        elif (filename.startswith('debug_') or 
              'debug' in filename.lower() or
              filename.startswith('check_')):
            files_to_delete['debug_files'].append(filepath)
        
        # 說明文件 (Markdown)
        elif (filename.endswith('.md') and 
              filename not in ['README.md']):  # 保留 README.md
            files_to_delete['documentation'].append(filepath)
        
        # 示例文件
        elif (filename.startswith('demo_') or 
              filename.startswith('example_') or
              'demo' in filename.lower() or
              'example' in filename.lower()):
            files_to_delete['example_files'].append(filepath)
        
        # 驗證文件
        elif (filename.startswith('verify_') or 
              'verify' in filename.lower() or
              filename.startswith('create_troubleshooting')):
            files_to_delete['verification_files'].append(filepath)
        
        # 臨時文件
        elif (filename.endswith('.html') and 'test' in filename.lower() or
              filename.endswith('.srt') and 'test' in filename.lower() or
              filename.startswith('simple_')):
            files_to_delete['temp_files'].append(filepath)
    
    return files_to_delete

def display_deletion_plan(files_to_delete):
    """顯示刪除計劃"""
    
    total_files = sum(len(files) for files in files_to_delete.values())
    
    print(f"📊 發現 {total_files} 個可刪除的文件")
    print()
    
    for category, files in files_to_delete.items():
        if files:
            category_names = {
                'test_files': '🧪 測試文件',
                'debug_files': '🔍 調試文件', 
                'documentation': '📚 說明文件',
                'example_files': '📄 示例文件',
                'temp_files': '🗂️ 臨時文件',
                'verification_files': '✅ 驗證文件'
            }
            
            print(f"{category_names[category]} ({len(files)} 個):")
            for file in sorted(files):
                print(f"  - {file}")
            print()
    
    return total_files

def generate_cleanup_script(files_to_delete):
    """生成清理腳本"""
    
    script_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
🧹 專案清理腳本
自動刪除測試文件、調試文件、說明文件等非必要文件
'''

import os
import shutil

def cleanup_project():
    '''執行專案清理'''
    
    files_to_delete = [
"""
    
    all_files = []
    for files in files_to_delete.values():
        all_files.extend(files)
    
    for file in sorted(all_files):
        script_content += f'        "{file}",\n'
    
    script_content += """    ]
    
    deleted_count = 0
    failed_count = 0
    
    print("🧹 開始清理專案...")
    print("=" * 50)
    
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"✅ 已刪除文件: {file_path}")
                    deleted_count += 1
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"✅ 已刪除目錄: {file_path}")
                    deleted_count += 1
            else:
                print(f"⚠️ 文件不存在: {file_path}")
        except Exception as e:
            print(f"❌ 刪除失敗: {file_path} - {e}")
            failed_count += 1
    
    print()
    print("🎯 清理結果:")
    print(f"  ✅ 成功刪除: {deleted_count} 個文件/目錄")
    print(f"  ❌ 刪除失敗: {failed_count} 個文件/目錄")
    print()
    print("🎉 專案清理完成！")

if __name__ == "__main__":
    cleanup_project()
"""
    
    return script_content

def main():
    """主函數"""
    print("🧹 專案清理分析")
    print("=" * 60)
    
    # 識別要刪除的文件
    files_to_delete = identify_files_to_delete()
    
    # 顯示刪除計劃
    total_files = display_deletion_plan(files_to_delete)
    
    if total_files > 0:
        # 生成清理腳本
        script_content = generate_cleanup_script(files_to_delete)
        
        with open('cleanup_project.py', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print("📝 已生成清理腳本: cleanup_project.py")
        print()
        print("⚠️ 請確認上述文件列表，然後執行:")
        print("   python cleanup_project.py")
        print()
        print("💡 建議在執行前先備份重要文件！")
    else:
        print("✅ 沒有找到可刪除的文件")

if __name__ == "__main__":
    main()
