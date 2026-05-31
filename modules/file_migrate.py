import os
import shutil
from modules.logger import logger, error_log
from config import FILE_MIGRATE_PATHS

IGNORE_DIRS = [".stfolder"]


class FileMigrator:
    """文件迁移管理器"""

    def __init__(self, state_manager):
        self.state_manager = state_manager

    def migrate(self, reverse: bool = False) -> bool:
        """
        执行文件迁移

        参数:
            reverse: 是否反向迁移（从备份文件夹迁移回同步文件夹）

        返回:
            是否成功
        """
        if not FILE_MIGRATE_PATHS:
            logger.error("[file_migrate] 未配置迁移路径")
            self.state_manager.set_status_text("未配置迁移路径")
            return False

        direction = "迁回同步文件夹" if reverse else "迁入备份文件夹"
        logger.info(f"[file_migrate] 开始{direction}")
        self.state_manager.set_status_text(f"正在{direction}...")

        total_migrated = 0
        total_failed = 0
        has_error = False

        for sync_folder, backup_folder in FILE_MIGRATE_PATHS.items():
            source_dir = backup_folder if reverse else sync_folder
            target_dir = sync_folder if reverse else backup_folder

            logger.info(f"[file_migrate] 处理: {source_dir} -> {target_dir}")

            try:
                if not os.path.exists(source_dir):
                    logger.error(f"[file_migrate] 源目录不存在: {source_dir}")
                    has_error = True
                    continue

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    logger.info(f"[file_migrate] 创建目标目录: {target_dir}")

                migrated_count = 0
                failed_count = 0

                for item in os.listdir(source_dir):
                    if item in IGNORE_DIRS:
                        # logger.info(f"[file_migrate] 忽略目录: {item}")
                        continue

                    source_path = os.path.join(source_dir, item)
                    target_path = os.path.join(target_dir, item)

                    try:
                        if os.path.isfile(source_path):
                            shutil.move(source_path, target_path)
                            # logger.info(f"[file_migrate] 移动文件: {item}")
                            migrated_count += 1
                        elif os.path.isdir(source_path):
                            shutil.move(source_path, target_path)
                            # logger.info(f"[file_migrate] 移动文件夹: {item}")
                            migrated_count += 1
                    except Exception as e:
                        logger.error(f"[file_migrate] 移动失败 {item}: {error_log(e)}")
                        failed_count += 1

                total_migrated += migrated_count
                total_failed += failed_count

            except Exception as e:
                logger.error(f"[file_migrate] 迁移失败 {source_dir}: {error_log(e)}")
                has_error = True

        result_msg = f"迁移完成: 成功{total_migrated}个"
        if total_failed > 0:
            result_msg += f", 失败{total_failed}个"

        logger.info(f"[file_migrate] {result_msg}")
        self.state_manager.set_status_text(result_msg)

        return not has_error
