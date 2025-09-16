#!/usr/bin/env python3
"""
Exam Answer Extractor
CSVファイルからChatGPTの回答番号を抽出するメインアプリケーション
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

from extractor import AnswerExtractor


def setup_logging() -> str:
    """ログ設定とログファイル名の生成（requirements.md準拠）"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"logs/{timestamp}.log"
    
    # ログディレクトリが存在しない場合は作成
    os.makedirs("logs", exist_ok=True)
    
    # ログ設定（ファイルとコンソール両方）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_filename


def main():
    """メイン実行関数（requirements.md準拠）"""
    # ログ設定
    log_filename = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("🚀 Exam Answer Extractor 開始")
    logger.info("=" * 50)
    logger.info(f"📄 ログファイル: {log_filename}")
    logger.info(f"⏰ 実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # extractor初期化
        logger.info("🔧 AnswerExtractor を初期化中...")
        extractor = AnswerExtractor()
        logger.info("✅ 初期化完了")
        
        # inputsフォルダのCSVファイルを検索
        input_dir = Path("inputs")
        if not input_dir.exists():
            logger.error("❌ inputsフォルダが存在しません")
            logger.info("💡 'inputs' フォルダを作成してCSVファイルを配置してください")
            return
            
        csv_files = list(input_dir.glob("*.csv"))
        if not csv_files:
            logger.warning("⚠️  inputsフォルダにCSVファイルが見つかりません")
            logger.info("💡 処理対象のCSVファイルを 'inputs' フォルダに配置してください")
            return
            
        logger.info(f"📊 処理対象ファイル数: {len(csv_files)}")
        for i, file in enumerate(csv_files, 1):
            logger.info(f"  {i}. {file.name}")
        
        # 各ファイルを処理
        total_processed = 0
        total_errors = 0
        processed_files = 0
        failed_files = 0
        
        logger.info("\n🔄 処理開始...")
        
        for i, csv_file in enumerate(csv_files, 1):
            logger.info(f"\n📁 [{i}/{len(csv_files)}] 処理中: {csv_file.name}")
            
            try:
                processed, errors = extractor.process_csv_with_move(csv_file)
                total_processed += processed
                total_errors += errors
                processed_files += 1
                
                success_rate = ((processed - errors) / processed * 100) if processed > 0 else 0
                logger.info(f"✅ 完了: 処理済み {processed}件, エラー {errors}件 (成功率: {success_rate:.1f}%)")
                
            except Exception as e:
                logger.error(f"❌ ファイル処理エラー: {type(e).__name__}: {e}")
                failed_files += 1
        
        # 最終サマリー
        logger.info("\n" + "=" * 50)
        logger.info("📈 処理完了サマリー")
        logger.info("=" * 50)
        logger.info(f"⏰ 実行完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📂 総処理ファイル数: {len(csv_files)}")
        logger.info(f"✅ 成功ファイル数: {processed_files}")
        logger.info(f"❌ 失敗ファイル数: {failed_files}")
        logger.info(f"📊 総処理レコード数: {total_processed}")
        logger.info(f"⚠️  総エラー数: {total_errors}")
        
        overall_success_rate = ((total_processed - total_errors) / total_processed * 100) if total_processed > 0 else 0
        logger.info(f"🎯 全体成功率: {overall_success_rate:.1f}%")
        
        # 結果判定
        if failed_files > 0:
            logger.warning(f"⚠️  {failed_files} ファイルの処理に失敗しました")
        
        if total_errors > 0:
            logger.warning(f"⚠️  {total_errors} 件のエラーが発生しました")
            logger.info("📄 詳細はログファイルを確認してください")
        
        if failed_files == 0 and total_errors == 0:
            logger.info("🎉 すべての処理が正常に完了しました！")
        
        logger.info(f"📁 結果ファイルは 'outputs' フォルダに保存されました")
        logger.info("=" * 50)
            
    except Exception as e:
        logger.error(f"💥 アプリケーションエラー: {type(e).__name__}: {e}")
        logger.error("処理を中断します")
        sys.exit(1)


if __name__ == "__main__":
    main()