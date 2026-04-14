import sys
import os
import traceback
import logging

# 获取程序根目录
def get_app_root():
    if getattr(sys, 'frozen', False):
        # 打包后的路径：exe 所在目录
        return os.path.dirname(sys.executable)
    # 开发环境路径：main.py 所在目录
    return os.path.dirname(os.path.abspath(__file__))

APP_ROOT = get_app_root()

# 确保项目根目录在 sys.path 中
sys.path.insert(0, APP_ROOT)

# 配置日志
log_dir = os.path.join(APP_ROOT, 'data')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'debug.log')

# 根 logger 设为 INFO，避免 requests/urllib3 的 DEBUG 日志刷屏
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('SteamAnalyzer')
logger.setLevel(logging.DEBUG)
# 静默第三方库的 DEBUG 日志
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)


def global_exception_handler(exc_type, exc_value, exc_tb):
    """全局未捕获异常处理"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"未捕获的异常:\n{error_msg}")
    print(f"\n{'='*60}")
    print(f"[CRASH] 程序发生未捕获的异常:")
    print(f"{'='*60}")
    print(error_msg)
    print(f"{'='*60}")
    print(f"日志已保存到: {log_file}")


# 安装全局异常处理
sys.excepthook = global_exception_handler


def main():
    logger.info("=" * 40)
    logger.info("Steam 游戏数据分析器启动")
    logger.info(f"Python: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")

    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        logger.info("PyQt5 导入成功")
    except ImportError as e:
        logger.error(f"PyQt5 导入失败: {e}")
        print("需要安装 PyQt5: pip install PyQt5")
        sys.exit(1)

    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)

    # 全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    try:
        from src.ui.main_window import MainWindow
        logger.info("主窗口模块导入成功")

        window = MainWindow()
        window.show()
        logger.info("主窗口已显示")
    except Exception as e:
        logger.critical(f"主窗口创建失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    exit_code = app.exec_()
    logger.info(f"程序正常退出，退出码: {exit_code}")
    sys.exit(0)  # 正常关闭始终返回 0


if __name__ == '__main__':
    main()
