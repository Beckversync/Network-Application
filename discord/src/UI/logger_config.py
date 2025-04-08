import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Xóa tất cả handler đã đăng ký (nếu có)
if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

# Handler ghi ra console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Handler ghi ra file (app.log)
file_handler = logging.FileHandler("app.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
