from pathlib import Path

file_path = Path("test_orders/臺灣嘉義地方法院112年度國審交訴字第1號刑事判決.txt")
text = file_path.read_text(encoding="utf-8")
text = text.replace('國民法官法庭', '法庭')
file_path.write_text(text, encoding="utf-8")

